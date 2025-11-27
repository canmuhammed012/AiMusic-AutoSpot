"""Dosya işlemleri yardımcı fonksiyonlar"""

import os
import sys
from typing import Tuple, Optional
from pathlib import Path

def get_resource_path(relative_path: str) -> str:
    """
    Kaynak dosya yolunu döndürür (PyInstaller uyumlu).
    
    Args:
        relative_path: Kaynak dosyasının göreli yolu
        
    Returns:
        Mutlak dosya yolu
    """
    try:
        # PyInstaller bundle içinde mi?
        base_path = sys._MEIPASS
    except Exception:
        # Normal Python çalıştırması
        # src/utils/file_utils.py -> src/utils -> src -> proje kökü
        current_file = os.path.abspath(__file__)
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    
    # Path'i normalize et (Windows için backslash)
    full_path = os.path.join(base_path, relative_path)
    full_path = os.path.normpath(full_path)
    
    return full_path

def format_path_display(path: str, max_len: int = 60) -> str:
    """
    Dosya yolunu görüntüleme için formatlar.
    
    Args:
        path: Dosya yolu
        max_len: Maksimum uzunluk
        
    Returns:
        Formatlanmış yol
    """
    if len(path) <= max_len:
        return path
    
    base_name = os.path.basename(path)
    dir_name = os.path.dirname(path)
    
    if len(base_name) > max_len - 5:
        return "..." + base_name[-(max_len - 5):]
    
    remaining_len = max_len - len(base_name) - 3
    if len(dir_name) <= remaining_len:
        return path
    
    return dir_name[:remaining_len] + "..." + os.sep + base_name

def validate_audio_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Ses dosyasını doğrular.
    
    Args:
        file_path: Dosya yolu
        
    Returns:
        (is_valid, error_message) tuple
    """
    # Dosya var mı?
    if not os.path.exists(file_path):
        return False, "Dosya bulunamadı."
    
    # Dosya okunabilir mi?
    if not os.access(file_path, os.R_OK):
        return False, "Dosya okunamıyor."
    
    # Dosya boş mu?
    if os.path.getsize(file_path) == 0:
        return False, "Dosya boş."
    
    # Dosya çok büyük mü? (1GB limit)
    max_size = 1024 * 1024 * 1024  # 1GB
    if os.path.getsize(file_path) > max_size:
        return False, "Dosya çok büyük (maksimum 1GB)."
    
    # Format kontrolü (uzantı)
    valid_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg']
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in valid_extensions:
        return False, f"Desteklenmeyen dosya formatı: {ext}"
    
    return True, None

def ensure_directory(path: str) -> bool:
    """
    Klasörün var olduğundan emin olur, yoksa oluşturur.
    
    Args:
        path: Klasör yolu
        
    Returns:
        Başarılı ise True
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False

