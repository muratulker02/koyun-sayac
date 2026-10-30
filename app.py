"""Koyun Sayacı arayüzü. Çalıştır: .venv/bin/python app.py  →  http://127.0.0.1:8780"""
import json
import time
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

from bildir import gonder
from defter import deftere_yaz, gecmis
from motor import Motor

KOK = Path(__file__).parent
AYAR = KOK / "ayarlar.json"
VARSAYILAN = {"suru": 700, "tolerans": 0, "kamera": "", "cizgi": [0.5, 0, 0.5, 1], "yon_ters": False}

app = Flask(__name__, static_folder=str(KOK / "arayuz"))
motor = Motor(str(KOK / "modeller" / "yolo11s.pt"))
oturum = {"ad": None, "mesaj": ""}


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


def demolar():
    return sorted(p.name for p in (KOK / "test-video").glob("*.mp4") if not p.name.startswith("sonuc-"))


def oturum_kaydedici(ad):
    """Sayım bitince (video sonu ya da 'Bitir') o oturumu deftere yazar."""
    def kaydet(ozet):
        a = ayarlar()
        oturum["mesaj"] = deftere_yaz(ad, {"cikan": ozet["cikan"], "giren": ozet["giren"]},
                                      a["suru"], a["tolerans"])
        oturum["ad"] = None
    return kaydet if ad else None


@app.get("/")
def ana():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/demo/<ad>")
def demo_dosya(ad):
    return send_from_directory(KOK / "test-video", ad)


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
def durum():
    a = ayarlar()
    e = env_oku()
    return jsonify({**motor.ozet(), "oturum": oturum["ad"], "mesaj": oturum["mesaj"],
                    "ayarlar": a, "demolar": demolar(), "gecmis": gecmis(),
                    "goruntu": motor.jpeg is not None,
                    "telegram": bool(e.get("TELEGRAM_TOKEN") and e.get("TELEGRAM_CHAT_ID"))})


@app.post("/api/baslat")
def baslat():
    d = request.json or {}
    a = ayarlar()
    if d.get("tur") == "demo":
        kaynak, gercek_hiz = str(KOK / "test-video" / d["demo"]), d.get("gercek_hiz", True)
    else:
        if not a["kamera"]:
            return jsonify({"hata": "Önce Ayarlar'dan kamera adresini girin."}), 400
        kaynak, gercek_hiz = a["kamera"], False
    oturum["ad"] = d.get("oturum")  # sabah | aksam | None (sadece test)
    oturum["mesaj"] = ""
    motor.cizgi_ayarla(a["cizgi"], a["yon_ters"])
    motor.baslat(kaynak, gercek_hiz=gercek_hiz, bitince=oturum_kaydedici(oturum["ad"]))
    return jsonify({"ok": True})


@app.post("/api/durdur")
def durdur():
    """Bitir: oturum açıksa o ana kadarki sayı deftere yazılır (motor iş parçacığı yazar)."""
    motor.durdur()
    return jsonify({"ok": True, "mesaj": oturum["mesaj"]})


@app.post("/api/cizgi")
def cizgi():
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
def ayarlar_kaydet():
    d = request.json or {}
    a = ayarlar()
    for k in ("suru", "tolerans"):
        if k in d:
            a[k] = int(d[k])
    if "kamera" in d:
        a["kamera"] = d["kamera"].strip()
    ayar_kaydet(a)
    if d.get("telegram_token") or d.get("telegram_chat"):
        e = env_oku()
        if d.get("telegram_token"):
            e["TELEGRAM_TOKEN"] = d["telegram_token"].strip()
        if d.get("telegram_chat"):
            e["TELEGRAM_CHAT_ID"] = d["telegram_chat"].strip()
        (KOK / ".env").write_text("".join(f"{k}={v}\n" for k, v in e.items()))
    return jsonify({"ok": True})


@app.post("/api/telegram-test")
def telegram_test():
    return jsonify({"ok": gonder("🐑 Koyun Sayacı test mesajı — bildirimler çalışıyor.")})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8780, threaded=True)
