"""Arka planda sayım yapan motor: kaynak (video/kamera) → YOLO takip → çizgi sayımı → son kare (JPEG).

Kamera akışı koparsa sayımı kaybetmeden yeniden bağlanır. İstenirse işaretli görüntüyü
saatlik video dosyalarına kaydeder (sonradan kontrol için).
"""
import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
from ultralytics import YOLO

from cizgi import CizgiSayaci

KOYUN_COCO = 18


class Motor:
    def __init__(self, model_yolu):
        self.model_yolu = model_yolu
        self.is_parcacigi = None
        self.dur_bayragi = False
        self.jpeg = None
        self.durum = "bekliyor"   # bekliyor | calisiyor | baglaniyor | bitti | hata
        self.hata = ""
        self.kaynak = None
        self.cizgi = (0.5, 0.0, 0.5, 1.0)
        self.yon_ters = False
        self.guven = 0.25
        self.boyut = 960
        self.sayac = None
        self.kare_boyut = None
        self.fps = 0.0
        self.kutu = 0
        self.supheli = []
        self.bitince = None
        self.log = print          # app bunu defter.sistem_log'a bağlar
        self.kayit_klasoru = None
        self._yazici = None
        self._yazici_saat = None

    # --- dışarıdan kontrol ---
    def baslat(self, kaynak, gercek_hiz=True, bitince=None, kayit_klasoru=None):
        self.bitince = None  # yarıda kesilen önceki sayım kaydedilmez
        self.durdur()
        self.kaynak, self.gercek_hiz, self.bitince = kaynak, gercek_hiz, bitince
        self.kayit_klasoru = Path(kayit_klasoru) if kayit_klasoru else None
        self.sayac, self.jpeg, self.hata, self.kare_boyut = None, None, "", None
        self.dur_bayragi = False
        self.durum = "calisiyor"
        self.is_parcacigi = threading.Thread(target=self._calis, daemon=True)
        self.is_parcacigi.start()

    def durdur(self):
        self.dur_bayragi = True
        if self.is_parcacigi and self.is_parcacigi.is_alive():
            self.is_parcacigi.join(timeout=10)

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
                "kutu": self.kutu, "fps": round(self.fps, 1), "supheli": len(self.supheli),
                "izlenen": len(s.gorulme) if s else 0,
                "cizgi": self.cizgi, "yon_ters": self.yon_ters}

    # --- iş parçacığı ---
    def _canli_mi(self):
        return str(self.kaynak).startswith(("rtsp", "http"))

    def _kaydet(self, img):
        if not self.kayit_klasoru:
            return
        saat = datetime.now().strftime("%Y-%m-%d_%H")
        if self._yazici is None or saat != self._yazici_saat:
            if self._yazici:
                self._yazici.release()
            self.kayit_klasoru.mkdir(parents=True, exist_ok=True)
            h, w = img.shape[:2]
            olcek = min(1.0, 960 / w)
            self._kayit_boyut = (int(w * olcek), int(h * olcek))
            self._yazici = cv2.VideoWriter(str(self.kayit_klasoru / f"{saat}.mp4"),
                                           cv2.VideoWriter_fourcc(*"avc1"), 10, self._kayit_boyut)
            self._yazici_saat = saat
            self._son_kayit = 0.0
        simdi = time.time()
        if simdi - self._son_kayit >= 0.1:  # 10 kare/sn yeter
            self._yazici.write(cv2.resize(img, self._kayit_boyut))
            self._son_kayit = simdi

    def _bir_tur(self, model, siniflar, tur):
        kaynak_fps = 25.0
        if not self._canli_mi():
            cap = cv2.VideoCapture(str(self.kaynak))
            kaynak_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            cap.release()
        akis = model.track(source=self.kaynak, stream=True, persist=False, tracker="bytetrack.yaml",
                           classes=siniflar, conf=self.guven, imgsz=self.boyut, verbose=False)
        t_onceki = time.time()
        for r in akis:
            if self.dur_bayragi:
                return
            if self.durum != "calisiyor":
                self.durum = "calisiyor"
                if self._canli_mi():
                    self.log("KAMERA bağlandı, sayım sürüyor")
                    self.hata = ""
            h, w = r.orig_shape
            if self.sayac is None:
                self.kare_boyut = (w, h)
                self.sayac = CizgiSayaci((0, 0), (0, 0))
                self.cizgi_ayarla()
            b = r.boxes
            self.kutu = len(b)
            img = r.orig_img.copy()
            aktif = set()
            if b.id is not None:
                for (x1, y1, x2, y2), tid in zip(b.xyxy.tolist(), b.id.int().tolist()):
                    # yeniden bağlanınca takip no'ları sıfırlanır → tur ile ayır
                    anahtar = (tur, tid)
                    aktif.add(anahtar)
                    self.sayac.guncelle(anahtar, ((x1 + x2) / 2, (y1 + y2) / 2))
                    sayildi = self.sayac.sayildi_mi(anahtar)
                    renk = (60, 200, 60) if sayildi else (0, 200, 255)  # yeşil sayıldı, sarı bekliyor
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    cv2.rectangle(img, (x1, y1), (x2, y2), renk, 2)
                    et = f"#{tid}" + (" OK" if sayildi else "")
                    (tw, th), _ = cv2.getTextSize(et, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(img, (x1, y1 - th - 8), (x1 + tw + 8, y1), renk, -1)
                    cv2.putText(img, et, (x1 + 4, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            self.supheli = self.sayac.supheli(aktif)
            a, bb = self.sayac.a, self.sayac.b
            cv2.line(img, (int(a[0]), int(a[1])), (int(bb[0]), int(bb[1])), (40, 40, 255), 4)
            ust = f"{datetime.now():%H:%M:%S}  CIKAN {self.sayac.cikan}  GIREN {self.sayac.giren}"
            if self.supheli:
                ust += f"  SUPHELI {len(self.supheli)}"
            cv2.rectangle(img, (0, 0), (12 + 15 * len(ust), 46), (0, 0, 0), -1)
            cv2.putText(img, ust, (8, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                        (80, 80, 255) if self.supheli else (255, 255, 255), 2)
            ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ok:
                self.jpeg = buf.tobytes()
            self._kaydet(img)
            simdi = time.time()
            gecen = simdi - t_onceki
            if self.gercek_hiz and gecen < 1 / kaynak_fps:
                time.sleep(1 / kaynak_fps - gecen)
                simdi = time.time()
                gecen = simdi - t_onceki
            self.fps = 0.9 * self.fps + 0.1 * (1 / gecen if gecen else 0)
            t_onceki = simdi

    def _calis(self):
        tur = 0
        try:
            model = YOLO(self.model_yolu)
            siniflar = None if len(model.names) == 1 else [KOYUN_COCO]
            if self._canli_mi():
                self.log(f"KAMERA bağlanılıyor: {self.kaynak}")
            while not self.dur_bayragi:
                try:
                    self._bir_tur(model, siniflar, tur)
                except Exception as e:
                    if not self._canli_mi():
                        raise
                    self.hata = f"kamera bağlantısı koptu: {e}"
                if self.dur_bayragi or not self._canli_mi():
                    break
                # canlı kamera bitti/koptu → bekle ve yeniden bağlan, sayım korunur
                self.log("KAMERA koptu, 5 sn sonra yeniden bağlanılacak" + (f" ({self.hata})" if self.hata else ""))
                self.durum = "baglaniyor"
                tur += 1
                model = YOLO(self.model_yolu)
                for _ in range(10):
                    if self.dur_bayragi:
                        break
                    time.sleep(0.5)
            self.durum = "bitti"
        except Exception as e:
            self.durum, self.hata = "hata", str(e)
        if self._yazici:
            self._yazici.release()
            self._yazici = None
        if self.bitince and self.sayac and self.durum != "hata":
            self.bitince(self.ozet())
