#!/bin/zsh
# Sayım bitince etiketlemeyi başlat (GPU'yu aynı anda iki iş paylaşmasın — sırayla daha hızlı)
cd "$(dirname "$0")/.."
while pgrep -f "[s]ay_toplu.py" >/dev/null; do sleep 30; done
rm -rf veri/egitim-kopek/set
nohup caffeinate -dimsu .venv/bin/python -I veri/hazirla_kopek.py veri/egitim-kopek/kaynak veri/egitim-kopek/set 1 > veri/egitim-kopek/hazirla.log 2>&1 &
