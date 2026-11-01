"""Koyun sayacı: video dosyası ya da kamera (RTSP) akışında sanal çizgiden geçenleri sayar.

Örnekler:
  python say.py test-video/NmMb.mp4 --cizgi 0.5,0,0.5,1 --kayit cikti.mp4
  (Günlük izleme/rapor için arayüzü kullanın: python app.py)

--cizgi: x1,y1,x2,y2 görüntüye oranla (0-1). Çizginin "solu"ndan "sağı"na geçen = çıkış.
Yön ters çıkarsa --yon-ters ekle.
"""
import argparse
import json
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

from cizgi import CizgiSayaci

KOK = Path(__file__).parent
KOYUN = 18  # COCO sınıfı: sheep


def oranli(c, w, h):
    x1, y1, x2, y2 = (float(v) for v in c.split(","))
    return (x1 * w, y1 * h), (x2 * w, y2 * h)


def say(a):
    model = YOLO(a.model)
    sayac = None
    yazici = None
    kare = 0
    t0 = time.time()
    akis = model.track(source=a.kaynak, stream=True, persist=True, tracker=a.takip,
                       classes=[__import__('siniflar').koyun_sinifi(model)],
                       conf=a.guven, imgsz=a.boyut, device=a.cihaz, verbose=False)
    for r in akis:
        h, w = r.orig_shape
        if sayac is None:
            p1, p2 = oranli(a.cizgi, w, h)
            sayac = CizgiSayaci(p1, p2, yon_ters=a.yon_ters)
        if r.boxes.id is not None:
            for (x1, y1, x2, y2), tid in zip(r.boxes.xyxy.tolist(), r.boxes.id.int().tolist()):
                sayac.guncelle(tid, ((x1 + x2) / 2, (y1 + y2) / 2))
        if a.kayit:
            img = r.plot(line_width=1, font_size=0.4)
            p1, p2 = (tuple(int(v) for v in p) for p in (sayac.a, sayac.b))
            cv2.line(img, p1, p2, (0, 0, 255), 3)
            cv2.rectangle(img, (0, 0), (360, 44), (0, 0, 0), -1)
            cv2.putText(img, f"CIKAN {sayac.cikan}  GIREN {sayac.giren}", (8, 31),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            if yazici is None:
                yazici = cv2.VideoWriter(a.kayit, cv2.VideoWriter_fourcc(*"mp4v"), a.fps, (w, h))
            yazici.write(img)
        kare += 1
        if a.sure and time.time() - t0 > a.sure * 60:
            break
    if yazici:
        yazici.release()
    sn = time.time() - t0
    return {"cikan": sayac.cikan if sayac else 0, "giren": sayac.giren if sayac else 0,
            "kare": kare, "saniye": round(sn, 1), "fps": round(kare / sn, 1) if sn else 0}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kaynak")
    p.add_argument("--cizgi", default="0.5,0,0.5,1")
    p.add_argument("--yon-ters", action="store_true")
    p.add_argument("--model", default=str(KOK / "modeller" / "yolo11s.pt"))
    p.add_argument("--siniflar", default=str(KOYUN))
    p.add_argument("--takip", default="bytetrack.yaml")
    p.add_argument("--guven", type=float, default=0.25)
    p.add_argument("--boyut", type=int, default=960)
    p.add_argument("--cihaz", default=None)
    p.add_argument("--kayit", help="işaretli video çıktısı (.mp4)")
    p.add_argument("--fps", type=float, default=25)
    p.add_argument("--sure", type=float, help="dakika sonra dur (canlı kamera için)")
    a = p.parse_args()

    sonuc = say(a)
    print(json.dumps(sonuc, ensure_ascii=False))


if __name__ == "__main__":
    main()
