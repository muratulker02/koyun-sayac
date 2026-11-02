#!/bin/zsh
# Vitrin yayın klasörü: index + sonuc.json + küçültülmüş poster + web boyutunda video → vitrin/yayin
set -e
cd "$(dirname "$0")"
mkdir -p yayin/video yayin/poster
cp index.html sonuc.json .vercelignore yayin/ 2>/dev/null || true
for v in video/*.mp4; do
  ad=$(basename "$v")
  [ -f "yayin/video/$ad" ] && [ "yayin/video/$ad" -nt "$v" ] && continue
  ffmpeg -v error -y -i "$v" -vf "scale=960:-2" -c:v libx264 -preset slow -crf 28 -maxrate 2200k -bufsize 4400k \
    -pix_fmt yuv420p -movflags +faststart -an "yayin/video/$ad"
  echo "video $ad $(du -h "yayin/video/$ad" | cut -f1)"
done
for p in poster/*.jpg; do
  ad=$(basename "$p")
  ffmpeg -v error -y -i "$p" -vf "scale=960:-2" -q:v 6 "yayin/poster/$ad"
done
echo "toplam $(du -sh yayin | cut -f1)"
echo YAYIN_HAZIR
