"""Telefondan/drone'dan gelen tek fotoğraf ya da video → kaç koyun var?

Fotoğraf: her koyuna numara, toplam sayı.
Video:    takip ile sürüden geçen/görünen farklı koyun sayısı + tek karede en çok görülen sayı.
Yüklenenler `yuklenen/` altında kalır; eğitim verisi olarak tekrar kullanılır.
"""
from pathlib import Path

import cv2
from ultralytics import YOLO

KOYUN_COCO = 18


def _ciz(img, kutular, etiketler, renk=(60, 200, 60)):
    for (x1, y1, x2, y2), et in zip(kutular, etiketler):
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        cv2.rectangle(img, (x1, y1), (x2, y2), renk, 2)
        (tw, th), _ = cv2.getTextSize(et, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.rectangle(img, (x1, y1 - th - 8), (x1 + tw + 8, y1), renk, -1)
        cv2.putText(img, et, (x1 + 4, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)


def _kucult(img, en=1280):
    h, w = img.shape[:2]
    return img if w <= en else cv2.resize(img, (en, int(h * en / w)))


def say_foto(model_yolu, yol, cikti, guven=0.25):
    model = YOLO(model_yolu)
    siniflar = None if len(model.names) == 1 else [KOYUN_COCO]
    img = cv2.imread(str(yol))
    if img is None:
        raise ValueError("fotoğraf okunamadı")
    r = model.predict(img, imgsz=1280, conf=guven, classes=siniflar, verbose=False)[0]
    kutular = r.boxes.xyxy.tolist()
    _ciz(img, kutular, [str(i + 1) for i in range(len(kutular))])
    cv2.putText(img, f"{len(kutular)} KOYUN", (14, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 6)
    cv2.putText(img, f"{len(kutular)} KOYUN", (14, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 255, 255), 3)
    cv2.imwrite(str(cikti), _kucult(img), [cv2.IMWRITE_JPEG_QUALITY, 82])
    return {"tur": "foto", "sayi": len(kutular)}


def say_video(model_yolu, yol, cikti, guven=0.25, en_az_kare=5):
    """Videodaki farklı koyunları takip no'larıyla sayar. Hareketsiz sürüde tek karedeki en çok sayı
    daha güvenilirdir; ikisini de döndürür."""
    model = YOLO(model_yolu)
    siniflar = None if len(model.names) == 1 else [KOYUN_COCO]
    gorulme, en_cok, en_cok_kare, ilk_kare, kare_no = {}, 0, None, None, 0
    for r in model.track(source=str(yol), stream=True, persist=False, tracker="bytetrack.yaml",
                         classes=siniflar, conf=guven, imgsz=960, verbose=False):
        kare_no += 1
        n = len(r.boxes)
        if ilk_kare is None:
            ilk_kare = r.orig_img.copy()
        if r.boxes.id is not None:
            for tid in r.boxes.id.int().tolist():
                gorulme[tid] = gorulme.get(tid, 0) + 1
        if n > en_cok:
            en_cok = n
            img = r.orig_img.copy()
            ids = r.boxes.id.int().tolist() if r.boxes.id is not None else [None] * n
            _ciz(img, r.boxes.xyxy.tolist(), [f"#{t}" if t is not None else "" for t in ids])
            en_cok_kare = img
    takip = sum(1 for g in gorulme.values() if g >= en_az_kare)
    if en_cok_kare is None:  # hiç koyun yok → 0 ve ilk kare
        if ilk_kare is None:
            raise ValueError("video okunamadı")
        en_cok_kare = ilk_kare
    cv2.putText(en_cok_kare, f"TEK KAREDE EN COK {en_cok} / TAKIPLE {takip}", (14, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 6)
    cv2.putText(en_cok_kare, f"TEK KAREDE EN COK {en_cok} / TAKIPLE {takip}", (14, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3)
    cv2.imwrite(str(cikti), _kucult(en_cok_kare), [cv2.IMWRITE_JPEG_QUALITY, 82])
    return {"tur": "video", "sayi": max(en_cok, takip), "en_cok_karede": en_cok, "takiple": takip, "kare": kare_no}


def say(model_yolu, yol, cikti):
    yol = Path(yol)
    if yol.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp"):
        return say_foto(model_yolu, yol, cikti)
    return say_video(model_yolu, yol, cikti)
