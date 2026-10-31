"""Bir klasördeki videoları son modelle toplu say (paralel işçi destekli).
Her video: sayı (iki yön), şüpheli, süre; + sürüden uzak orta-güvenli 'yalnız' tespitler → köpek/insan adayı kare.
  python veri/say_toplu.py <video klasörü> <çıktı klasörü> [işçi_no işçi_sayısı]
Örn. 3 paralel: ... 0 3 | ... 1 3 | ... 2 3  → sonuc-<işçi>.csv; birleştirmek için: cat sonuc-*.csv
"""
import csv
import sys
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))
from cizgi import CizgiSayaci  # noqa: E402

M = str(KOK / "modeller" / "koyun-tepeden.pt")
KLASOR, OUT = Path(sys.argv[1]), Path(sys.argv[2])
ISCI, ISCI_N = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1)
(OUT / "aday").mkdir(parents=True, exist_ok=True)
videolar = sorted(p for p in KLASOR.rglob("*") if p.suffix.lower() in (".mp4", ".mov", ".avi", ".mkv"))
videolar = [v for i, v in enumerate(videolar) if i % ISCI_N == ISCI]
csv_yolu = OUT / f"sonuc-{ISCI}.csv"
bitenler = {s.split(",")[0] for s in csv_yolu.read_text().splitlines()[1:]} if csv_yolu.exists() else set()
videolar = [v for v in videolar if v.name not in bitenler]   # yarıda kalan koşu kaldığı yerden sürer
print(f"işçi {ISCI}/{ISCI_N}: {len(videolar)} video", flush=True)

yeni = not csv_yolu.exists()
with open(csv_yolu, "a") as fcsv:
    yaz = csv.writer(fcsv)
    if yeni:
        yaz.writerow(["video", "kare", "sayilan", "asagi", "yukari", "supheli", "aday_kare", "sn"])
    for v in videolar:
        model = YOLO(M)
        s, n, t, aday, son_aday_kare = None, 0, time.time(), 0, -999
        for r in model.track(source=str(v), stream=True, imgsz=960, conf=0.25, tracker="bytetrack.yaml", verbose=False):
            h, w = r.orig_shape; n += 1
            if s is None:
                s = CizgiSayaci((0, h / 2), (w, h / 2))
            aktif = set()
            kutular = r.boxes.xyxy.tolist() if r.boxes is not None else []
            if r.boxes.id is not None:
                for (x1, y1, x2, y2), tid in zip(kutular, r.boxes.id.int().tolist()):
                    aktif.add(tid); s.guncelle(tid, ((x1 + x2) / 2, (y1 + y2) / 2))
            if len(kutular) >= 2 and n - son_aday_kare > 45:
                confs = r.boxes.conf.tolist()
                for i, (x1, y1, x2, y2) in enumerate(kutular):
                    cx, cy, boy = (x1 + x2) / 2, (y1 + y2) / 2, max(x2 - x1, y2 - y1)
                    en_yakin = min(((cx - (a + b) / 2) ** 2 + (cy - (c + d) / 2) ** 2) ** 0.5
                                   for j, (a, c, b, d) in enumerate(kutular) if j != i)
                    if en_yakin > 3 * boy and 0.3 <= confs[i] <= 0.75:
                        img = r.orig_img.copy()
                        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 4)
                        X1, Y1 = max(0, int(cx - 6 * boy)), max(0, int(cy - 6 * boy))
                        kes = img[Y1:int(cy + 6 * boy), X1:int(cx + 6 * boy)]
                        if kes.size:
                            kes = cv2.resize(kes, (480, int(480 * kes.shape[0] / max(1, kes.shape[1]))))
                            cv2.imwrite(str(OUT / "aday" / f"{v.stem}_k{n}_{confs[i]:.2f}.jpg"), kes, [cv2.IMWRITE_JPEG_QUALITY, 70])
                            aday += 1; son_aday_kare = n
                        break
        sup = len(s.supheli(set())) if s else 0
        say = (s.cikan + s.giren) if s else 0
        satir = [v.name, n, say, s.giren if s else 0, s.cikan if s else 0, sup, aday, round(time.time() - t, 1)]
        yaz.writerow(satir); fcsv.flush(); print(" ".join(map(str, satir)), flush=True)
print("BITTI", flush=True)
