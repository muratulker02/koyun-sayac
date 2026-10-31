"""Telegram zinciri uçtan uca: sahte Telegram sunucusu → Bağla → .env → mesaj → günlük → rapor.
Gerçek bot anahtarı gerekmez; yalnız api.telegram.org adresi yerel sunucuya çevrilir."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

KOK = Path(__file__).parent
GELEN = []  # sahte Telegram'a düşen sendMessage çağrıları


class SahteTelegram(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _yaz(self, obj):
        g = json.dumps(obj).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(g))); self.end_headers(); self.wfile.write(g)

    def do_GET(self):
        yol = urlparse(self.path).path
        token = yol.split("/bot", 1)[1].split("/", 1)[0]
        if token != "111:DOGRU":
            return self._yaz({"ok": False, "error_code": 401, "description": "Unauthorized"})
        if yol.endswith("/getMe"):
            return self._yaz({"ok": True, "result": {"username": "koyun_test_bot"}})
        if yol.endswith("/getUpdates"):
            return self._yaz({"ok": True, "result": [{"message": {"chat": {"id": 424242, "first_name": "Murat"}, "text": "merhaba"}}]})
        self._yaz({"ok": False})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        govde = parse_qs(self.rfile.read(n).decode())
        if self.path.endswith("/sendMessage"):
            GELEN.append({"chat_id": govde["chat_id"][0], "text": govde["text"][0]})
            return self._yaz({"ok": True, "result": {"message_id": len(GELEN)}})
        self._yaz({"ok": False})


def main():
    sunucu = HTTPServer(("127.0.0.1", 0), SahteTelegram)
    threading.Thread(target=sunucu.serve_forever, daemon=True).start()
    api = f"http://127.0.0.1:{sunucu.server_port}"

    # programı geçici bir kopya klasöründe, ayrı portta aç (gerçek kayıtlara dokunma)
    gecici = Path(tempfile.mkdtemp(prefix="koyun-tg-"))
    for d in ("app.py", "motor.py", "cizgi.py", "defter.py", "bildir.py", "arayuz", "takip", "modeller", "test-video"):
        (shutil.copytree if (KOK / d).is_dir() else shutil.copy)(KOK / d, gecici / d)
    port = 8799
    env = {**os.environ, "TELEGRAM_API": api, "KOYUN_PORT": str(port)}
    p = subprocess.Popen([sys.executable, "app.py"], cwd=gecici, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for _ in range(60):
            try:
                requests.get(f"http://127.0.0.1:{port}/api/durum", timeout=1); break
            except Exception:
                time.sleep(0.5)
        else:
            raise SystemExit("program açılmadı: " + p.stderr.read().decode()[-800:])
        U = f"http://127.0.0.1:{port}"
        sonuc = []

        r = requests.post(f"{U}/api/telegram-bagla", json={"telegram_token": "999:YANLIS"}).json()
        sonuc.append(("yanlış anahtar reddedildi", "geçersiz" in r.get("hata", "")))

        r = requests.post(f"{U}/api/telegram-bagla", json={"telegram_token": "111:DOGRU"}).json()
        sonuc.append(("Bağla ok, bot adı", r.get("ok") is True and r.get("bot") == "koyun_test_bot" and r.get("kim") == "Murat"))
        env_metin = (gecici / ".env").read_text()
        sonuc.append((".env yazıldı", "TELEGRAM_TOKEN=111:DOGRU" in env_metin and "TELEGRAM_CHAT_ID=424242" in env_metin))
        sonuc.append(("hoş geldin mesajı Telegram'a gitti", len(GELEN) == 1 and GELEN[0]["chat_id"] == "424242" and "bağlandı" in GELEN[0]["text"]))
        d = requests.get(f"{U}/api/durum").json()
        sonuc.append(("arayüz telegram=açık", d.get("telegram") is True))
        sonuc.append(("sistem günlüğüne düştü", any("TELEGRAM bağlandı: @koyun_test_bot" in s for s in d.get("sistem", []))))

        r = requests.post(f"{U}/api/telegram-test").json()
        sonuc.append(("Deneme düğmesi mesaj gönderdi", r.get("ok") is True and len(GELEN) == 2))

        r = requests.post(f"{U}/api/rapor").json()
        sonuc.append(("Şimdi rapor gönder → Telegram", r.get("ok") is True and len(GELEN) == 3 and "Anlık durum" in GELEN[2]["text"]))

        for ad, ok in sonuc:
            print(("✅" if ok else "❌"), ad)
        print("\nSahte Telegram'a düşen mesajlar:")
        for g in GELEN:
            print(" →", g["chat_id"], "|", g["text"].replace("\n", " / ")[:120])
        basarisiz = [ad for ad, ok in sonuc if not ok]
        if basarisiz:
            raise SystemExit(f"\nBAŞARISIZ: {basarisiz}")
        print(f"\n{len(sonuc)}/{len(sonuc)} geçti")
    finally:
        p.kill(); sunucu.shutdown(); shutil.rmtree(gecici, ignore_errors=True)


if __name__ == "__main__":
    main()
