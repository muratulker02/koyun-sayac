"""Koyun Sayacı arayüzü. Çalıştır: .venv/bin/python app.py  →  http://127.0.0.1:8780

İki kip:
  • İzleme  — kamera bütün gün açık; her çıkış/giriş günün defterine yazılır, dışarıda kalan
              anlık görünür, son koyun girince ve akşam kontrol saatinde Telegram'a rapor gider.
  • Demo    — hazır videolarla deneme; deftere yazmaz, gerçek sayı biliniyorsa doğruluğu gösterir.
"""
import json
import os
import threading
import time
from datetime import date, datetime
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

import defter
from bildir import bot_adi, gonder, sohbet_bul
from motor import Motor

KOK = Path(__file__).parent
AYAR = KOK / "ayarlar.json"
DEMO = KOK / "test-video"
VIDEO_KAYIT = KOK / "kayitlar" / "video"
VARSAYILAN = {"suru": 700, "tolerans": 0, "kamera": "", "cizgi": [0.5, 0, 0.5, 1], "yon_ters": False,
              "rapor_saati": "19:30", "otomatik_baslat": True, "video_kaydet": True}


def model_yolu():
    ozel = KOK / "modeller" / "koyun-tepeden.pt"
    return str(ozel if ozel.exists() else KOK / "modeller" / "yolo11s.pt")


app = Flask(__name__, static_folder=str(KOK / "arayuz"))
motor = Motor(model_yolu())
motor.log = defter.sistem_log
durum = {"kip": None, "demo": None, "son": (0, 0), "mesaj": ""}


def ayarlar():
    a = dict(VARSAYILAN)
    if AYAR.exists():
        a.update(json.loads(AYAR.read_text()))
    return a


def ayar_kaydet(a):
    AYAR.write_text(json.dumps(a, ensure_ascii=False, indent=2))


def env_oku():
    f = KOK / ".env"
    d = {}
    if f.exists():
        for s in f.read_text().splitlines():
            if "=" in s and not s.startswith("#"):
                k, v = s.split("=", 1)
                d[k.strip()] = v.strip()
    return d


def demo_bilgi():
    f = DEMO / "demolar.json"
    return json.loads(f.read_text()) if f.exists() else {}


def demolar():
    bilgi = demo_bilgi()
    adlar = sorted(p.name for p in DEMO.glob("*.mp4"))
    return [{"ad": ad, **bilgi.get(ad, {})} for ad in adlar]


# --- bekçi: sayaç farkını deftere yazar, bildirimleri yönetir ---
def izleme_baslat():
    a = ayarlar()
    if not a["kamera"]:
        return False
    durum.update(kip="izleme", demo=None, son=(0, 0), mesaj="")
    motor.model_yolu = model_yolu()
    motor.cizgi_ayarla(a["cizgi"], a["yon_ters"])
    motor.baslat(a["kamera"], gercek_hiz=False,
                 kayit_klasoru=VIDEO_KAYIT if a["video_kaydet"] else None)
    return True


def bekci():
    gun = date.today()
    while True:
        time.sleep(1)
        try:
            a = ayarlar()
            if durum["kip"] == "izleme" and motor.sayac:
                c, g = motor.sayac.cikan, motor.sayac.giren
                sc, sg = durum["son"]
                if (c, g) != (sc, sg):
                    once = defter.oku()
                    k = defter.ekle(max(0, c - sc), max(0, g - sg))
                    durum["son"] = (c, g)
                    # son koyun da girdi → hemen haber ver (günde bir kez)
                    if (defter.disarida(once) > a["tolerans"] >= defter.disarida(k)
                            and k["cikan"] > 0 and not k.get("tamam_bildirildi")):
                        gonder(f"✅ Hepsi içeride ({datetime.now():%H:%M}): {k['cikan']} çıktı, {k['giren']} girdi")
                        k["tamam_bildirildi"] = True
                        defter._yaz(k)
            # gün değişti → sayaç farkı sıfırdan
            if date.today() != gun:
                gun = date.today()
                if motor.sayac:
                    durum["son"] = (motor.sayac.cikan, motor.sayac.giren)
            # akşam kontrol saati
            k = defter.oku()
            if datetime.now().strftime("%H:%M") >= a["rapor_saati"] and not k.get("rapor"):
                metin = defter.rapor_metni(k, a["suru"], a["tolerans"])
                if durum["kip"] != "izleme" and not (k["cikan"] or k["giren"]):
                    metin = "ℹ️ Bugün izleme kapalıydı, sayım yapılmadı."
                gonder(f"🐑 Akşam kontrolü {a['rapor_saati']}\n{metin}")
                defter.rapor_kaydet(metin)
            # kamera ayarlıysa ve otomatik başlatma açıksa izleme hep açık kalsın
            if (a["otomatik_baslat"] and a["kamera"] and durum["kip"] is None
                    and motor.durum in ("bekliyor", "bitti", "hata")):
                izleme_baslat()
        except Exception as e:  # bekçi asla ölmesin
            print("bekçi hatası:", e)


# --- sayfalar ---
@app.get("/")
def ana():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/kayit/<ad>")
def kayit_video(ad):
    return send_from_directory(VIDEO_KAYIT, ad)


@app.get("/kayit-csv")
def kayit_csv():
    if not defter.CSV.exists():
        return "Henüz geçiş kaydı yok.", 404
    return send_from_directory(defter.KLASOR, defter.CSV.name, as_attachment=True)


@app.get("/akis")
def akis():
    def uret():
        son = None
        while True:
            j = motor.jpeg
            if j is not None and j is not son:
                son = j
                yield b"--kare\r\nContent-Type: image/jpeg\r\n\r\n" + j + b"\r\n"
            time.sleep(0.03)
    return Response(uret(), mimetype="multipart/x-mixed-replace; boundary=kare")


@app.get("/api/durum")
def api_durum():
    a = ayarlar()
    e = env_oku()
    bugun = defter.oku()
    videolar = sorted((p.name for p in VIDEO_KAYIT.glob(f"{date.today().isoformat()}_*.mp4")), reverse=True) \
        if VIDEO_KAYIT.exists() else []
    return jsonify({**motor.ozet(), "kip": durum["kip"], "demo": durum["demo"], "mesaj": durum["mesaj"],
                    "goruntu": motor.jpeg is not None, "ayarlar": a, "demolar": demolar(),
                    "bugun": {k: v for k, v in bugun.items() if k != "olaylar"},
                    "olaylar": bugun["olaylar"][-8:][::-1], "disarida": defter.disarida(bugun),
                    "gecmis": defter.gecmis(), "videolar": videolar, "sistem": defter.son_sistem(12),
                    "model": Path(motor.model_yolu).name,
                    "telegram": bool(e.get("TELEGRAM_TOKEN") and e.get("TELEGRAM_CHAT_ID"))})


@app.post("/api/izleme")
def api_izleme():
    if not izleme_baslat():
        return jsonify({"hata": "Önce Ayarlar'dan kamera adresini girin."}), 400
    return jsonify({"ok": True})


@app.post("/api/demo")
def api_demo():
    d = request.json or {}
    ad = d["demo"]
    bilgi = demo_bilgi().get(ad, {})
    a = ayarlar()

    def bitti(ozet):
        g = bilgi.get("gercek")
        sayilan = ozet["giren"] + ozet["cikan"]
        if g:
            hata = sayilan - g
            durum["mesaj"] = (f"Demo bitti — gerçek {g}, sayılan {sayilan} → "
                              + ("✅ hatasız" if hata == 0 else f"{hata:+d} fark (doğruluk %{100 * (1 - abs(hata) / g):.1f})"))
        else:
            durum["mesaj"] = f"Demo bitti — {ozet['cikan']} çıkış, {ozet['giren']} giriş sayıldı."

    durum.update(kip="demo", demo=ad, son=(0, 0), mesaj="")
    motor.model_yolu = model_yolu()
    motor.cizgi_ayarla(bilgi.get("cizgi", a["cizgi"]), bilgi.get("yon_ters", a["yon_ters"]))
    motor.baslat(str(DEMO / ad), gercek_hiz=d.get("gercek_hiz", True), bitince=bitti)
    return jsonify({"ok": True})


@app.post("/api/durdur")
def api_durdur():
    motor.durdur()
    durum["kip"] = None if durum["kip"] == "demo" else "durduruldu"
    return jsonify({"ok": True})


@app.post("/api/rapor")
def api_rapor():
    a = ayarlar()
    metin = defter.rapor_metni(defter.oku(), a["suru"], a["tolerans"])
    gonder(f"🐑 Anlık durum {datetime.now():%H:%M}\n{metin}")
    return jsonify({"ok": True, "metin": metin})


@app.post("/api/cizgi")
def api_cizgi():
    d = request.json or {}
    a = ayarlar()
    if "cizgi" in d:
        a["cizgi"] = [round(float(v), 4) for v in d["cizgi"]]
    if "yon_ters" in d:
        a["yon_ters"] = bool(d["yon_ters"])
    ayar_kaydet(a)
    motor.cizgi_ayarla(a["cizgi"], a["yon_ters"])
    return jsonify({"ok": True})


@app.post("/api/ayarlar")
def api_ayarlar():
    d = request.json or {}
    a = ayarlar()
    for k in ("suru", "tolerans"):
        if k in d and str(d[k]).strip() != "":
            a[k] = int(d[k])
    for k in ("kamera", "rapor_saati"):
        if k in d:
            a[k] = str(d[k]).strip()
    for k in ("otomatik_baslat", "video_kaydet"):
        if k in d:
            a[k] = bool(d[k])
    ayar_kaydet(a)
    if d.get("telegram_token") or d.get("telegram_chat"):
        e = env_oku()
        if d.get("telegram_token"):
            e["TELEGRAM_TOKEN"] = d["telegram_token"].strip()
        if d.get("telegram_chat"):
            e["TELEGRAM_CHAT_ID"] = d["telegram_chat"].strip()
        (KOK / ".env").write_text("".join(f"{k}={v}\n" for k, v in e.items()))
    return jsonify({"ok": True})


@app.post("/api/telegram-bagla")
def api_telegram_bagla():
    """Bot anahtarı girildi, kullanıcı bota 'merhaba' yazdı → sohbet numarasını bul ve kaydet."""
    d = request.json or {}
    e = env_oku()
    token = (d.get("telegram_token") or "").strip() or e.get("TELEGRAM_TOKEN", "")
    if not token:
        return jsonify({"hata": "Önce bot anahtarını yapıştırın."}), 400
    ad = bot_adi(token)
    if not ad:
        return jsonify({"hata": "Bot anahtarı geçersiz (BotFather'dan aldığınız uzun kodu kontrol edin)."}), 400
    bul = sohbet_bul(token)
    if not bul:
        return jsonify({"hata": f"Telegram'da @{ad} botunu açıp 'merhaba' yazın, sonra tekrar basın.", "bot": ad}), 400
    sohbet, kim = bul
    e["TELEGRAM_TOKEN"], e["TELEGRAM_CHAT_ID"] = token, sohbet
    (KOK / ".env").write_text("".join(f"{k}={v}\n" for k, v in e.items()))
    gonder("🐑 Koyun Sayacı bağlandı. Bildirimler buraya gelecek.")
    defter.sistem_log(f"TELEGRAM bağlandı: @{ad} → {kim}")
    return jsonify({"ok": True, "bot": ad, "kim": kim})


@app.post("/api/kamera-dene")
def api_kamera_dene():
    """Kamera adresinden tek kare alır; bağlantı ve görüntü kontrolü."""
    import cv2
    d = request.json or {}
    adres = (d.get("kamera") or ayarlar()["kamera"]).strip()
    if not adres:
        return jsonify({"hata": "Kamera adresi boş."}), 400
    cap = cv2.VideoCapture(adres)
    ok, img = cap.read()
    cap.release()
    if not ok:
        defter.sistem_log(f"KAMERA deneme başarısız: {adres}")
        return jsonify({"hata": "Kameraya bağlanılamadı. Adres, kullanıcı adı/şifre ve ağ bağlantısını kontrol edin."}), 400
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 70])
    motor.jpeg = buf.tobytes()
    h, w = img.shape[:2]
    defter.sistem_log(f"KAMERA deneme başarılı: {w}x{h}")
    return jsonify({"ok": True, "boyut": f"{w}×{h}"})


@app.post("/api/telegram-test")
def api_telegram_test():
    return jsonify({"ok": gonder("🐑 Koyun Sayacı test mesajı — bildirimler çalışıyor.")})


if __name__ == "__main__":
    defter.sistem_log(f"PROGRAM açıldı, model {Path(model_yolu()).name}")
    threading.Thread(target=bekci, daemon=True).start()
    app.run(host="127.0.0.1", port=int(os.environ.get("KOYUN_PORT", 8780)), threaded=True)
