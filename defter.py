"""Günlük kayıt defteri: gün boyu çıkan / giren toplamı, dışarıda kalan ve akşam raporu.

kayitlar/YYYY-MM-DD.json → {"cikan": 700, "giren": 698, "olaylar": [...], "rapor": "..."}
"""
import json
import threading
from datetime import date, datetime
from pathlib import Path

KOK = Path(__file__).parent
KLASOR = KOK / "kayitlar"
_kilit = threading.Lock()


def _dosya(gun=None):
    return KLASOR / f"{(gun or date.today()).isoformat()}.json"


def oku(gun=None):
    f = _dosya(gun)
    k = json.loads(f.read_text()) if f.exists() else {}
    k.setdefault("cikan", 0)
    k.setdefault("giren", 0)
    k.setdefault("olaylar", [])
    return k


def _yaz(k, gun=None):
    KLASOR.mkdir(exist_ok=True)
    _dosya(gun).write_text(json.dumps(k, ensure_ascii=False, indent=1))


def ekle(cikan=0, giren=0):
    """Bugünün toplamına yeni geçişleri ekler (motorun sayaç farkı)."""
    if not (cikan or giren):
        return oku()
    with _kilit:
        k = oku()
        k["cikan"] += cikan
        k["giren"] += giren
        saat = datetime.now().strftime("%H:%M:%S")
        k["olaylar"].append([saat, cikan, giren])
        if not k.get("ilk_cikis") and cikan:
            k["ilk_cikis"] = saat[:5]
        if giren:
            k["son_giris"] = saat[:5]
        _yaz(k)
        return k


def disarida(k):
    return k["cikan"] - k["giren"]


def rapor_metni(k, suru=0, tolerans=0):
    d = disarida(k)
    if k["cikan"] == 0 and k["giren"] == 0:
        return "ℹ️ Bugün hiç geçiş sayılmadı (kamera çalışıyor mu?)"
    if d > tolerans:
        return f"⚠️ EKSİK VAR: {k['cikan']} çıktı, {k['giren']} girdi → {d} koyun DIŞARIDA"
    if d < -tolerans:
        return f"❓ Fazla giriş: {k['cikan']} çıktı, {k['giren']} girdi ({-d} fazla) — kaydı kontrol edin"
    ek = f" (sürü {suru})" if suru and abs(k['cikan'] - suru) > tolerans else ""
    return f"✅ Tamam: {k['cikan']} çıktı, {k['giren']} girdi — hepsi içeride{ek}"


def rapor_kaydet(metin):
    with _kilit:
        k = oku()
        k["rapor"] = metin
        k["rapor_saat"] = datetime.now().strftime("%H:%M")
        _yaz(k)


def gecmis(gun=14):
    if not KLASOR.exists():
        return []
    out = []
    for f in sorted(KLASOR.glob("*.json"), reverse=True)[:gun]:
        k = json.loads(f.read_text())
        k.pop("olaylar", None)
        out.append({"tarih": f.stem, **k})
    return out
