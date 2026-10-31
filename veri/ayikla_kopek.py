"""Göz kontrolünden sonra: kontrol/ klasöründen SİLDİĞİN kırpımların köpek etiketini setten çıkarır.
  python veri/ayikla_kopek.py <çıktı klasörü>
"""
import json
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
silinen = 0
for satir in (OUT / "kontrol" / "esleme.jsonl").read_text().splitlines():
    e = json.loads(satir)
    if (OUT / "kontrol" / e["kirpim"]).exists():
        continue                       # kırpım duruyor → etiket doğru kabul edildi
    y = OUT / e["etiket"]
    if not y.exists():
        continue
    kalan = [s for s in y.read_text().splitlines() if s.strip() != e["satir"].strip()]
    y.write_text("\n".join(kalan) + ("\n" if kalan else ""))
    silinen += 1
print(f"{silinen} köpek etiketi çıkarıldı")
