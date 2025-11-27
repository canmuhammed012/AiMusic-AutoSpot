"""Ses Montaj Uygulaması - Ana Giriş Noktası"""

import sys
import os
import customtkinter as ctk
from tkinter import messagebox

# Proje kök dizinini path'e ekle
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from src.utils.logger import setup_logging, get_logger
from src.utils.ffmpeg_setup import detect_and_set_ffmpeg, _patch_pydub_subprocess
from src.gui.main_window import MainWindow
from src.constants import APP_VERSION, APP_NAME

def main():
    """Ana fonksiyon"""
    # ÖNCE subprocess patch'ini uygula (CMD pencerelerini önlemek için)
    # Bu, FFmpeg ayarlanmadan önce yapılmalı
    try:
        _patch_pydub_subprocess()
    except Exception as e:
        # Patch hatası kritik değil, devam et
        pass
    
    # Logging'i başlat
    logger = setup_logging()
    logger.info(f"{APP_NAME} v{APP_VERSION} başlatılıyor...")
    
    # FFmpeg'i ayarla (içinde de patch çağrılıyor ama zaten uygulanmış olacak)
    try:
        detect_and_set_ffmpeg()
        logger.info("FFmpeg başarıyla yapılandırıldı")
    except Exception as e:
        logger.error(f"FFmpeg ayarlanırken hata: {e}")
        messagebox.showerror(
            "Kritik Hata",
            f"FFmpeg başlatılamadı:\n\n{e}\n\n"
            "Lütfen FFmpeg'in kurulu olduğundan veya proje klasöründe "
            "bulunduğundan emin olun."
        )
        sys.exit(1)
    
    # GUI'yi başlat
    try:
        ctk.set_appearance_mode("light")
        app = MainWindow()
        logger.info("Uygulama başlatıldı")
        app.mainloop()
    except Exception as e:
        logger.error(f"Uygulama hatası: {e}", exc_info=True)
        messagebox.showerror(
            "Kritik Hata",
            f"Uygulama başlatılamadı:\n\n{e}"
        )
        sys.exit(1)
    finally:
        logger.info("Uygulama kapatılıyor...")

if __name__ == "__main__":
    main()

