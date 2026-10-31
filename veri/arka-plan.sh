#!/bin/zsh
# Sayım (tek işçi, kaldığı yerden) + etiketleme (tek işçi) — GPU paylaşımı 2 süreçle sınırlı (5 süreç 25× yavaşlattı)
cd "$(dirname "$0")/.."
nohup caffeinate -dimsu .venv/bin/python -I veri/say_toplu.py veri/icaerus/set12/secilen veri/sayim-set12 0 1 >> veri/sayim-set12/log-0.txt 2>&1 &
nohup caffeinate -dimsu .venv/bin/python -I veri/hazirla_kopek.py veri/egitim-kopek/kaynak veri/egitim-kopek/set 1 > veri/egitim-kopek/hazirla.log 2>&1 &
