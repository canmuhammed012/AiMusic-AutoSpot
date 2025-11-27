"""Otomatik güncelleme kontrolü modülü"""

import requests
import json
import logging
from typing import Optional, Dict, Any
from packaging import version

logger = logging.getLogger(__name__)

# GitHub repository bilgileri
GITHUB_REPO_OWNER = "canmuhammed012"
GITHUB_REPO_NAME = "AiMusic-AutoSpot"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
# Alternatif: Basit JSON dosyası için
# VERSION_CHECK_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/main/latest.json"

def check_for_updates(current_version: str, timeout: int = 5) -> Dict[str, Any]:
    """
    GitHub'dan güncel versiyonu kontrol eder.
    
    Args:
        current_version: Mevcut uygulama versiyonu (örn: "8.0.0")
        timeout: İstek timeout süresi (saniye)
        
    Returns:
        Dict içinde:
            - available: bool - Güncelleme var mı?
            - version: str - Yeni versiyon numarası
            - download_url: str - İndirme linki
            - release_notes: str - Sürüm notları
            - error: str - Hata mesajı (varsa)
    """
    try:
        logger.info(f"Güncelleme kontrol ediliyor... (Mevcut: {current_version})")
        
        # GitHub API'den son release'i al
        response = requests.get(GITHUB_API_URL, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        latest_version = data.get("tag_name", "").lstrip("v")  # "v8.0.0" -> "8.0.0"
        
        if not latest_version:
            logger.warning("GitHub API'den versiyon bilgisi alınamadı")
            return {
                "available": False,
                "error": "Versiyon bilgisi bulunamadı"
            }
        
        # Versiyon karşılaştırması
        try:
            current = version.parse(current_version)
            latest = version.parse(latest_version)
            
            if latest > current:
                # Setup dosyasını bul (Windows için .exe)
                download_url = None
                for asset in data.get("assets", []):
                    if asset.get("name", "").endswith("_Setup.exe"):
                        download_url = asset.get("browser_download_url")
                        break
                
                logger.info(f"Yeni versiyon bulundu: {latest_version}")
                return {
                    "available": True,
                    "version": latest_version,
                    "download_url": download_url,
                    "release_notes": data.get("body", ""),
                    "release_url": data.get("html_url", "")
                }
            else:
                logger.info(f"Uygulama güncel: {current_version}")
                return {
                    "available": False,
                    "version": latest_version
                }
        except version.InvalidVersion as e:
            logger.error(f"Versiyon formatı geçersiz: {e}")
            return {
                "available": False,
                "error": f"Versiyon formatı geçersiz: {e}"
            }
            
    except requests.exceptions.Timeout:
        logger.warning("Güncelleme kontrolü zaman aşımına uğradı")
        return {
            "available": False,
            "error": "Bağlantı zaman aşımına uğradı"
        }
    except requests.exceptions.RequestException as e:
        logger.warning(f"Güncelleme kontrolü başarısız: {e}")
        return {
            "available": False,
            "error": f"Bağlantı hatası: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Güncelleme kontrolü sırasında beklenmeyen hata: {e}", exc_info=True)
        return {
            "available": False,
            "error": f"Beklenmeyen hata: {str(e)}"
        }

def check_for_updates_simple(current_version: str, version_url: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Basit JSON dosyasından güncelleme kontrolü (alternatif yöntem).
    
    Args:
        current_version: Mevcut uygulama versiyonu
        version_url: JSON dosyasının URL'i
        timeout: İstek timeout süresi
        
    Returns:
        Güncelleme bilgisi dict'i
    """
    try:
        logger.info(f"Güncelleme kontrol ediliyor... (Basit yöntem)")
        
        response = requests.get(version_url, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        latest_version = data.get("version", "")
        download_url = data.get("download_url", "")
        release_notes = data.get("release_notes", "")
        
        if not latest_version:
            return {
                "available": False,
                "error": "Versiyon bilgisi bulunamadı"
            }
        
        try:
            current = version.parse(current_version)
            latest = version.parse(latest_version)
            
            if latest > current:
                return {
                    "available": True,
                    "version": latest_version,
                    "download_url": download_url,
                    "release_notes": release_notes
                }
            else:
                return {
                    "available": False,
                    "version": latest_version
                }
        except version.InvalidVersion as e:
            return {
                "available": False,
                "error": f"Versiyon formatı geçersiz: {e}"
            }
            
    except Exception as e:
        logger.error(f"Güncelleme kontrolü başarısız: {e}")
        return {
            "available": False,
            "error": str(e)
        }

