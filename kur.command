#!/bin/zsh
# Koyun Sayacı — Mac kurulumu (çift tıkla). İnternet gerekir, 5–10 dk sürer.
cd "$(dirname "$0")"
echo "=== KOYUN SAYACI — Mac kurulumu ==="
if ! command -v uv >/dev/null; then
  echo "[1/3] uv indiriliyor..."; curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH"
else echo "[1/3] uv kurulu."; fi
echo "[2/3] Python ortamı..."; uv venv --python 3.12 .venv -q || { echo "HATA"; read; exit 1; }
echo "[3/3] Kütüphaneler..."; UV_HTTP_TIMEOUT=300 uv pip install --python .venv/bin/python -q ultralytics lap pyyaml requests flask || { echo "HATA"; read; exit 1; }
cat > ~/Desktop/"Koyun Sayacı.command" <<EOF
#!/bin/zsh
cd "$(pwd)"
curl -s -o /dev/null 127.0.0.1:8780/api/durum || { nohup .venv/bin/python app.py > sunucu.log 2>&1 & sleep 5; }
open http://127.0.0.1:8780/
EOF
chmod +x ~/Desktop/"Koyun Sayacı.command"
echo; echo "KURULUM TAMAM. Masaüstündeki 'Koyun Sayacı' simgesine çift tıklayın."; read -k1 "?Kapatmak için bir tuşa basın."
