"""Günlük kayıt defteri: sabah çıkan / akşam giren, karşılaştırma ve bildirim."""
import json
from datetime import date, datetime
from pathlib import Path

from bildir import gonder

KOK = Path(__file__).parent


def deftere_yaz(oturum, sonuc, beklenen, tolerans):
    d = KOK / "kayitlar"
    d.mkdir(exist_ok=True)
    f = d / f"{date.today().isoformat()}.json"
    kayit = json.loads(f.read_text()) if f.exists() else {}
    kayit[oturum] = {**sonuc, "saat": datetime.now().strftime("%H:%M")}
    f.write_text(json.dumps(kayit, ensure_ascii=False, indent=2))

    if oturum == "sabah":
        cikan = sonuc["cikan"]
        mesaj = f"🌅 Sabah çıkış: {cikan} koyun"
        if beklenen and abs(cikan - beklenen) > tolerans:
            mesaj += f" (sürü {beklenen}, fark {cikan - beklenen:+d})"
    else:
        cikan = kayit.get("sabah", {}).get("cikan")
        giren = sonuc["giren"]
        if cikan is None:
            mesaj = f"🌙 Akşam giriş: {giren} koyun (sabah kaydı yok!)"
        elif cikan - giren > tolerans:
            mesaj = f"⚠️ EKSİK VAR: sabah {cikan} çıktı, akşam {giren} girdi → {cikan - giren} eksik"
        else:
            mesaj = f"✅ Tamam: sabah {cikan} çıktı, akşam {giren} girdi"
    gonder(mesaj)
    return mesaj


def gecmis(gun=14):
    d = KOK / "kayitlar"
    if not d.exists():
        return []
    out = []
    for f in sorted(d.glob("*.json"), reverse=True)[:gun]:
        k = json.loads(f.read_text())
        out.append({"tarih": f.stem, **k})
    return out
