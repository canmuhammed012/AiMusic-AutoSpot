# Ai Music AutoSpot

Otomatik ses montaj uygulaması - Spot tespiti, fon müziği entegrasyonu ve profesyonel ses işleme.

## Özellikler

- 🎯 Otomatik spot tespiti
- 🎵 Fon müziği entegrasyonu
- 🎨 Modern ve kullanıcı dostu arayüz
- ⚙️ Gelişmiş ayarlar
- 🔄 Otomatik güncelleme sistemi
- 📦 Hazır preset katalogları

## Kurulum

1. `Setup/Ai Music AutoSpot_8.0.0_Setup.exe` dosyasını çalıştırın
2. Kurulum sihirbazını takip edin
3. Uygulamayı başlatın

## Gereksinimler

- Windows 10/11
- FFmpeg (uygulama ile birlikte gelir)

## Geliştirme

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# FFmpeg'i indir ve proje klasörüne yerleştir
# FFmpeg dosyaları GitHub'da yok (çok büyük olduğu için)
# FFmpeg'i https://ffmpeg.org/download.html adresinden indirin
# ve ffmpeg/bin/ klasörüne yerleştirin

# Uygulamayı çalıştır
python run.py

# Setup dosyası oluştur
build_setup_new.bat
```

### FFmpeg Kurulumu (Geliştirme için)

FFmpeg dosyaları GitHub'da bulunmuyor (dosya boyutu limiti nedeniyle). Geliştirme yapmak için:

1. FFmpeg'i [resmi sitesinden](https://ffmpeg.org/download.html) indirin
2. Windows build'i seçin
3. `ffmpeg/bin/` klasörüne şu dosyaları yerleştirin:
   - `ffmpeg.exe`
   - `ffprobe.exe`
   - `ffplay.exe`
   - Tüm `.dll` dosyaları (`av*.dll`, `sw*.dll`, vb.)

**Not:** Normal kullanıcılar için FFmpeg setup dosyasına dahil edilmiştir, ekstra kurulum gerekmez.

## Lisans

© 2025 Kavartkurt A.Ş. All Rights Reserved.

