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

from flask import Flask, Response, jsonify, redirect, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

import defter
from bildir import bot_adi, gonder, sohbet_bul
from fotosay import say as foto_say
from motor import Motor

KOK = Path(__file__).parent
AYAR = KOK / "ayarlar.json"
DEMO = KOK / "test-video"
VIDEO_KAYIT = KOK / "kayitlar" / "video"
YUKLENEN = KOK / "yuklenen"          # telefondan/drone'dan gelen fotoğraf-videolar (eğitim için de saklanır)
VARSAYILAN = {"suru": 700, "tolerans": 0, "kamera": "", "cizgi": [0.5, 0, 0.5, 1], "yon_ters": False,
              "rapor_saati": "19:30", "otomatik_baslat": True, "video_kaydet": True,
              "giris_kullanici": "", "giris_sifre_hash": "", "model": "koyun-tepeden.pt"}


MODELLER = {  # Ayarlar'daki seçenekler: dosya → açıklama
    "koyun-tepeden.pt": "Beyaz/açık renkli sürü (en hassas, 160/160)",
    "koyun-birlesik.pt": "Karışık sürü: koyun + keçi/koyu renk, köpek ve insanı ayırır",
}


def model_yolu():
    secim = (json.loads(AYAR.read_text()).get("model") if AYAR.exists() else None) or "koyun-tepeden.pt"
    for ad in (secim, "koyun-tepeden.pt", "yolo11s.pt"):
        if (KOK / "modeller" / ad).exists():
            return str(KOK / "modeller" / ad)
    return str(KOK / "modeller" / "yolo11s.pt")


app = Flask(__name__, static_folder=str(KOK / "arayuz"))
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 ** 3
app.secret_key = (KOK / ".gizli").read_text() if (KOK / ".gizli").exists() else None
if not app.secret_key:
    app.secret_key = os.urandom(32).hex()
    (KOK / ".gizli").write_text(app.secret_key)


# --- isteğe bağlı giriş: Ayarlar'da kullanıcı adı + şifre verilirse herkes giriş yapmadan göremez ---
GIRIS_HTML = """<!doctype html><html lang=tr><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Koyun Sayacı — Giriş</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#f4f1ea;font:15px system-ui}
form{background:#fffdf8;border:1px solid #e3ddd0;border-radius:14px;padding:26px 28px;width:300px;box-shadow:0 4px 14px rgba(0,0,0,.05)}
h1{font-size:20px;margin:0 0 14px}label{display:block;font-size:13px;color:#6b7365;margin:10px 0 4px}
input{width:100%;box-sizing:border-box;font:inherit;padding:9px 10px;border:1px solid #e3ddd0;border-radius:8px}
button{width:100%;margin-top:16px;padding:11px;font:inherit;font-weight:600;background:#2f7d3b;color:#fff;border:0;border-radius:10px;cursor:pointer}
.hata{color:#c0392b;font-size:13px;margin-top:8px}</style>
<form method=post><h1>🐑 Koyun Sayacı</h1><label>Kullanıcı adı</label><input name=k autofocus autocomplete=username>
<label>Şifre</label><input name=s type=password autocomplete=current-password><button>Giriş</button>{HATA}</form>"""


def giris_gerekli():
    a = ayarlar()
    return bool(a.get("giris_kullanici") and a.get("giris_sifre_hash"))


@app.before_request
def giris_kontrol():
    if request.path.startswith("/giris") or not giris_gerekli() or session.get("giris"):
        return None
    if request.path.startswith("/api/"):
        return jsonify({"hata": "giriş gerekli"}), 401
    return redirect("/giris")


@app.route("/giris", methods=["GET", "POST"])
def giris():
    if not giris_gerekli():
        return redirect("/")
    hata = ""
    if request.method == "POST":
        a = ayarlar()
        if request.form.get("k") == a["giris_kullanici"] and check_password_hash(a["giris_sifre_hash"], request.form.get("s", "")):
            session["giris"] = True
            defter.sistem_log(f"GİRİŞ yapıldı: {a['giris_kullanici']} ({request.remote_addr})")
            return redirect("/")
        hata = '<div class=hata>Kullanıcı adı ya da şifre yanlış.</div>'
    return GIRIS_HTML.replace("{HATA}", hata)


@app.get("/cikis")
def cikis():
    session.clear()
    return redirect("/giris")
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
                    "goruntu": motor.jpeg is not None, "ayarlar": {k: v for k, v in a.items() if k != "giris_sifre_hash"}, "giris_acik": giris_gerekli(), "demolar": demolar(),
                    "bugun": {k: v for k, v in bugun.items() if k != "olaylar"},
                    "olaylar": bugun["olaylar"][-8:][::-1], "disarida": defter.disarida(bugun),
                    "gecmis": defter.gecmis(), "videolar": videolar, "sistem": defter.son_sistem(12),
                    "model": Path(motor.model_yolu).name,
                    "modeller": {ad: acik for ad, acik in MODELLER.items() if (KOK / "modeller" / ad).exists()},
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
    if d.get("model") in MODELLER and (KOK / "modeller" / d["model"]).exists():
        a["model"] = d["model"]
    for k in ("otomatik_baslat", "video_kaydet"):
        if k in d:
            a[k] = bool(d[k])
    if "giris_kullanici" in d:
        a["giris_kullanici"] = str(d["giris_kullanici"]).strip()
        if not a["giris_kullanici"]:
            a["giris_sifre_hash"] = ""          # kullanıcı adı silindi → giriş kapalı
    if d.get("giris_sifre"):
        a["giris_sifre_hash"] = generate_password_hash(str(d["giris_sifre"]))
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


@app.post("/api/yukle")
def api_yukle():
    """Telefon fotoğrafı / drone videosu yükle → kaç koyun var? Dosya eğitim için yuklenen/ altında kalır."""
    f = request.files.get("dosya")
    if not f or not f.filename:
        return jsonify({"hata": "Dosya seçilmedi."}), 400
    uzanti = Path(f.filename).suffix.lower()
    if uzanti not in (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".mp4", ".mov", ".avi", ".mkv", ".m4v"):
        return jsonify({"hata": f"Desteklenmeyen dosya türü: {uzanti}"}), 400
    YUKLENEN.mkdir(exist_ok=True)
    ad = datetime.now().strftime("%Y%m%d-%H%M%S") + uzanti
    yol = YUKLENEN / ad
    f.save(yol)
    try:
        sonuc = foto_say(model_yolu(), yol, YUKLENEN / (yol.stem + "-sonuc.jpg"))
    except Exception as e:
        return jsonify({"hata": f"Sayılamadı: {e}"}), 400
    defter.sistem_log(f"YÜKLEME sayıldı: {ad} → {sonuc['sayi']} koyun")
    sonuc.update(ad=ad, goruntu=f"/yuklenen/{yol.stem}-sonuc.jpg")
    return jsonify({"ok": True, **sonuc})


@app.get("/yuklenen/<ad>")
def yuklenen_dosya(ad):
    return send_from_directory(YUKLENEN, ad)


@app.post("/api/telegram-test")
def api_telegram_test():
    return jsonify({"ok": gonder("🐑 Koyun Sayacı test mesajı — bildirimler çalışıyor.")})


if __name__ == "__main__":
    defter.sistem_log(f"PROGRAM açıldı, model {Path(model_yolu()).name}")
    threading.Thread(target=bekci, daemon=True).start()
    app.run(host="127.0.0.1", port=int(os.environ.get("KOYUN_PORT", 8780)), threaded=True)
