#!/bin/zsh
# Dağıtım paketi: Masaüstü/KoyunSayaci-<tarih>.zip (kod + model + kısa demolar + kurulum). Veri/venv/eğitim yok.
set -e
cd "$(dirname "$0")"
AD="KoyunSayaci-$(date +%Y%m%d)"
P="/tmp/$AD"; rm -rf "$P"; mkdir -p "$P/modeller" "$P/test-video" "$P/takip" "$P/arayuz" "$P/kayitlar"
cp app.py motor.py cizgi.py defter.py bildir.py fotosay.py siniflar.py say.py test_bildir.py README.md LICENSE KURULUM.md SONUCLAR.md kur.bat baslat.vbs kur.command "$P/"
cp arayuz/index.html "$P/arayuz/"; cp takip/*.yaml "$P/takip/"
cp modeller/koyun-tepeden.pt modeller/koyun-birlesik.pt "$P/modeller/"
# küçük demolar (gerçek sayısı bilinen 2 video + kapı üstü 1)
for v in tepeden-agila-giris-12.mp4 tepeden-agila-giris-13.mp4 kapi-ustu-giris-3.mp4; do cp "test-video/$v" "$P/test-video/"; done
python3 - "$P/test-video" <<'EOF'
import json,sys,os
d=json.load(open("test-video/demolar.json")); out=sys.argv[1]
json.dump({k:v for k,v in d.items() if os.path.exists(f"{out}/{k}")}, open(f"{out}/demolar.json","w"), ensure_ascii=False, indent=1)
EOF
chmod +x "$P/kur.command"
cd /tmp && rm -f ~/Desktop/"$AD.zip" && zip -qr ~/Desktop/"$AD.zip" "$AD" && rm -rf "$P"
ls -la ~/Desktop/"$AD.zip" | awk '{print $5/1e6 " MB", $9}'
