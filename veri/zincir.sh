#!/bin/zsh
# Zincir: etiketleme → birleşik eğitim → sayım testi (kaldığı yerden). GPU'da hep tek ağır iş.
cd "$(dirname "$0")/.."
rm -rf veri/egitim-kopek/set
caffeinate -dimsu .venv/bin/python -I veri/hazirla_kopek.py veri/egitim-kopek/kaynak veri/egitim-kopek/set 1 > veri/egitim-kopek/hazirla.log 2>&1
echo "ETIKETLEME_BITTI $(date +%H:%M)" >> veri/zincir.log
./veri/egit_birlesik.sh >> veri/zincir.log 2>&1
while pgrep -f "[b]irlesik-y26" >/dev/null || ! grep -q "EGITIM_BITTI\|Error\|Traceback" egitimler/birlesik-y26.log 2>/dev/null; do sleep 60; done
echo "EGITIM_BITTI $(date +%H:%M)" >> veri/zincir.log
caffeinate -dimsu .venv/bin/python -I veri/say_toplu.py veri/icaerus/set12/secilen veri/sayim-set12 0 1 >> veri/sayim-set12/log-0.txt 2>&1
echo "SAYIM_BITTI $(date +%H:%M)" >> veri/zincir.log
