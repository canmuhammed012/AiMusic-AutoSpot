"""Yapılandırma yönetimi"""

import json
import os
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Uygulama yapılandırmasını yönetir"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        ConfigManager başlatır.
        
        Args:
            config_file: Yapılandırma dosyası yolu (None ise varsayılan)
        """
        if config_file is None:
            # AppData kullan (kalıcı depolama)
            appdata = os.getenv('APPDATA')
            if appdata:
                config_dir = os.path.join(appdata, "AiMusicAutoSpot")
                os.makedirs(config_dir, exist_ok=True)
                config_file = os.path.join(config_dir, "settings.json")
            else:
                # Fallback: temp dizini
                config_file = os.path.join(
                    tempfile.gettempdir(), 
                    "aimusic_settings.json"
                )
        
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """
        Yapılandırmayı dosyadan yükle.
        
        Returns:
            Yüklenen yapılandırma sözlüğü
        """
        try:
            if os.path.exists(self.config_file):
                # Dosya boyutunu kontrol et
                if os.path.getsize(self.config_file) == 0:
                    # Boş dosya, varsayılan ayarları kullan
                    self._config = self._get_default_config()
                    return self._config
                
                with open(self.config_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        # Boş içerik
                        self._config = self._get_default_config()
                        return self._config
                    
                    self._config = json.loads(content)
            else:
                self._config = self._get_default_config()
        except json.JSONDecodeError as e:
            # JSON parse hatası - dosya bozuk, varsayılan ayarları kullan
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Config dosyası bozuk, varsayılan ayarlar kullanılıyor: {e}")
            self._config = self._get_default_config()
            # Bozuk dosyayı yedekle ve yeniden oluştur
            try:
                backup_file = self.config_file + ".backup"
                if os.path.exists(self.config_file):
                    import shutil
                    shutil.move(self.config_file, backup_file)
            except Exception:
                pass
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Ayarlar yüklenemedi: {e}")
            self._config = self._get_default_config()
        
        return self._config
    
    def save(self) -> bool:
        """
        Yapılandırmayı dosyaya kaydet.
        
        Returns:
            Başarılı ise True
        """
        try:
            # Klasör yoksa oluştur
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ayarlar kaydedilemedi: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Yapılandırma değeri al.
        
        Args:
            key: Anahtar (nokta ile nested: "ui.theme")
            default: Varsayılan değer
            
        Returns:
            Yapılandırma değeri
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Yapılandırma değeri ayarla.
        
        Args:
            key: Anahtar (nokta ile nested: "ui.theme")
            value: Değer
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Yapılandırmayı güncelle.
        
        Args:
            updates: Güncelleme sözlüğü
        """
        self._config.update(updates)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Varsayılan yapılandırmayı döndürür"""
        return {
            "output_format": "wav",
            "theme": "light",
            "window_geometry": {
                "width": 1100,
                "height": 750
            },
            "last_paths": {
                "ham": "",
                "fon": "",
                "output": ""
            }
        }

