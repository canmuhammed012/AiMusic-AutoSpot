"""Logging yapılandırması ve yardımcı fonksiyonlar"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

_logger: Optional[logging.Logger] = None

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    clear_existing: bool = True
) -> logging.Logger:
    """
    Logging sistemini yapılandırır.
    
    Args:
        log_level: Log seviyesi (logging.DEBUG, INFO, WARNING, ERROR)
        log_file: Log dosyası yolu (None ise otomatik)
        clear_existing: Mevcut log dosyasını temizle
        
    Returns:
        Yapılandırılmış root logger
    """
    global _logger
    
    if log_file is None:
        log_dir = tempfile.gettempdir()
        log_file = os.path.join(log_dir, "ses_montaj_debug.log")
    
    # Eski log dosyasını temizle
    if clear_existing and os.path.exists(log_file):
        try:
            os.remove(log_file)
        except Exception:
            pass
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(funcName)s:%(lineno)d]'
    )
    
    # File handler
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
    except Exception as e:
        print(f"Log dosyası oluşturulamadı: {e}")
        file_handler = None
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Mevcut handler'ları temizle
    root_logger.handlers.clear()
    
    if file_handler:
        root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    _logger = root_logger
    return root_logger

def get_logger(name: str = None) -> logging.Logger:
    """
    Logger instance'ı alır.
    
    Args:
        name: Logger adı (None ise root logger)
        
    Returns:
        Logger instance
    """
    if _logger is None:
        setup_logging()
    
    if name:
        return logging.getLogger(name)
    return _logger or logging.getLogger()

