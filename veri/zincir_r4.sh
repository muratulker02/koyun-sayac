#!/bin/zsh
# 4. tur (SON): r3a bitince + yeni ICAERUS setleri inince → aç → sözde etiket → birleştir → r3a'dan ince ayar → sınav.
# Başlat: nohup caffeinate -dimsu veri/zincir_r4.sh > egitimler/r4-zincir.log 2>&1 &
cd "$(dirname "$0")/.."
PY=.venv/bin/python; OK=veri/r4-adim; mkdir -p $OK veri/egitim-r4
yaz(){ echo "$(date '+%Y-%m-%d %H:%M:%S')  $*"; }
adim(){ local ad=$1; shift; if [ -f $OK/$ad.ok ]; then yaz "[$ad] zaten bitti"; return 0; fi; yaz "[$ad] başlıyor"; "$@" || { yaz "[$ad] HATA"; exit 1; }; touch $OK/$ad.ok; yaz "[$ad] bitti"; }

bekle(){  # r3a eğitimi (GPU) ve indirmeler bitsin
  until grep -q "ZINCIR_BITTI" egitimler/r3a-zincir.log 2>/dev/null; do sleep 120; done; yaz "r3a bitti"
  until grep -q "HEPSI_INDI" veri/icaerus/gece-indir.log 2>/dev/null; do sleep 120; done; yaz "indirmeler bitti"
}
ac(){
  for d in set-keci-video set-cesitli set-cesitli2; do
    for z in veri/icaerus/$d/*.zip; do
      [ -f "$z" ] || continue
      mkdir -p veri/icaerus/$d/icerik && ditto -x -k "$z" veri/icaerus/$d/icerik && rm "$z" && yaz "açıldı: $z"
    done
  done
}
etiket(){
  # yeni setlerin video+fotoları → sözde etiket (koyun/keçi: karışık model r3a; köpek/insan YOLO-World; köpek sonra ayıklanır)
  mkdir -p veri/egitim-r4/kaynak
  for d in set-keci-video set-cesitli set-cesitli2; do ln -sfn "$PWD/veri/icaerus/$d/icerik" "veri/egitim-r4/kaynak/$d"; done
  KOYUN_MODEL=modeller/birlesik-r3a.pt $PY veri/sozde_etiket.py veri/egitim-r4/kaynak veri/egitim-r4/set --video-basi 40 --koyun-kaynak model
  # otomatik köpek etiketleri güvenilmez (3a dersi): hepsini sil, köpek bilgisi elle temizlenmiş eski setten gelir
  $PY - <<'PY'
from pathlib import Path
n=0
for f in Path("veri/egitim-r4/set/labels").rglob("*.txt"):
    s=f.read_text().splitlines(); y=[l for l in s if not l.startswith("1 ")]
    if len(y)!=len(s): n+=len(s)-len(y); f.write_text("\n".join(y)+("\n" if y else ""))
print("köpek etiketi silindi:",n)
PY
}
birlestir(){ R4=1 $PY veri/hazirla_birlesik.py; }
egit(){ $PY veri/egit.py --veri veri/egitim-birlesik/veri.yaml --temel modeller/birlesik-r3a.pt --ad birlesik-r4 --tur 15 --batch 16 && [ -f modeller/birlesik-r4.pt ]; }
sinav(){
  { echo "== 4. tur sınavı $(date '+%d %b %H:%M') =="
    for m in koyun-tepeden koyun-birlesik birlesik-r3a birlesik-r4; do
      echo "-- $m: 4 bilinen video (160) --"; $PY olc.py --model modeller/$m.pt 2>&1 | grep -E "TOPLAM"
    done
    echo "-- demolar (47; keçi 83-84): r4 --"
    for v in kapi-ustu-giris-3 kapi-ustu-giris-4 kapi-ustu-giris-11 kopekli-suru-tepeden tepeden-agila-giris-8 kalabalik-suru-92; do
      echo "$v  $($PY say.py test-video/$v.mp4 --model modeller/birlesik-r4.pt --siniflar 0 --boyut 960 --cizgi 0,0.5,1,0.5 2>/dev/null | tail -1)"; done
    echo "R4_BITTI"; } > veri/r4-rapor.txt 2>&1; cat veri/r4-rapor.txt
}
adim bekle bekle
adim ac ac
adim etiket etiket
adim birlestir birlestir
adim egit egit
adim sinav sinav
yaz "ZINCIR_BITTI — rapor veri/r4-rapor.txt, model modeller/birlesik-r4.pt"
