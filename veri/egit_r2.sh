#!/bin/zsh
# 2. tur: karışık modeli (koyun-birlesik.pt) aynı birleşik sette, mozaiksiz ve düşük öğrenme hızıyla 20 tur daha ince ayarla
# (hedef: beyazda 160/160'a dönmek, keçi/köpek kazanımını korumak). Bitince 4 gt video + keçi/köpek sınavını kendi koşar → veri/r2-rapor.txt
cd "$(dirname "$0")/.."
.venv/bin/python -I - > egitimler/birlesik-r2.log 2>&1 <<'PY'
from ultralytics import YOLO
m = YOLO("modeller/koyun-birlesik.pt")
m.train(data="veri/egitim-birlesik/veri.yaml", epochs=20, imgsz=960, batch=16, device="mps",
        project="runs/detect/egitimler", name="birlesik-r2", exist_ok=True, patience=8, close_mosaic=20,
        lr0=0.002, lrf=0.05, warmup_epochs=1, degrees=180, flipud=0.5, fliplr=0.5, scale=0.3, hsv_v=0.3, workers=8, plots=True)
print("EGITIM_BITTI")
PY
cp runs/detect/egitimler/birlesik-r2/weights/best.pt modeller/koyun-birlesik-r2.pt
{
  echo "== 2. tur sınavı $(date '+%d %b %H:%M') =="
  echo "-- 4 bilinen video (160) --"; .venv/bin/python olc.py --model modeller/koyun-birlesik-r2.pt 2>&1 | grep -E "^video|TOPLAM"
  echo "-- kapı üstü / keçi / köpek --"; .venv/bin/python kiyas.py modeller/koyun-birlesik-r2.pt 2>&1 | grep -E "mp4"
  echo "-- val sınıf bazlı --"; tail -c 3000 egitimler/birlesik-r2.log | tr '\r' '\n' | grep -E "^\s+(all|koyun|kopek|insan)\s+[0-9]" | tail -4
  echo "R2_BITTI"
} > veri/r2-rapor.txt 2>&1
