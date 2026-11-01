"""Eğitim — Mac (MPS), Windows (CUDA) ve CPU'da aynı komut.

  python veri/egit.py --veri veri/egitim-birlesik/veri.yaml --temel modeller/koyun-birlesik.pt --ad birlesik-r3 --tur 30

Bitince en iyi ağırlık modeller/<ad>.pt olarak kopyalanır ve 'EGITIM_BITTI' basılır.
Varsayılanlar 2. turun kazanan ayarları: mozaiksiz ince ayar, düşük öğrenme hızı, 180° döndürme + ayna
(tepeden kamera her yöne bakabilir). Cihaz otomatik: cuda > mps > cpu.
"""
import argparse
import shutil
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent


def cihaz():
    import torch
    if torch.cuda.is_available():
        return "0"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--veri", required=True, help="veri.yaml")
    p.add_argument("--temel", default=str(KOK / "modeller" / "koyun-birlesik.pt"), help="başlangıç ağırlığı")
    p.add_argument("--ad", required=True, help="koşu adı; çıktı modeller/<ad>.pt")
    p.add_argument("--tur", type=int, default=30)
    p.add_argument("--boyut", type=int, default=960)
    p.add_argument("--batch", type=int, default=16, help="RTX 5060 Ti 16 GB: 16; 8 GB kart: 8")
    p.add_argument("--lr", type=float, default=0.002)
    p.add_argument("--mozaik-kapat", type=int, default=None, help="son kaç turda mozaik kapansın (varsayılan: hepsi = mozaiksiz)")
    p.add_argument("--sabir", type=int, default=10)
    p.add_argument("--isci", type=int, default=8)
    a = p.parse_args()

    from ultralytics import YOLO
    proje = KOK / "egitimler"
    proje.mkdir(exist_ok=True)
    m = YOLO(a.temel)
    m.train(data=a.veri, epochs=a.tur, imgsz=a.boyut, batch=a.batch, device=cihaz(),
            project=str(proje), name=a.ad, exist_ok=True, patience=a.sabir,
            close_mosaic=a.mozaik_kapat if a.mozaik_kapat is not None else a.tur,
            lr0=a.lr, lrf=0.05, warmup_epochs=1, degrees=180, flipud=0.5, fliplr=0.5, scale=0.3, hsv_v=0.3,
            workers=a.isci, plots=True)
    # Ultralytics bazen project yolunun önüne runs/detect ekliyor → her iki yerde ara
    adaylar = [proje / a.ad / "weights" / "best.pt", KOK / "runs" / "detect" / "egitimler" / a.ad / "weights" / "best.pt"]
    adaylar += list(KOK.glob(f"**/{a.ad}/weights/best.pt"))
    for b in adaylar:
        if b.exists():
            hedef = KOK / "modeller" / f"{a.ad}.pt"
            shutil.copy2(b, hedef)
            print("MODEL:", hedef)
            break
    else:
        print("UYARI: best.pt bulunamadı; egitimler/ altına bak")
    print("EGITIM_BITTI")


if __name__ == "__main__":
    main()
