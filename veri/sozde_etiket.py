"""3. tur için sözde etiket: etiketsiz drone videolarından/fotoğraflarından eğitim seti üretir (₺0).

  python veri/sozde_etiket.py <video/foto klasörü> <çıktı klasörü> [--sn 1] [--video-basi 60] [--esik 0.5]

Koyun/keçi: karışık sürü modeli (koyun-birlesik.pt, sınıf 0, güven ≥ --esik).
Köpek / insan: YOLO-World ("dog","person"). Köpek, koyun modelinin ≥0,75 ile koyun dediği yerde sayılmaz
(YOLO-World bazen koyunu köpek sanıyor). İnsan, bir koyun/keçi kutusuyla örtüşüyorsa atılır
(YOLO-World kahverengi keçiyi "person" sanıyor — 31 Eki tespiti).
Köpek kırpımları <çıktı>/kontrol/ altına yazılır → göz ile ayıkla, sonra: python veri/ayikla_kopek.py <çıktı>
Çıktı: images/{train,val}, labels/{train,val}, veri.yaml (0 koyun, 1 kopek, 2 insan).
"""
import argparse
import json
import random
from pathlib import Path

import cv2
from ultralytics import YOLO

KOK = Path(__file__).resolve().parent.parent
UZ_VIDEO = (".mp4", ".mov", ".avi", ".mkv")
UZ_FOTO = (".jpg", ".jpeg", ".png")


def ortusme(a, b):
    ax1, ay1, ax2, ay2 = a; bx1, by1, bx2, by2 = b
    ix = max(0, min(ax2, bx2) - max(ax1, bx1)); iy = max(0, min(ay2, by2) - max(ay1, by1))
    kes = ix * iy
    return kes / max(1e-6, min((ax2 - ax1) * (ay2 - ay1), (bx2 - bx1) * (by2 - by1)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kaynak"); p.add_argument("cikti")
    p.add_argument("--sn", type=float, default=1.0, help="saniyede kaç kare")
    p.add_argument("--video-basi", type=int, default=60, help="bir videodan en çok kaç kare")
    p.add_argument("--esik", type=float, default=0.5, help="koyun güven eşiği")
    p.add_argument("--koyun-yalniz", type=float, default=0.5, help="köpek/insan olmayan karelerin alınma oranı")
    p.add_argument("--boyut", type=int, default=1280)
    p.add_argument("--koyun-kaynak", choices=["model", "world", "ikisi"], default="model",
                   help="koyun kutuları: bizim tepeden model / YOLO-World 'sheep' (yandan çekimler için) / ikisinin birleşimi")
    p.add_argument("--atla", default=None, help="bu klasördeki (images/*/) kare adları atlanır (eski sette zaten var)")
    a = p.parse_args()
    atla = set()
    if a.atla:
        atla = {q.stem for q in Path(a.atla).rglob("*.jpg")}

    OUT = Path(a.cikti)
    for d in ("images/train", "images/val", "labels/train", "labels/val", "kontrol"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    import os
    koyun_m = YOLO(str(KOK / os.environ.get("KOYUN_MODEL", "modeller/koyun-birlesik.pt")))
    genel_m = YOLO(str(KOK / "modeller" / "yolov8s-worldv2.pt"))
    genel_m.set_classes(["dog", "person", "sheep"])
    SHEEP = 2
    random.seed(7)
    sayac = {"kare": 0, "koyun_kutu": 0, "kopek_kutu": 0, "insan_kutu": 0, "atlanan_bos": 0}

    def isle(img, ad):
        h, w = img.shape[:2]
        if ad in atla:
            return False
        g = genel_m.predict(img, imgsz=a.boyut, conf=0.3, verbose=False)[0]
        koyunlar = []
        if a.koyun_kaynak in ("model", "ikisi"):
            k = koyun_m.predict(img, imgsz=a.boyut, conf=a.esik, classes=[0], verbose=False)[0]
            koyunlar = [(tuple(b), c) for b, c in zip(k.boxes.xyxy.tolist(), k.boxes.conf.tolist())]
        if a.koyun_kaynak in ("world", "ikisi"):
            for b, c, conf in zip(g.boxes.xyxy.tolist(), g.boxes.cls.int().tolist(), g.boxes.conf.tolist()):
                if c == SHEEP and conf >= a.esik and not any(ortusme(tuple(b), kb) > 0.5 for kb, _ in koyunlar):
                    koyunlar.append((tuple(b), conf))
        satirlar, kirpimlar, kopek, insan = [], {}, 0, 0
        for (x1, y1, x2, y2), c in koyunlar:
            satirlar.append(f"0 {(x1+x2)/2/w:.6f} {(y1+y2)/2/h:.6f} {(x2-x1)/w:.6f} {(y2-y1)/h:.6f}")
        for b, c, conf in zip(g.boxes.xyxy.tolist(), g.boxes.cls.int().tolist(), g.boxes.conf.tolist()):
            b = tuple(b)
            if c == SHEEP:
                continue
            if c == 0:   # dog
                if conf < 0.40 or any(kc >= 0.75 and ortusme(b, kb) > 0.5 for kb, kc in koyunlar):
                    continue
                sinif = 1
            else:        # person
                if any(ortusme(b, kb) > 0.5 for kb, _ in koyunlar):
                    continue   # keçi/koyunla örtüşen "insan" atılır
                sinif = 2
            x1, y1, x2, y2 = b
            satirlar.append(f"{sinif} {(x1+x2)/2/w:.6f} {(y1+y2)/2/h:.6f} {(x2-x1)/w:.6f} {(y2-y1)/h:.6f}")
            if sinif == 1:
                kopek += 1
                satirlar = [s for s in satirlar if not (s.startswith("0 ") and ortusme(b, _kutu(s, w, h)) > 0.5)]
                cx, cy, boy = (x1+x2)/2, (y1+y2)/2, max(x2-x1, y2-y1)
                ox, oy = max(0, int(cx-3*boy)), max(0, int(cy-3*boy))
                kes = img[oy:int(cy+3*boy), ox:int(cx+3*boy)].copy()
                if kes.size:
                    cv2.rectangle(kes, (int(x1-ox), int(y1-oy)), (int(x2-ox), int(y2-oy)), (0, 0, 255), 3)
                    kad = f"{ad}_{conf:.2f}.jpg"
                    cv2.imwrite(str(OUT / "kontrol" / kad), cv2.resize(kes, (320, max(1, int(320*kes.shape[0]/max(1, kes.shape[1]))))))
                    kirpimlar[kad] = satirlar[-1] if sinif == 1 else None
            else:
                insan += 1
        if not satirlar:
            sayac["atlanan_bos"] += 1
            return False
        if not (kopek or insan) and random.random() > a.koyun_yalniz:
            return False
        bol = "val" if random.random() < 0.15 else "train"
        cv2.imwrite(str(OUT / "images" / bol / f"{ad}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        (OUT / "labels" / bol / f"{ad}.txt").write_text("\n".join(satirlar) + "\n")
        with open(OUT / "kontrol" / "esleme.jsonl", "a") as f:
            for kad, satir in kirpimlar.items():
                f.write(json.dumps({"kirpim": kad, "etiket": f"labels/{bol}/{ad}.txt", "satir": satir}) + "\n")
        sayac["kare"] += 1; sayac["koyun_kutu"] += len(koyunlar); sayac["kopek_kutu"] += kopek; sayac["insan_kutu"] += insan
        return True

    def _kutu(s, w, h):
        _, cx, cy, bw, bh = map(float, s.split())
        return ((cx-bw/2)*w, (cy-bh/2)*h, (cx+bw/2)*w, (cy+bh/2)*h)

    dosyalar = sorted(p for p in Path(a.kaynak).rglob("*") if p.suffix.lower() in UZ_VIDEO + UZ_FOTO)
    for d in dosyalar:
        if d.suffix.lower() in UZ_FOTO:
            img = cv2.imread(str(d))
            if img is not None:
                isle(img, d.stem)
            continue
        cap = cv2.VideoCapture(str(d))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        adim = max(1, int(fps / a.sn))
        kareler = list(range(0, n, adim))
        if len(kareler) > a.video_basi:   # uzun videoda eşit aralıklı seçim
            kareler = kareler[:: max(1, len(kareler) // a.video_basi)][: a.video_basi]
        for i in kareler:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, img = cap.read()
            if not ok:
                break
            isle(img, f"{d.stem}_k{i}")
        cap.release()
        print(d.name, sayac, flush=True)

    (OUT / "veri.yaml").write_text(f"path: {OUT.resolve()}\ntrain: images/train\nval: images/val\nnames:\n  0: koyun\n  1: kopek\n  2: insan\n")
    print("BITTI", sayac)


if __name__ == "__main__":
    main()
