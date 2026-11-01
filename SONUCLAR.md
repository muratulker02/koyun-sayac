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
beyaz sürü modeliyle keçi videosu 76 geçiş / 20 şüpheli, kutular yanıp sönüyordu (1 Kas, Murat'ın gözlemi). Sırada: 51 GB ek ICAERUS verisi (indirildi) ile üçüncü tur, hedef tek modelde ikisi de.

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

## Kurulum testleri (31 Ekim)
| Ortam | Sonuç |
|---|---|
| Mac (M5 Max) | geliştirme + tüm ölçümler; canlı RTSP kamera simülasyonu: kesilme/yeniden bağlanma, saatlik kayıt, günlük ✅ |
| Windows 11 + RTX 5060 Ti | `kur.bat` sıfırdan kuruldu (torch cu128, CUDA aktif), demo #3: **38/38**, 56 kare/sn, 0 şüpheli ✅ |

## Sırada
Çiftlikte kamera takılınca ilk haftanın görüntüleriyle son ince ayar; hedef, senin ağılında da %100.
