# 🐑 Koyun Sayacı — Kurulum ve Kullanım

Kapının üstündeki kameradan geçen koyunları sayar, sabah çıkan ile akşam gireni karşılaştırır,
eksik varsa Telegram'dan haber verir.

## 1) Kurulum

**Windows:** klasörü `C:\KoyunSayaci` gibi bir yere kopyalayın → `kur.bat`'a çift tıklayın →
bitince masaüstünde **Koyun Sayacı** simgesi oluşur. (NVIDIA ekran kartı varsa otomatik kullanır.)

**Mac:** `kur.command`'a çift tıklayın (ilk açılışta sağ tık → Aç gerekebilir).

Kurulum interneti kullanır, 5–15 dk sürer. Program sonra internetsiz de sayar; yalnız Telegram için internet gerekir.

## 2) İlk ayar (bir kez)

Programı açın → sağda **⚙️ Ayarlar**:

1. **Kamera adresi**: kameranın RTSP adresi, örn. `rtsp://admin:sifre@192.168.1.64:554/stream1`
   (adres kameranın kutusunda/uygulamasında yazar). **Dene**'ye basın, görüntü ekrana gelmeli.
2. **Sürü sayısı**: 700. **Tolerans**: 0 (alarm vermeden önce göz yumulacak fark).
3. **Akşam kontrol saati**: raporun otomatik gideceği saat (örn. 19:30).
4. Görüntüde **✏️ Sayma çizgisini çiz** → kapının iki ucuna tıklayın. Sarı ok **ÇIKIŞ** yönünü gösterir;
   tersse **⇄ Yönü çevir**.
5. **📨 Telegram**: @BotFather'dan bot açın, anahtarı yapıştırın, bota "merhaba" yazın, **Bağla**.
6. **Kaydet** → **▶ İzlemeyi başlat**. Bundan sonra program açılınca izleme kendiliğinden başlar.

## 3) Günlük kullanım

Hiçbir şeye basmanız gerekmez. Ekranda:
- **Bugün çıkan / giren / şu an dışarıda** — anlık.
- Her koyunun üstünde **#numara**; yeşil = sayıldı, sarı = henüz çizgiyi geçmedi, **ŞÜPHELİ** = çizgiye
  yaklaşıp geçmeden kaybolan iz (olası kaçırma — akşam sayı tutmazsa önce buna bakın).
- Telegram'a: son koyun girince "✅ Hepsi içeride", akşam kontrol saatinde rapor, eksikse "⚠️ EKSİK VAR".
- **📨 Şimdi durum raporu gönder** ile istediğiniz an rapor alırsınız.

## 4) Kayıtlar (hepsi `kayitlar/` klasöründe)

| Dosya | İçerik |
|---|---|
| `gecisler.csv` | her geçiş: tarih, saat, çıkan, giren, dışarıda (Excel'de açılır) |
| `2026-10-31.json` | günün özeti: toplamlar, ilk çıkış / son giriş saati, akşam raporu |
| `sistem.log` | kamera bağlandı/koptu, rapor gitti, program açıldı |
| `video/2026-10-31_07.mp4` | saatlik işaretli görüntü kaydı (şüphede izleyin) |

## 5) Kamera kurulum kuralları

1. Kamera **kapının tam üstünde, aşağı dik bakacak**, 4–5 m yükseklikte (4 mm lens ≈ 6 m genişlik görür).
2. Kapı **1–2 koyun genişliğinde** daraltılırsa doğruluk en yüksek olur.
3. Işık **yandan** (30–50 W LED projektör); kameraya doğru değil.
4. Güneşlik; kamera gün doğumu/batımında güneşe bakmasın.
5. Kurulumdan sonra bir sabah çıkışını elle de sayıp programla karşılaştırın.

## 6) Sorun giderme

- **"Kameraya bağlanılamadı"**: adres/şifre yanlış ya da kamera ağda değil. Kameranın kendi uygulamasında
  RTSP'nin açık olduğundan emin olun.
- **Sayı eksik çıkıyor**: çizgi kapının tamamını kesiyor mu? Koyunlar çizginin dışından geçiyorsa sayılmaz.
  Kamera eğik bakıyorsa koyunlar üst üste biner; dik bakmalı.
- **Program açılmıyor**: `kur.bat`'ı yeniden çalıştırın. Windows'ta `sunucu.log` hatayı yazar.
- Mac'te 8780 portu doluysa `app.py` içindeki port numarasını değiştirin.

Model: `modeller/koyun-tepeden.pt` (tepeden koyun için eğitilmiş). Yeni model gelince bu dosyanın üstüne
kopyalamak yeter; program açılışta onu kullanır.
