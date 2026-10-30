"""Telegram bildirimi. TELEGRAM_TOKEN ve TELEGRAM_CHAT_ID .env'de yoksa sadece ekrana yazar."""
import os
from pathlib import Path

import requests


def _env():
    f = Path(__file__).parent / ".env"
    if f.exists():
        for satir in f.read_text().splitlines():
            if "=" in satir and not satir.startswith("#"):
                k, v = satir.split("=", 1)
                os.environ[k.strip()] = v.strip()


def gonder(mesaj):
    _env()
    token, sohbet = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and sohbet):
        print(f"[telegram kapalı] {mesaj}")
        return False
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      data={"chat_id": sohbet, "text": mesaj}, timeout=20)
    return r.ok
