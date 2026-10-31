"""Modelleri sayısı bilinmeyen (≈50) kapı-üstü videolarında kıyaslar: sayı + şüpheli + ortalama kutu güveni.
  python kiyas.py egitimler/test12-y26/weights/best.pt egitimler/buyuk-y11/weights/best.pt ...
"""
import sys
from pathlib import Path

from ultralytics import YOLO

from cizgi import CizgiSayaci

KOK = Path(__file__).parent
VIDEOLAR = ["kapi-ustu-giris-3.mp4", "kapi-ustu-giris-4.mp4", "kapi-ustu-giris-11.mp4"]

for m in sys.argv[1:]:
    print(f"## {m}")
    for v in VIDEOLAR:
        model = YOLO(m)
        s, guven, n, aktif = None, [], 0, set()
        for r in model.track(source=str(KOK / "test-video" / v), stream=True, imgsz=960, conf=0.25,
                             tracker="bytetrack.yaml", verbose=False):
            h, w = r.orig_shape
            if s is None:
                s = CizgiSayaci((0, h / 2), (w, h / 2))
            aktif = set()
            if r.boxes.id is not None:
                for (x1, y1, x2, y2), tid, c in zip(r.boxes.xyxy.tolist(), r.boxes.id.int().tolist(), r.boxes.conf.tolist()):
                    s.guncelle(tid, ((x1 + x2) / 2, (y1 + y2) / 2))
                    guven.append(c)
                    aktif.add(tid)
            n += 1
        print(f"  {v}: geçen {s.giren + s.cikan:3d} (giriş {s.giren}, çıkış {s.cikan})  "
              f"numara {len(s.gorulme)}  şüpheli {len(s.supheli(aktif))}  ort.güven {sum(guven) / max(1, len(guven)):.2f}")
