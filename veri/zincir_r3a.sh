#!/bin/zsh
# 3a turu (Mac): ELİMİZDEKİ TÜM videolar (set1 17 + set12 97 tepeden; yandan/mera/uzak drone YOLO-World ile) → sözde etiket → birleştir → eğitim → sınav (indirme yok)
# Başlat:  nohup caffeinate -dimsu veri/zincir_r3.sh > egitimler/r3-zincir.log 2>&1 &
cd "$(dirname "$0")/.."
PY=.venv/bin/python; OK=veri/r3a-adim
yaz(){ echo "$(date '+%Y-%m-%d %H:%M:%S')  $*"; }
adim(){ local ad=$1; shift; if [ -f $OK/$ad.ok ]; then yaz "[$ad] zaten bitti"; return 0; fi; yaz "[$ad] başlıyor"; "$@" || { yaz "[$ad] HATA"; exit 1; }; touch $OK/$ad.ok; yaz "[$ad] bitti"; }

indir(){
  cd veri/icaerus
  URL=$(curl -s -m 30 "https://zenodo.org/api/records/14967219" | python3 -c "import json,sys; print(json.load(sys.stdin)['files'][0]['links']['self'])")
  aria2c -c -x16 -s16 -k4M --max-tries=0 --retry-wait=10 --file-allocation=none --summary-interval=300 --console-log-level=warn -d set-cesitli -o "Sheep dataset.zip" "$URL"
  local r=$?; cd ../..; return $r
}
ac(){ mkdir -p veri/icaerus/set-cesitli/icerik && ditto -x -k "veri/icaerus/set-cesitli/Sheep dataset.zip" veri/icaerus/set-cesitli/icerik && rm "veri/icaerus/set-cesitli/Sheep dataset.zip"; }
etiket(){ $PY veri/sozde_etiket.py veri/egitim-r3/kaynak-tepeden veri/egitim-r3/set --video-basi 60 --atla veri/egitim-kopek/set/images --koyun-kaynak model \
          && $PY veri/sozde_etiket.py veri/egitim-r3/kaynak-yandan veri/egitim-r3/set --video-basi 80 --koyun-kaynak world --esik 0.35; }
birlestir(){ $PY veri/hazirla_birlesik.py; }
egit(){ $PY veri/egit.py --veri veri/egitim-birlesik/veri.yaml --temel modeller/koyun-birlesik.pt --ad birlesik-r3a --tur 30 --batch 16 && [ -f modeller/birlesik-r3a.pt ]; }
sinav(){
  { echo "== 3. tur sınavı $(date '+%d %b %H:%M') =="
    echo "-- 4 bilinen video (160): eski karışık model --"; $PY olc.py --model modeller/koyun-birlesik.pt 2>&1 | grep -E "^video|TOPLAM"
    echo "-- 4 bilinen video (160): YENİ r3 --"; $PY olc.py --model modeller/birlesik-r3a.pt 2>&1 | grep -E "^video|TOPLAM"
    echo "-- demolar (47 olmalı; keçi 83-84): YENİ r3 --"
    for v in kapi-ustu-giris-3 kapi-ustu-giris-4 kapi-ustu-giris-11 kopekli-suru-tepeden tepeden-agila-giris-8 kalabalik-suru-92; do
      echo "$v  $($PY say.py test-video/$v.mp4 --model modeller/birlesik-r3a.pt --siniflar 0 --boyut 960 --cizgi 0,0.5,1,0.5 2>/dev/null | tail -1)"; done
    echo "-- val sınıf bazlı --"; grep -E "^\s+(all|koyun|kopek|insan)\s+[0-9]" egitimler/birlesik-r3a/results.csv 2>/dev/null | tail -4
    echo "R3_BITTI"; } > veri/r3a-rapor.txt 2>&1; cat veri/r3a-rapor.txt
}


adim etiket etiket
adim birlestir birlestir
adim egit egit
adim sinav sinav
yaz "ZINCIR_BITTI — rapor veri/r3a-rapor.txt, model modeller/birlesik-r3a.pt"
