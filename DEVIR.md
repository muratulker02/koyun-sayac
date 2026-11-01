# DEVİR — Koyun Sayacı (1 Kasım 2026)

Bu dosya işi başka bir makineye/kişiye devretmek için yazıldı. Ayrıntılı sonuçlar `SONUCLAR.md`,
kullanım `README.md` içinde.

## 1. Ne var, nerede

| Parça | Yer | Durum |
|---|---|---|
| Kod | GitHub `muratulker02/koyun-sayac` (özel) | güncel |
| Modeller (repoda tutulmaz) | GitHub Release **v1.0** → `koyun-tepeden.pt`, `koyun-birlesik.pt`, `yolov8s-worldv2.pt` | indirip `modeller/` içine koy |
| Tak-çalıştır paket | Release v1.0 → `KoyunSayaci-20261101.zip` (166 MB) | Mac: `baslat.command`, Windows: `kur.bat` |
| Eğitim seti (9,1 GB, 2.873 train / 736 val, 3 sınıf) | Mac `veri/egitim-birlesik` → devir için `devir/egitim-birlesik.tar` | ofis PC'ye kopyalanıyor |
| Demo videoları (11 adet, 460 MB) | Mac `test-video/` → `devir/test-video.tar` | ofis PC'ye kopyalanıyor |
| Ham ICAERUS verisi | Zenodo (CC-BY); `veri/indir.ps1` indirir | set2 + keçi + 22 GB çeşitli set |

Modeller:
- **koyun-tepeden.pt** (varsayılan): beyaz/açık sürü. 4 bilinen video 160/160; tam videolar 47/47.
- **koyun-birlesik.pt** (r2): koyun+keçi / köpek / insan. 159/160; keçi 84 (elle 83); köpeği saymaz.

## 2. Ofis PC'de 3. tur eğitim (RTX 5060 Ti 16 GB, C:'de 52 GB boş)

Tek betik: `devir/pc-zincir.ps1`. Adımları sırayla yapar, her biten adım için `.<adım>.ok` bırakır;
yarıda kesilirse aynı komutla kaldığı yerden sürer. Kök: `C:\Users\pamus\KoyunSayaci-egitim`, günlük `zincir.log`.

```
powershell -ExecutionPolicy Bypass -File C:\Users\pamus\pc-zincir.ps1
```

| Adım | Ne yapar | Süre (tahmin) |
|---|---|---|
| repo | repo + 3 model dosyasını Mac'teki devir sunucusundan alır (md5 doğrular) | 1 dk |
| kurulum | uv → Python 3.12 → torch cu128 + ultralytics (kısayol/başlangıç OLUŞTURMAZ) | 1–10 dk |
| egitim-seti | 9,8 GB tar'ı indirir, `veri/egitim-birlesik` olarak açar, yaml yolunu düzeltir | ağa bağlı |
| demo-videolar | `test-video/` | 1 dk |
| veri-indir | `veri/indir.ps1`: set2 (160 MB, sınav), keçi (180 MB), **set-cesitli 22 GB** (etiketsiz) | ofis hattına bağlı |
| sozde-etiket | `veri/sozde_etiket.py`: 22 GB setin video/fotolarından sözde etiket (koyun: karışık model; köpek/insan: YOLO-World) → `veri/egitim-r3/set` | 1–2 sa |
| birlestir | `veri/hazirla_birlesik.py`: mevcut sete r3'ü ekler | 1 dk |
| egitim | `veri/egit.py --temel koyun-birlesik.pt --ad birlesik-r3 --tur 30` → `modeller/birlesik-r3.pt` | 1–3 sa |
| sinav | `olc.py` (160 sınavı) eski ve yeni model; demolarda `say.py` → `r3-rapor.txt` | 10 dk |

Kabul ölçütü (yeni model pakete girer mi?): 4 bilinen video **160/160**, demolar 47/47, keçi 83–84,
köpek sayılmıyor. Birini kaybediyorsa eski model kalır.

Mac'teki devir sunucusu: `cd devir && python3 -m http.server 8790 --bind <Tailscale IP>` (dosyalar: repo tar,
egitim-birlesik.tar, test-video.tar, modeller/). Ofis PC yalnız Tailscale üzerinden ulaşır.

### Kaldığı yer (1 Kas 23:45) — Murat: ofis PC kolu İPTAL, her şey Mac'te
Ofis PC'deki süreçler durduruldu, yarım indirmeler silindi; `C:\Users\pamus\KoyunSayaci-egitim` (4,6 GB: repo + ortam) duruyor, istenirse silinir.
Mac: `veri/zincir_r3a.sh` tüm yerel veriyle (114 video + yandan + COCO 1.594 foto) 30 tur eğitiyor; `veri/icaerus/gece-indir.sh` 01:00'da
kalan ICAERUS setlerini (4,8 + 22 + 29 GB) indirir → sabah son tur.

### Önceki not (1 Kas 20:00)
repo + kurulum bitti; 9,8 GB eğitim seti aktarımı ofisten ~1 MB/s gidiyordu, Murat "evde internet hızlı, orada
yapacağız" dedi → durduruldu (PC'deki yarım tar sıfırlandı, baştan iner). **Evden sürdürmek:** Mac'te
`devir/evden-baslat.sh` (sunucuyu açar + SSH'ta zinciri kaldığı adımdan çalıştırır). Not: Mac'in Tailscale IP'si evde
değişirse betik yeni IP'yi otomatik verir.

## 3. Elle çalıştırmak istersen (herhangi bir makine)

```
# ortam
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python torch torchvision ultralytics lap pyyaml requests flask
# veri
python veri/sozde_etiket.py <video klasörü> veri/egitim-r3/set --video-basi 60
python veri/hazirla_birlesik.py            # mevcut egitim-birlesik'e ekler; sıfırdan: --yeniden
# eğitim (cuda/mps/cpu otomatik)
python veri/egit.py --veri veri/egitim-birlesik/veri.yaml --temel modeller/koyun-birlesik.pt --ad birlesik-r3 --tur 30
# sınav
python olc.py --model modeller/birlesik-r3.pt          # 4 bilinen video, 160 olmalı
python say.py test-video/kapi-ustu-giris-3.mp4 --model modeller/birlesik-r3.pt --siniflar 0 --boyut 960 --cizgi 0,0.5,1,0.5
```

## 4. Bilinen tuzaklar

- MPS'te (Mac) aynı anda 2'den fazla YOLO süreci → 25× yavaşlama. Windows CUDA'da sorun yok.
- Ultralytics `project=` göreli yolun önüne `runs/detect/` ekleyebilir; `egit.py` her iki yerde arar.
- YOLO-World kahverengi keçiyi "person" sanır → `sozde_etiket.py` koyun kutusuyla örtüşen insanı atar.
- Model 960 px'te eğitildi; 1920 px ile saymak yanlış sonuç verir (156/83). Programın ayarını değiştirme.
- Dense sürüde elle doğrulama için yarık tarama güvenilmez (±5); sıralı geçişte iyi (keçi videosu 83).
- PowerShell 5.1 betikleri UTF-8 **BOM** ile kaydedilmeli (Türkçe karakter yoksa ayrıştırma hatası verir).
- Ofis PC'de arka plan işi SSH oturumuna bağlı: Mac'ten `caffeinate -s ssh ... pc-zincir.ps1` ile çalıştırıldı;
  kopunca aynı komutla yeniden başlat, kaldığı yerden sürer.

## 5. Senden bekleyenler (Murat)

- **Telegram**: BotFather → bot → anahtarı Ayarlar → Telegram'a yapıştır → Bağla. Kod hazır, sahte sunucuda 8/8.
- **Kamera**: ağıl kapısının üstü, dik aşağı bakış, 5–10 m. Takılınca ilk haftanın görüntüsüyle son ince ayar.
- 3. tur raporu (`r3-rapor.txt`) gelince karar: yeni model pakete girsin mi?
