"""Hızlı başlatma scripti - proje kökünden çalıştırın"""

import sys
import os
import traceback

# Proje kök dizinini path'e ekle
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# CRITICAL: Subprocess patch'ini EN BAŞTA uygula (CMD pencerelerini önlemek için)
# Bu, tüm modüller import edilmeden önce çalışmalı
try:
    from src.utils.ffmpeg_setup import _patch_pydub_subprocess
    _patch_pydub_subprocess()
except Exception as e:
    # Patch başarısız olsa bile devam et (ama log'la)
    import logging
    logging.basicConfig(level=logging.WARNING)
    logger = logging.getLogger(__name__)
    logger.warning(f"Subprocess patch uygulanamadı (devam ediliyor): {e}")

# Ana modülü çalıştır
try:
    from src.main import main
    
    if __name__ == "__main__":
        main()
except Exception as e:
    # Hata durumunda konsol penceresinin kapanmaması için
    print("=" * 60)
    print("KRİTİK HATA - Uygulama başlatılamadı!")
    print("=" * 60)
    print(f"\nHata: {str(e)}")
    print("\nDetaylı hata bilgisi:")
    print("-" * 60)
    traceback.print_exc()
    print("=" * 60)
    print("\nBu pencereyi kapatmak için Enter tuşuna basın...")
    try:
        input()
    except:
        pass
    sys.exit(1)

