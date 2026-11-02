# Koyun Sayacı — Eğitim ve Test Sonuçları (31 Ekim 2026)

## Son model: `modeller/koyun-tepeden.pt` (YOLO26s, büyük eğitim)

Eğitim verisi: 1.305 tepeden görüntü, 18.376+ işaretli koyun (ICAERUS drone seti + kapı videoları, Fransa).
Eğitim: 40 tur, M5 Max Mac. Video #3 eğitime hiç girmedi (dürüst sınav).

### Hiç görmediği 428 tepeden fotoğrafta tespit
| Hassasiyet | Yakalama | mAP50 | mAP50-95 |
|---|---|---|---|
| 0,992 | 0,989 | 0,995 | 0,904 |
(ICAERUS'un kendi "altın standart" modeli: 0,97 / 0,966 / 0,991)

### Sayım sınavı — gerçek geçiş sayısı bilinen 4 video
| Video | Gerçek | Sayılan |
|---|---|---|
| #1 | 35 | 35 |
| #2 | 41 | 41 |
| **#3 (eğitimde yok)** | **38** | **38** |
| #4 | 46 | 46 |
| Toplam | 160 | **160 → %100** |

### Kapının tam üstü videoları (sayısı "≈50" diye verilmiş, kesin değil)
| Yükseklik | Sayılan | Verilen numara | Şüpheli |
|---|---|---|---|
| 5 m | 47 | 47 | 0 |
| 6 m | 47 | 57 | 0 |
| 10 m | 47 | 50 | 0 |
Dört farklı model de bu videolarda 47–49 saydı; gerçek sayı büyük ihtimalle 47.

## Yol
| Model | 4 video | Not |
|---|---|---|
| Hazır YOLO11s (eğitimsiz) | 77/160 (%48) | tepeden koyunu tanımıyor |
| Hazır YOLO26s (eğitimsiz) | 99/160 (%62) | |
| YOLO11s, 540 kare ince ayar | 160/160 | |
| YOLO26s, 540 kare ince ayar | 160/160 | |
| YOLO11s, büyük (1.305) | 159/160 | 428 fotoğrafta R 0,981 |
| **YOLO26s, büyük (1.305)** | **160/160** | **428 fotoğrafta R 0,989 — SEÇİLDİ** |

Takipçi ayarları (güven eşiği, görüntü boyutu, ByteTrack/BoT-SORT) eğitilmiş modelde fark yaratmadı
(7 ayarın 5'i 160/160) → programdaki varsayılanlar kaldı.

## İkinci model: `modeller/koyun-birlesik.pt` (karışık sürü, 1 Kasım)

Eğitim: beyaz koyun 1.305 + **etiketli keçi 287** (ICAERUS 14929694) + köpek/insan kareleri 1.589 → 3 sınıf
(koyun/küçükbaş · köpek · insan), 40 tur, koyun-tepeden.pt'den ince ayar. Doğrulama (736 görüntü): koyun
P 0,947 R 0,950 mAP50 0,970 · insan mAP50 0,917 · köpek mAP50 0,519 (az örnek).

İkinci tur (1 Kas sabahı): aynı sette mozaiksiz, düşük öğrenme hızıyla 20 tur daha → koyun P 0,969 R 0,937,
köpek P 0,923, insan mAP50 0,922. Pakete giren sürüm bu (r2).

| Sınav | Beyaz sürü modeli | Karışık sürü modeli (r2) |
|---|---|---|
| 4 bilinen video (160 koyun) | **160/160** | 159/160 (video 13: 45/46) |
| Kapı üstü 5 m / 10 m (47) | 47 / 47 | 47 / 47 |
| Kahverengi keçi videosu (elle sayım ~83 ±3) | 76 geçiş, 20 şüpheli, çoğu kaçtı | **84 geçiş, 0 şüpheli** → %99 |
| Beyaz çoban köpeği | **koyun sanıyor** (%62) | koyun saymıyor; çoban "insan" |

Karar: programda **varsayılan = beyaz sürü modeli** (Murat'ın sürüsü açık renk); Ayarlar → Model'den
"karışık sürü" seçilebilir. Demo listesinde keçi (≈83; "≈92" eski modelin kör sayımıydı, 1 Kas yarık taramayla elle 83 sayıldı) ve köpekli videolar **kendi modelini** (karışık sürü) kullanır;
beyaz sürü modeliyle keçi videosu 76 geçiş / 20 şüpheli, kutular yanıp sönüyordu (1 Kas, Murat'ın gözlemi). Sırada (isteğe bağlı): ek ICAERUS verisiyle üçüncü tur — indirme yarım kaldı (20,5 GB setin ~0,5 GB'ı indi, ikinci set hiç inmedi); etiketsiz veri sözde etiket ister, ~yarım gün.

### Keçi videosunun gerçek sayısı (1 Kas) — veri setinde sayı yok, elle doğrulandı
Yarık tarama (sayım çizgisindeki piksel satırı her kareden alınıp üst üste dizildi; çizgiyi geçen her hayvan tek leke) ile
baş sayımı: **83 küçükbaş (±3)**, 2 insan. "≈92" eski beyaz modelin kör sayımıydı (şüpheli kayıtlarla şişmiş).

| Ayar (karışık sürü modeli, 4K kaynak) | Sayılan |
|---|---|
| 960 px, çizgi %50 (programın ayarı) | 84 |
| 1280 px, çizgi %40 | 84 |
| 1280 px, çizgi %60 | 84 |
| 1920 px, çizgi %50 | 156 ✗ (model 960'ta eğitildi, bu boyut geçersiz; programda kullanılmaz) |

Sonuç: elle 83, model 84 → %99; çizgi yeri sonucu değiştirmiyor.

## Üçüncü model: `modeller/koyun-heracidan.pt` — HER AÇIDAN (2 Kas 03:30)

Murat'ın hedefi: fotoğraf/videoda tepeden, yandan, yerden — her açıdan çalışan tek model. Eğitim seti 5.565 görüntü:
önceki karışık set (2.873) + elimizdeki **tüm** ICAERUS videolarından yeni kareler (114 video, 1.256 kare; otomatik köpek
etiketleri güvenilmez çıktı → silindi, köpek bilgisi elle temizlenmiş eski setten) + yandan/mera/uzak drone videoları
(YOLO-World "sheep" etiketiyle) + **COCO 'sheep' 1.436 yerden/yandan fotoğraf**. 30 tur, karışık modelden ince ayar, M5 Max 4 sa.

| Sınav | Beyaz sürü | Karışık (r2) | **Her açıdan (r3a)** |
|---|---|---|---|
| 4 bilinen video (160) | 160/160 | 159/160 | **160/160** |
| Tam videolar (47'lik sürü, 5 video) | 47 | 47 | **47 / 47 / 47 / 47 / 47** |
| Kahverengi keçi (elle 83) | 76, 20 şüpheli | 84 | **84** |
| Köpekli sürü | köpeği sayar | 47 | **47, köpek sayılmaz** |
| **Yandan/yerden COCO foto (158 foto, 943 koyun) mAP50** | 0,25 | 0,20 | **0,61** (P 0,70 R 0,55) |

Karar: kapı kamerası için varsayılan beyaz sürü modeli kalır (Ayarlar'dan seçilebilir); **yüklenen fotoğraf/video her
zaman her-açıdan modeliyle sayılır**; keçi/köpek demoları da onu kullanır. 4. tur (2 Kas 04:20–07:22): + 56 GB yeni ICAERUS verisi (4.767 dosya → 4.012 sözde etiketli kare; set 7.890/1.641), r3a modelinden
15 tur. Sonuç: 160/160, demolar 47/**48**/47/47/47, keçi 84, COCO yandan mAP50 0,611 (r3a 0,613). **Daha iyi değil** →
pakette `koyun-heracidan.pt` = r3a kalır; r4 `modeller/birlesik-r4.pt` olarak saklanır (`veri/r4-rapor.txt`).

## Demo videoları yeniden kesildi (1 Kas öğleden sonra, Murat'ın gözlemi)
Murat: "sayım çizgisi ortada, videolar fazla kırpılmış, koyunlar kenardan başlıyor". ICAERUS'un 4 kesiti (35/41/38/46) sürünün
ortasından başlıyordu (ör. #1: koyunlar 33. sn'de giriyor, kesit 41. sn'de başlıyor; ilk karede 46 koyun, 4'ü çizgiyi geçmiş).
Tüm demolar **tam kaynaktan, ilk koyundan 5 sn önce** başlayacak şekilde yeniden kesildi (1280×720, 15 kare/sn); yandan çekimler
listeden çıkarıldı. Tam videolarda programın sayımı (960 px, orta çizgi):

| Video (set1 23.11.23-*) | Sayılan | Not |
|---|---|---|
| Tepeden giriş #1 (-8) | 47 | kesit 35/35 |
| Tepeden giriş #2 (-10) | 47 | kesit 41/41 |
| Tepeden giriş #3 (-12) | 47 | kesit 38/38 (29 sn'de kesilince 45 → son 2 koyun 29. sn'den sonra geçiyor) |
| Tepeden giriş #4 (-13) | 47 | kesit 46/46 |
| Kapı üstü 5 m / 6 m / 10 m (-3/-4/-11) | 47 / 47 / 47 | veri seti "≈50" diyor |
| Köpekli sürü (23.11.10-1, karışık model) | 47 | köpek sayılmadı |
| Kahverengi keçi (set12, karışık model) | 84 | elle 83 |

Aynı çiftlikte aynı günlerde çekilen 7 videonun hepsi **47** veriyor → sürü 47; bu, kesit doğrulukları (160/160) ile
birlikte güçlü bir kanıt. Demo kartlarında gerçek = 47 yazıyor.

## Kurulum testleri (31 Ekim)
| Ortam | Sonuç |
|---|---|
| Mac (M5 Max) | geliştirme + tüm ölçümler; canlı RTSP kamera simülasyonu: kesilme/yeniden bağlanma, saatlik kayıt, günlük ✅ |
| Windows 11 + RTX 5060 Ti | `kur.bat` sıfırdan kuruldu (torch cu128, CUDA aktif), demo #3: **38/38**, 56 kare/sn, 0 şüpheli ✅ |

## Sırada
Çiftlikte kamera takılınca ilk haftanın görüntüleriyle son ince ayar; hedef, senin ağılında da %100.
