"""Arka planda sayım yapan motor: kaynak (video/kamera) → YOLO takip → çizgi sayımı → son kare (JPEG)."""
import threading
import time

import cv2
from ultralytics import YOLO

from cizgi import CizgiSayaci

KOYUN = 18  # COCO: sheep


class Motor:
    def __init__(self, model_yolu):
        self.model_yolu = model_yolu
        self.model = None
        self.kilit = threading.Lock()
        self.is_parcacigi = None
        self.dur_bayragi = False
        self.jpeg = None
        self.durum = "bekliyor"   # bekliyor | calisiyor | bitti | hata
        self.hata = ""
        self.kaynak = None
        self.cizgi = (0.5, 0.0, 0.5, 1.0)
        self.yon_ters = False
        self.guven = 0.25
        self.sayac = None
        self.kare_boyut = None
        self.fps = 0.0
        self.kutu = 0
        self.bitince = None       # bitince çağrılacak fonksiyon(sonuc)

    # --- dışarıdan kontrol ---
    def baslat(self, kaynak, gercek_hiz=True, bitince=None):
        self.bitince = None  # yarıda kesilen önceki sayım kaydedilmez
        self.durdur()
        self.kaynak, self.gercek_hiz, self.bitince = kaynak, gercek_hiz, bitince
        self.sayac, self.jpeg, self.hata = None, None, ""
        self.dur_bayragi = False
        self.durum = "calisiyor"
        self.is_parcacigi = threading.Thread(target=self._calis, daemon=True)
        self.is_parcacigi.start()

    def durdur(self):
        self.dur_bayragi = True
        if self.is_parcacigi and self.is_parcacigi.is_alive():
            self.is_parcacigi.join(timeout=5)

    def cizgi_ayarla(self, cizgi=None, yon_ters=None):
        if cizgi is not None:
            self.cizgi = tuple(float(v) for v in cizgi)
        if yon_ters is not None:
            self.yon_ters = bool(yon_ters)
        if self.sayac and self.kare_boyut:
            w, h = self.kare_boyut
            x1, y1, x2, y2 = self.cizgi
            self.sayac.a, self.sayac.b = (x1 * w, y1 * h), (x2 * w, y2 * h)
            self.sayac.yon_ters = self.yon_ters

    def ozet(self):
        s = self.sayac
        return {"durum": self.durum, "hata": self.hata, "kaynak": self.kaynak,
                "cikan": s.cikan if s else 0, "giren": s.giren if s else 0,
                "kutu": self.kutu, "fps": round(self.fps, 1),
                "cizgi": self.cizgi, "yon_ters": self.yon_ters}

    # --- iş parçacığı ---
    def _calis(self):
        try:
            if self.model is None:
                self.model = YOLO(self.model_yolu)
            kaynak_fps = 25.0
            if not str(self.kaynak).startswith(("rtsp", "http")):
                cap = cv2.VideoCapture(str(self.kaynak))
                kaynak_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                cap.release()
            akis = self.model.track(source=self.kaynak, stream=True, persist=False,
                                    tracker="bytetrack.yaml", classes=[KOYUN],
                                    conf=self.guven, imgsz=960, verbose=False)
            t_onceki = time.time()
            for r in akis:
                if self.dur_bayragi:
                    break
                h, w = r.orig_shape
                if self.sayac is None:
                    self.kare_boyut = (w, h)
                    self.sayac = CizgiSayaci((0, 0), (0, 0))
                    self.cizgi_ayarla()
                b = r.boxes
                self.kutu = len(b)
                if b.id is not None:
                    for (x1, y1, x2, y2), tid in zip(b.xyxy.tolist(), b.id.int().tolist()):
                        self.sayac.guncelle(tid, ((x1 + x2) / 2, (y1 + y2) / 2))
                img = r.plot(line_width=2, font_size=0.5, labels=False, conf=False)
                a, bb = self.sayac.a, self.sayac.b
                cv2.line(img, (int(a[0]), int(a[1])), (int(bb[0]), int(bb[1])), (40, 40, 255), 4)
                ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 75])
                if ok:
                    self.jpeg = buf.tobytes()
                simdi = time.time()
                gecen = simdi - t_onceki
                if self.gercek_hiz and gecen < 1 / kaynak_fps:
                    time.sleep(1 / kaynak_fps - gecen)
                    simdi = time.time()
                    gecen = simdi - t_onceki
                self.fps = 0.9 * self.fps + 0.1 * (1 / gecen if gecen else 0)
                t_onceki = simdi
            self.durum = "bitti"
        except Exception as e:  # kamera kopması vb.
            self.durum, self.hata = "hata", str(e)
        if self.bitince and self.sayac and not self.hata:
            self.bitince(self.ozet())
