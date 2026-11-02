"""Model dosyalarını GitHub Releases'ten modeller/ içine indirir (depoda tutulmazlar).

  python modeller/indir.py            # eksik olanları indirir
  python modeller/indir.py --zorla    # hepsini yeniden indirir
"""
import sys
import urllib.request
from pathlib import Path

KOK = Path(__file__).resolve().parent
SURUM = "v1.0"
TABAN = f"https://github.com/muratulker02/koyun-sayac/releases/download/{SURUM}/"
DOSYALAR = ["koyun-tepeden.pt", "koyun-heracidan.pt", "koyun-birlesik.pt", "yolov8s-worldv2.pt"]


def indir(ad):
    hedef = KOK / ad
    gecici = hedef.with_suffix(".indiriliyor")
    print(f"  {ad} ...", end="", flush=True)
    with urllib.request.urlopen(TABAN + ad, timeout=60) as r, open(gecici, "wb") as f:
        toplam = 0
        while True:
            parca = r.read(1 << 20)
            if not parca:
                break
            f.write(parca)
            toplam += len(parca)
    gecici.rename(hedef)
    print(f" {toplam / 1e6:.1f} MB")


def main():
    zorla = "--zorla" in sys.argv
    print(f"Modeller ({SURUM}) → {KOK}")
    for ad in DOSYALAR:
        if (KOK / ad).exists() and not zorla:
            print(f"  {ad} zaten var")
            continue
        indir(ad)
    print("BITTI")


if __name__ == "__main__":
    main()
