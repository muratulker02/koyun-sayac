# 🐑 Koyun Sayacı

Ahır kapısının üstüne asılan bir kamerayla sabah çıkan ve akşam giren koyunları sayar; eksik varsa
Telegram'dan haber verir. Ayrıca telefondan ya da drone'dan çekilmiş bir fotoğraf/videoda kaç koyun
olduğunu sayar.

Tamamen yerel çalışır (bulut yok, abonelik yok). Windows ve Mac.

## Ne yapar

- **Kapı sayımı:** kamera gün boyu açık; kırmızı çizgiyi geçen her hayvan yönüne göre *çıkış* ya da
  *giriş* sayılır. Ekranda "Bugün çıkan / Bugün giren / Şu an dışarıda" anlık görünür.
- **Her koyuna numara:** yakalanan hayvan sarı kutu + numara alır, çizgiyi geçince yeşil "OK" olur.
  Çizgiyi geçmeden gözden kaybolan hayvan **şüpheli** diye uyarılır — kaçırma gizli kalmaz.
- **Akşam raporu:** ayarladığınız saatte (örn. 19:30) Telegram'a "700 çıktı, 698 girdi — ⚠️ 2 eksik"
  gibi rapor gider; son hayvan girdiğinde "hepsi içeride" mesajı gelir.
- **Kayıt:** günlük JSON, `kayitlar/gecisler.csv` (Excel'de açılır), sistem günlüğü, saatlik video.
- **Fotoğraf / video ile say:** bir dosya bırakın → kaç koyun var, her biri numaralı görselle.
- **Demo testler:** gerçek sayısı bilinen videolarla doğruluğu kendiniz ölçün.

## Kurulum

Paketi (`KoyunSayaci-*.zip`) açın:

- **Windows:** `kur.bat` çift tık → masaüstüne "Koyun Sayacı" kısayolu gelir. NVIDIA ekran kartı
  varsa otomatik CUDA kurulur.
- **Mac:** `kur.command` çift tık.

Kaynak koddan: Python 3.12 + `uv` ile `uv venv --python 3.12 .venv && uv pip install --python
.venv/bin/python torch torchvision ultralytics lap pyyaml requests flask`, sonra `python app.py` →
http://127.0.0.1:8780 . Model dosyası `modeller/koyun-tepeden.pt` paketten alınır (depoda yok).

Ayrıntı: [KURULUM.md](KURULUM.md). Eğitim ve doğruluk sonuçları: [SONUCLAR.md](SONUCLAR.md).

## Kamera

Kapının **tam üstüne**, 4–5 m yükseklik, dik aşağı bakacak; kapı 1–2 hayvan geçecek genişliğe
daraltılırsa sayım en sağlıklı olur. 4 MP, 4 mm lens bir IP kamera (RTSP) yeterli; gece için
yandan LED projektör. Bilgisayarda NVIDIA RTX 3050 ve üstü idealdir; CPU'da da çalışır, yavaş.

## Model

YOLO26s, tepeden koyun görüntüleriyle ince ayarlı (ICAERUS açık veri setleri, 1.305 görüntü,
18 bin işaretli koyun). Gerçek sayısı bilinen 4 kapı videosunda 160/160. Kendi ahırınızın ilk
günlerinin görüntüsüyle bir tur daha eğitmek doğruluğu sizin kapınıza da taşır (`veri/` betikleri).

## Dosyalar

| Dosya | İş |
|---|---|
| `app.py` | arayüz ve sunucu (Flask, :8780) |
| `motor.py` | kamera/video → YOLO takip → çizgi sayımı → ekran görüntüsü |
| `cizgi.py` | çizgi geçişi mantığı (+ `test_cizgi.py`) |
| `defter.py` | günlük kayıt, CSV, sistem günlüğü |
| `bildir.py` | Telegram (+ `test_bildir.py`) |
| `fotosay.py` | fotoğraf/video yükleyip sayma |
| `say.py`, `olc.py`, `kiyas.py` | komut satırından sayma ve doğruluk ölçme |
| `veri/` | eğitim verisi hazırlama betikleri |
| `kur.bat`, `kur.command`, `paketle.sh` | kurulum ve paket |

## Lisans

Kod: MIT. Eğitim verisi ICAERUS (CC BY 4.0) — https://icaerus.eu

## Telefon / tablet

Arayüz telefon ve tablet ekranına uyar. Başka cihazdan açmak için bilgisayarda **Ayarlar → Telefon / tabletten erişim**
kutusunu işaretleyin, **kullanıcı adı ve şifre** belirleyin (ağdan gelen bağlantılara şifre zorunludur), programı yeniden
başlatın; ekranda görünen `http://<bilgisayar-ip>:8780` adresini aynı Wi-Fi'daki telefonda açın. "📸 Telefon kamerasıyla
çek ve say" düğmesi doğrudan kamerayı açar. Ana ekrana eklenirse uygulama gibi açılır.
