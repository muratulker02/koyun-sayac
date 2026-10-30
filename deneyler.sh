#!/bin/zsh
# Takipçi/eşik ayarlarının kaçırmaya etkisi — hazır YOLO26s ile (eğitim bitince eğitilmiş modelle tekrar)
cd ~/projects/koyun-sayac
M=${1:-modeller/yolo26s.pt}
run(){ echo "## $*"; .venv/bin/python olc.py --model $M "$@" 2>&1 | grep TOPLAM; }
run --guven 0.25 --boyut 960
run --guven 0.10 --boyut 960
run --guven 0.10 --boyut 1280
run --guven 0.10 --boyut 1280 --takip botsort.yaml
run --guven 0.10 --boyut 1280 --iou 0.5
run --guven 0.15 --boyut 1280 --iou 0.5 --takip takip/koyun-bytetrack.yaml
run --guven 0.10 --boyut 1536 --iou 0.5 --takip takip/koyun-bytetrack.yaml
