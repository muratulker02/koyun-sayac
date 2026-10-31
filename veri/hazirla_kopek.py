"""Köpek/insan sınıflı eğitim seti hazırla (₺0, otomatik etiket + göz kontrolü).

Yeni videolardan saniyede 1 kare alır; koyunları bizim modelle, köpek ve insanı YOLO-World ("dog","person"
sözcük komutlu açık-sözlüklü model) etiketler. (COCO yolo11s denendi: koyunu köpek sanıyor, gerçek
köpeği görmüyor → kullanılmaz. YOLO-World beyaz köpeği 0,63 ile buldu, 31 Eki.) Sınıflar: 0 koyun, 1 kopek, 2 insan.
Köpek/insan içeren her kare + koyun-yalnız karelerin bir örneği eğitime girer.
Köpek tespitlerinin küçük kırpımları `kontrol/` altına yazılır → yanlışları göz ile ayıkla.

  python veri/hazirla_kopek.py <video klasörü> <çıktı klasörü> [kare/sn=1]
"""
import json
import random
import sys
from pathlib import Path

import cv2
from ultralytics import YOLO

KOK = Path(__file__).resolve().parent.parent
VIDEOLAR, OUT = Path(sys.argv[1]), Path(sys.argv[2])
HER_SN = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
for d in ("images/train", "images/val", "labels/train", "labels/val", "kontrol"):
    (OUT / d).mkdir(parents=True, exist_ok=True)

koyun_m = YOLO(str(KOK / "modeller" / "koyun-tepeden.pt"))
genel_m = YOLO(str(KOK / "modeller" / "yolov8s-worldv2.pt"))
genel_m.set_classes(["dog", "person"])
KOPEK, INSAN = 0, 1
KOPEK_ESIK = 0.40
random.seed(7)
def _ortusuyor(satir, x1, y1, x2, y2, w, h):
    _, cx, cy, bw, bh = map(float, satir.split())
    ax1, ay1, ax2, ay2 = (cx-bw/2)*w, (cy-bh/2)*h, (cx+bw/2)*w, (cy+bh/2)*h
    ix = max(0, min(ax2, x2) - max(ax1, x1)); iy = max(0, min(ay2, y2) - max(ay1, y1))
    kes = ix * iy; a = (ax2-ax1)*(ay2-ay1); b = (x2-x1)*(y2-y1)
    return kes / max(1e-6, min(a, b)) > 0.5

sayac = {"kare": 0, "kopekli": 0, "insanli": 0, "koyun_yalniz": 0, "kopek_kutu": 0, "insan_kutu": 0}

videolar = sorted(p for p in Path(VIDEOLAR).rglob("*") if p.suffix.lower() in (".mp4", ".mov"))
for v in videolar:
    cap = cv2.VideoCapture(str(v))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    adim = max(1, int(fps / HER_SN))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    for i in range(0, n, adim):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, img = cap.read()
        if not ok:
            break
        h, w = img.shape[:2]
        k = koyun_m.predict(img, imgsz=1280, conf=0.3, verbose=False)[0]
        g = genel_m.predict(img, imgsz=1280, conf=0.3, verbose=False)[0]
        satirlar = []
        koyun_kutular = list(zip(k.boxes.xyxy.tolist(), k.boxes.conf.tolist()))
        for (x1, y1, x2, y2), _ in koyun_kutular:
            satirlar.append(f"0 {(x1+x2)/2/w:.6f} {(y1+y2)/2/h:.6f} {(x2-x1)/w:.6f} {(y2-y1)/h:.6f}")
        kirpimlar = {}   # kırpım dosyası → bu karedeki etiket satırı (ayıklama için)
        kopek = insan = 0
        for (x1, y1, x2, y2), c, conf in zip(g.boxes.xyxy.tolist(), g.boxes.cls.int().tolist(), g.boxes.conf.tolist()):
            if c == KOPEK and conf < KOPEK_ESIK:
                continue
            # koyun modelinin ≥0,75 güvenle koyun dediği yer köpek sayılmaz (YOLO-World bazen koyunu köpek sanıyor)
            if c == KOPEK and any(kc >= 0.75 and _ortusuyor(f"0 {(a+b)/2/w} {(cc+d)/2/h} {(b-a)/w} {(d-cc)/h}", x1, y1, x2, y2, w, h)
                                  for (a, cc, b, d), kc in koyun_kutular):
                continue
            sinif = 1 if c == KOPEK else 2
            kopek += sinif == 1; insan += sinif == 2
            satirlar.append(f"{sinif} {(x1+x2)/2/w:.6f} {(y1+y2)/2/h:.6f} {(x2-x1)/w:.6f} {(y2-y1)/h:.6f}")
            # koyun modelinin aynı yere çizdiği kutuyu sil (köpek koyun değil)
            satirlar = [s for s in satirlar if not (s.startswith("0 ") and _ortusuyor(s, x1, y1, x2, y2, w, h))] if sinif == 1 else satirlar
            if sinif == 1:
                cx, cy, boy = (x1+x2)/2, (y1+y2)/2, max(x2-x1, y2-y1)
                kes = img[max(0, int(cy-3*boy)):int(cy+3*boy), max(0, int(cx-3*boy)):int(cx+3*boy)]
                if kes.size:
                    kes = kes.copy()
                    ox, oy = max(0, int(cx-3*boy)), max(0, int(cy-3*boy))
                    cv2.rectangle(kes, (int(x1-ox), int(y1-oy)), (int(x2-ox), int(y2-oy)), (0, 0, 255), 3)
                    kad = f"{v.stem}_k{i}_{conf:.2f}.jpg"
                    cv2.imwrite(str(OUT / "kontrol" / kad), cv2.resize(kes, (320, int(320*kes.shape[0]/max(1, kes.shape[1])))))
                    kirpimlar[kad] = satirlar[-1]
        if not satirlar:
            continue
        al = kopek or insan or random.random() < 0.15   # koyun-yalnız karelerin %15'i
        if not al:
            continue
        bol = "val" if random.random() < 0.15 else "train"
        ad = f"{v.stem}_k{i}"
        cv2.imwrite(str(OUT / "images" / bol / f"{ad}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        (OUT / "labels" / bol / f"{ad}.txt").write_text("\n".join(satirlar) + "\n")
        for kad, satir in kirpimlar.items():
            with open(OUT / "kontrol" / "esleme.jsonl", "a") as f:
                f.write(json.dumps({"kirpim": kad, "etiket": f"labels/{bol}/{ad}.txt", "satir": satir}) + "\n")
        sayac["kare"] += 1; sayac["kopekli"] += bool(kopek); sayac["insanli"] += bool(insan)
        sayac["koyun_yalniz"] += not (kopek or insan); sayac["kopek_kutu"] += kopek; sayac["insan_kutu"] += insan
    cap.release()
    print(v.name, sayac, flush=True)

(OUT / "veri.yaml").write_text(f"path: {OUT.resolve()}\ntrain: images/train\nval: images/val\nnames:\n  0: koyun\n  1: kopek\n  2: insan\n")
print("BITTI", sayac)

