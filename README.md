# 🐑 Koyun Sayacı

Ahır kapısının üstüne asılan bir kamerayla kapıdan geçen koyunları tek tek sayar; sabah çıkanla akşam
gireni karşılaştırır, eksik varsa Telegram'dan haber verir. Telefondan ya da drone'dan çekilmiş bir
fotoğraf/videoda kaç koyun olduğunu da sayar.

Tamamen yerel çalışır: bulut yok, abonelik yok. Windows ve Mac.

**Deneme sonuçları ve işaretli videolar:** https://koyun-sayac-vitrin.vercel.app

## Doğruluk (gerçek sürü videoları, ICAERUS açık veri seti)

| Deneme | Gerçek | Sistem |
|---|---|---|
| Kaç koyun geçtiği kesin bilinen 4 kapı videosu | 160 | **160** |
| Aynı 47'lik sürü, 5 ayrı video, 5–10 m kamera yüksekliği | 47 | **47 / 47 / 47 / 47 / 47** |
| Kahverengi keçi sürüsü (elle sayım 83 ±3), 2 insan geçiyor | ≈83 | **84**, insanlar sayılmadı |
| Sürü + beyaz çoban köpeği | 47 | **47**, köpek sayılmadı |

Ayrıntı: [SONUCLAR.md](SONUCLAR.md).

## Ne yapar

- **Kapı sayımı:** kamera gün boyu açık; kırmızı çizgiyi geçen her hayvan yönüne göre *çıkış* ya da
  *giriş* sayılır. Ekranda "Bugün çıkan / Bugün giren / Şu an dışarıda" anlık görünür.
- **Her koyuna numara:** yakalanan hayvan kutu + numara alır, çizgiyi geçince "sayıldı" olur. Çizgiyi
  geçmeden gözden kaybolan hayvan **şüpheli** diye uyarılır; kaçırma gizli kalmaz.
- **Köpek ve insan sayılmaz:** etiketlenir, sayıma girmez.
- **Akşam raporu:** ayarladığınız saatte Telegram'a "700 çıktı, 698 girdi — ⚠️ 2 eksik" gider; son
  hayvan girdiğinde "hepsi içeride" mesajı gelir.
- **Kayıt:** günlük JSON, `kayitlar/gecisler.csv` (Excel'de açılır), sistem günlüğü, saatlik video.
- **Fotoğraf / video ile say:** bir dosya bırakın → kaç koyun var, her biri numaralı görselle.
- **Telefon / tablet:** arayüz telefon ve tablete uyar; aynı Wi‑Fi'dan şifreyle erişilir.
- **Demo testler:** gerçek sayısı bilinen videolarla doğruluğu kendiniz ölçün.

## Kurulum

### A) Hazır paket (önerilen)

[Releases](../../releases) sayfasından `KoyunSayaci-*.zip` indirip açın:

- **Windows:** `kur.bat` çift tık → masaüstüne "Koyun Sayacı" kısayolu gelir. NVIDIA ekran kartı varsa
  otomatik CUDA kurulur.
- **Mac:** `kur.command` çift tık (ilk açılışta sağ tık → Aç gerekebilir).

Kurulum interneti kullanır, 5–15 dk sürer. Program sonra internetsiz de sayar; yalnız Telegram için
internet gerekir. Adım adım: [KURULUM.md](KURULUM.md).

### B) Kaynak koddan

```bash
git clone https://github.com/muratulker02/koyun-sayac.git && cd koyun-sayac
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python torch torchvision ultralytics lap pyyaml requests flask
.venv/bin/python modeller/indir.py        # 3 model dosyasını Releases'ten modeller/ içine indirir
.venv/bin/python app.py                   # http://127.0.0.1:8780
```

Windows'ta `.venv\Scripts\python.exe` kullanın. Model dosyaları (`*.pt`) depoda tutulmaz,
[Releases](../../releases) içindedir.

## Kamera ve bilgisayar

- **Kamera:** kapının **tam üstüne**, **3–6 m** yüksekliğe, dik aşağı bakacak. Alçak ahırda kirişe
  takılır, direk gerekmez. 4 MP, **2,8 mm geniş açı**, PoE, RTSP veren bir IP kamera yeterli
  (ör. Hikvision DS‑2CD1043G0‑IUF). Wi‑Fi ve yalnız buluttan çalışan kameralar uygun değil. Gece için
  kızılötesi ya da yandan LED projektör.
- **Bilgisayar:** önerilen **Mac mini M4 (16 GB)**: küçük, sessiz, az elektrik. Alternatif: NVIDIA
  RTX 3050 ve üstü ekran kartlı Windows PC. Intel N100 / Celeron mini PC ve Raspberry Pi gerçek zamanlı
  sayım için yavaş.
- **Bağlantı:** kamera → Cat6 → PoE anahtar → bilgisayar. Programın Ayarlar'ına kameranın RTSP adresi
  yazılır, sayım çizgisi fareyle kapının üstüne çekilir.
- **İlk hafta:** her ahır farklı; ilk günlerin görüntüsüyle bir tur ince ayar (`veri/` betikleri)
  doğruluğu sizin kapınıza taşır.

## Model

YOLO26s, tepeden koyun görüntüleriyle ince ayarlı. Üç model:

| Dosya | Ne için |
|---|---|
| `koyun-tepeden.pt` | kapı sayımı (varsayılan): beyaz/açık sürü, 160/160 |
| `koyun-heracidan.pt` | her açıdan: koyun + keçi, köpek/insan ayrımı, yandan ve yerden fotoğraflar (yükleme bu modeli kullanır) |
| `koyun-birlesik.pt` | önceki karışık model (karşılaştırma için) |

Eğitim verisi: ICAERUS drone ve kapı videoları (Fransa), COCO "sheep" fotoğrafları (yandan görüş).
Eğitim betikleri `veri/` altında (`egit.py` cuda/mps/cpu otomatik, `sozde_etiket.py` sözde etiket,
`hazirla_birlesik.py` set birleştirme). Sonuçlar ve yol: [SONUCLAR.md](SONUCLAR.md).

## Dosyalar

| Dosya | İş |
|---|---|
| `app.py` | arayüz ve sunucu (Flask, :8780) |
| `motor.py` | kamera/video → YOLO takip → çizgi sayımı → ekran görüntüsü |
| `cizgi.py` | çizgi geçişi mantığı (+ `test_cizgi.py`) |
| `siniflar.py` | hangi sınıf sayılır, hangisi yalnız etiketlenir |
| `defter.py` | günlük kayıt, CSV, sistem günlüğü |
| `bildir.py` | Telegram (+ `test_bildir.py`) |
| `fotosay.py` | fotoğraf/video yükleyip sayma |
| `say.py`, `olc.py`, `kiyas.py` | komut satırından sayma ve doğruluk ölçme |
| `veri/` | eğitim verisi hazırlama ve eğitim betikleri |
| `vitrin/` | deneme sonuçları sayfası (işaretli videolar, Vercel) |
| `kur.bat`, `kur.command`, `paketle.sh` | kurulum ve paket |

Testler: `.venv/bin/python -m pytest test_bildir.py test_cizgi.py`

## Veri ve lisans

- **Kod:** MIT ([LICENSE](LICENSE)).
- **Ultralytics YOLO** kütüphanesi ve başlangıç ağırlıkları **AGPL‑3.0** lisanslıdır; buradan türetilen
  `*.pt` modelleri de aynı koşullara tabidir. Kendi çiftliğinizde kullanmak serbesttir; kapalı kaynak
  ticari bir ürün içinde dağıtmak için Ultralytics'ten ticari lisans gerekir (https://www.ultralytics.com/license).
- **Eğitim ve demo görüntüleri:** ICAERUS projesi açık veri setleri, CC BY 4.0 (https://icaerus.eu, Zenodo);
  COCO 2017 (CC BY 4.0).
