#!/bin/zsh
# Birleşik eğitim (koyun+keçi / köpek / insan) — mevcut koyun-tepeden.pt'den ince ayar, 3 sınıf.
# Uyku engelli; ~45-60 dk M5 Max. Çıktı: egitimler/birlesik-y26/weights/best.pt
cd "$(dirname "$0")/.."
.venv/bin/python -I veri/hazirla_birlesik.py || exit 1
nohup caffeinate -dimsu .venv/bin/python -I - > egitimler/birlesik-y26.log 2>&1 <<'EOF' &
from ultralytics import YOLO
m = YOLO("modeller/koyun-tepeden.pt")          # 1 sınıflı koyun modelinden başla; baş katmanı 3 sınıfa yeniden kurulur
m.train(data="veri/egitim-birlesik/veri.yaml", epochs=40, imgsz=960, batch=16, device="mps",
        project="egitimler", name="birlesik-y26", exist_ok=True, patience=12, close_mosaic=8,
        degrees=180, flipud=0.5, fliplr=0.5, scale=0.4, hsv_v=0.4, workers=8, plots=True)
print("EGITIM_BITTI")
EOF
echo "eğitim başladı: egitimler/birlesik-y26.log"
