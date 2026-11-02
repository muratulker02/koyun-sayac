"""Vitrin videoları: demo videolarını sayım işaretleriyle (kutu, çizgi, büyük Türkçe sayaç) yeniden yazar.

  .venv/bin/python vitrin/isaretle.py            # tüm demolar
  .venv/bin/python vitrin/isaretle.py kapi-ustu-giris-3   # tek demo (ad, .mp4'süz)

Çıktı: vitrin/video/<ad>.mp4 (H.264, web), vitrin/poster/<ad>.jpg, vitrin/sonuc.json (sayılan/gerçek).
Sayım ayarları uygulamayla aynı: güven 0,25, 960 px, ByteTrack, demonun kendi modeli.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))
from cizgi import CizgiSayaci            # noqa: E402
from siniflar import izlenecek_siniflar, koyun_sinifi  # noqa: E402

VITRIN = KOK / "vitrin"
FONT_B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_R = "/System/Library/Fonts/Supplemental/Arial.ttf"
ETIKET = {1: "KÖPEK · sayılmaz", 2: "İNSAN · sayılmaz"}
RENK = {1: (60, 60, 230), 2: (230, 140, 40)}      # BGR


def yazi(img, metin, xy, boyut, renk=(255, 255, 255), kalin=True):
    """Türkçe karakterli yazı (PIL), BGR görüntüye."""
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil)
    f = ImageFont.truetype(FONT_B if kalin else FONT_R, boyut)
    d.text(xy, metin, font=f, fill=renk[::-1])
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def panel(img, satirlar, x, y, gen):
    """Yarı saydam koyu panel + satırlar [(metin, boyut, renk, kalın)]."""
    yuk = 14 + sum(b + 8 for _, b, _, _ in satirlar)
    kat = img.copy()
    cv2.rectangle(kat, (x, y), (x + gen, y + yuk), (15, 15, 15), -1)
    img = cv2.addWeighted(kat, 0.72, img, 0.28, 0)
    cy = y + 8
    for metin, b, renk, kalin in satirlar:
        img = yazi(img, metin, (x + 14, cy), b, renk, kalin)
        cy += b + 8
    return img


def isle(ad, bilgi):
    kaynak = KOK / "test-video" / f"{ad}.mp4"
    cikti = VITRIN / "video" / f"{ad}.mp4"
    poster = VITRIN / "poster" / f"{ad}.jpg"
    model_ad = bilgi.get("model", "koyun-tepeden.pt")
    model = YOLO(str(KOK / "modeller" / model_ad))
    ks = koyun_sinifi(model)
    siniflar = izlenecek_siniflar(model)
    cizgi = bilgi.get("cizgi")
    gercek = bilgi.get("gercek")
    gercek_yak = bilgi.get("gercek_yaklasik")

    cap = cv2.VideoCapture(str(kaynak))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w, h = int(cap.get(3)), int(cap.get(4))
    cap.release()
    poster_kare = int(n * 0.45)

    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", f"{fps}",
         "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "26", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", str(cikti)], stdin=subprocess.PIPE)

    sayac = None
    kare = 0
    t0 = time.time()
    akis = model.track(source=str(kaynak), stream=True, persist=False, tracker="bytetrack.yaml",
                       classes=siniflar, conf=0.25, imgsz=960, verbose=False)
    for r in akis:
        img = r.orig_img.copy()
        if cizgi and sayac is None:
            x1, y1, x2, y2 = cizgi
            sayac = CizgiSayaci((x1 * w, y1 * h), (x2 * w, y2 * h), yon_ters=bilgi.get("yon_ters", False))
        gorunen = 0
        etiketler = []
        if r.boxes is not None and len(r.boxes):
            idler = r.boxes.id.int().tolist() if r.boxes.id is not None else [None] * len(r.boxes)
            for (bx1, by1, bx2, by2), c, tid in zip(r.boxes.xyxy.tolist(), r.boxes.cls.int().tolist(), idler):
                p1, p2 = (int(bx1), int(by1)), (int(bx2), int(by2))
                if c == ks:
                    gorunen += 1
                    sayildi = False
                    if sayac is not None and tid is not None:
                        sayac.guncelle(tid, ((bx1 + bx2) / 2, (by1 + by2) / 2))
                        sayildi = sayac.sayildi_mi(tid)
                    renk = (255, 170, 0) if sayildi else (60, 220, 60)   # sayılan mavi, bekleyen yeşil
                    cv2.rectangle(img, p1, p2, renk, 2)
                else:
                    cv2.rectangle(img, p1, p2, RENK.get(c, (200, 200, 200)), 3)
                    etiketler.append((ETIKET.get(c, "DİĞER"), p1, RENK.get(c, (200, 200, 200))))
        if sayac is not None:
            a, b = (tuple(int(v) for v in sayac.a), tuple(int(v) for v in sayac.b))
            cv2.line(img, a, b, (0, 0, 255), 4)
            img = yazi(img, "sayım çizgisi", (a[0] + 10, a[1] - 30), 22, (0, 0, 255))
        for metin, p1, renk in etiketler:
            img = yazi(img, metin, (p1[0], max(0, p1[1] - 28)), 22, renk)
        # sayaç paneli
        if sayac is not None:
            sayilan = sayac.cikan + sayac.giren
            hedef = f"{gercek}" if gercek is not None else (f"≈{gercek_yak}" if gercek_yak else "?")
            satirlar = [("Çizgiyi geçen", 24, (210, 210, 210), False),
                        (f"{sayilan}", 72, (255, 255, 255), True),
                        (f"Gerçek sayı: {hedef}", 26, (120, 230, 120), True)]
            img = panel(img, satirlar, 16, 16, 330)
            img = panel(img, [("■ mavi kutu = sayıldı   ■ yeşil = henüz geçmedi", 20, (220, 220, 220), False)],
                        16, h - 54, 520)
        else:
            img = panel(img, [("Ekranda görünen koyun", 24, (210, 210, 210), False),
                              (f"{gorunen}", 72, (255, 255, 255), True),
                              ("Tanıma örneği · sayım çizgisi yok", 22, (120, 230, 120), True)], 16, 16, 400)
        ff.stdin.write(img.tobytes())
        if kare == poster_kare:
            cv2.imwrite(str(poster), img, [cv2.IMWRITE_JPEG_QUALITY, 82])
        kare += 1
    ff.stdin.close()
    ff.wait()
    sonuc = {"ad": ad, "baslik": bilgi.get("baslik"), "model": model_ad, "gercek": gercek,
             "gercek_yaklasik": gercek_yak, "kare": kare, "sure_sn": round(kare / fps, 1),
             "islem_sn": round(time.time() - t0, 1)}
    if sayac is not None:
        sonuc.update({"cikan": sayac.cikan, "giren": sayac.giren, "sayilan": sayac.cikan + sayac.giren})
    print(json.dumps(sonuc, ensure_ascii=False), flush=True)
    return sonuc


def main():
    demolar = json.loads((KOK / "test-video" / "demolar.json").read_text())
    secim = sys.argv[1:] or [k[:-4] for k in demolar]
    yol = VITRIN / "sonuc.json"
    eski = json.loads(yol.read_text()) if yol.exists() else {}
    for ad in secim:
        eski[ad] = isle(ad, demolar[f"{ad}.mp4"])
        yol.write_text(json.dumps(eski, ensure_ascii=False, indent=1))
    print("VITRIN_BITTI")


if __name__ == "__main__":
    main()
