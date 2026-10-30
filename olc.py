"""Doğruluk ölçümü: işaretli (gt) videolarda gerçek geçiş sayısı ile programın saydığını karşılaştırır.

  python olc.py                       # hazır model
  python olc.py --model modeller/koyun-tepeden.pt
"""
import argparse
import collections
import json
from pathlib import Path

from ultralytics import YOLO

from cizgi import CizgiSayaci

KOK = Path(__file__).parent
V = KOK / "veri/icaerus/set2/depot_zenodo_2_annotations"
VIDEOLAR = ["8", "10", "12", "13"]
CIZGI_Y = 0.5  # yatay sayma çizgisi (görüntü yüksekliğine oranla)


def gercek_sayi(gt, w, h):
    iz = collections.defaultdict(list)
    for s in open(gt):
        f, i, x, y, bw, bh = s.split(",")[:6]
        iz[int(i)].append((int(f), float(x) + float(bw) / 2, float(y) + float(bh) / 2))
    s = CizgiSayaci((0, CIZGI_Y * h), (w, CIZGI_Y * h))
    for i, p in iz.items():
        for _, cx, cy in sorted(p):
            s.guncelle(i, (cx, cy))
    return s.giren, s.cikan


def program_sayisi(model, video, siniflar, guven, boyut):
    s = None
    for r in model.track(source=str(video), stream=True, persist=False, tracker="bytetrack.yaml",
                         classes=siniflar, conf=guven, imgsz=boyut, verbose=False):
        h, w = r.orig_shape
        if s is None:
            s = CizgiSayaci((0, CIZGI_Y * h), (w, CIZGI_Y * h))
        if r.boxes.id is not None:
            for (x1, y1, x2, y2), tid in zip(r.boxes.xyxy.tolist(), r.boxes.id.int().tolist()):
                s.guncelle(tid, ((x1 + x2) / 2, (y1 + y2) / 2))
    return s.giren, s.cikan


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=str(KOK / "modeller/yolo11s.pt"))
    p.add_argument("--guven", type=float, default=0.25)
    p.add_argument("--boyut", type=int, default=960)
    p.add_argument("--videolar", default=",".join(VIDEOLAR))
    a = p.parse_args()
    model = YOLO(a.model)
    siniflar = [18] if len(model.names) > 1 else [0]
    satirlar, top_g, top_p = [], 0, 0
    for n in a.videolar.split(","):
        video = V / f"Videos/crop_23.11.23-{n}.MP4"
        g_giren, _ = gercek_sayi(V / f"MOT1.1/MOT1.1_crop_23.11.23-{n}/gt/gt.txt", 1440, 1080)
        model = YOLO(a.model)  # her video temiz takipçi
        p_giren, p_cikan = program_sayisi(model, video, siniflar, a.guven, a.boyut)
        satirlar.append({"video": n, "gercek": g_giren, "sayilan": p_giren, "ters": p_cikan})
        top_g += g_giren
        top_p += p_giren
        print(f"video {n:>2}: gerçek {g_giren:3d}  sayılan {p_giren:3d}  (ters yön {p_cikan})", flush=True)
    print(f"TOPLAM: gerçek {top_g}  sayılan {top_p}  hata {top_p - top_g:+d}  "
          f"doğruluk %{100 * (1 - abs(top_p - top_g) / max(top_g, 1)):.1f}")
    print(json.dumps(satirlar))


if __name__ == "__main__":
    main()
