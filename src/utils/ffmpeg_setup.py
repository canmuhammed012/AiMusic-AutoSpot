"""FFmpeg kurulumu ve yapılandırması"""

import os
import sys
import shutil
import tempfile
import glob
import logging
import subprocess
import importlib.util
from pydub import AudioSegment
from .file_utils import get_resource_path

logger = logging.getLogger(__name__)

# Patch'in sadece bir kez uygulandığından emin olmak için flag
_subprocess_patched = False

# Pydub'un subprocess çağrılarını gizli çalıştırmak için patch
_original_popen = subprocess.Popen
_original_call = subprocess.call
_original_run = subprocess.run
_original_check_call = subprocess.check_call
_original_check_output = subprocess.check_output

def _hidden_popen(*args, **kwargs):
    """Gizli subprocess.Popen wrapper - CMD pencerelerini önler"""
    if sys.platform == "win32":
        # Windows'ta CMD penceresini gizle
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        if 'startupinfo' not in kwargs:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = startupinfo
        # stdout ve stderr'i gizle (eğer belirtilmemişse)
        if 'stdout' not in kwargs:
            kwargs['stdout'] = subprocess.DEVNULL
        if 'stderr' not in kwargs:
            kwargs['stderr'] = subprocess.DEVNULL
    return _original_popen(*args, **kwargs)

def _hidden_call(*args, **kwargs):
    """Gizli subprocess.call wrapper"""
    if sys.platform == "win32":
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        if 'startupinfo' not in kwargs:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = startupinfo
    return _original_call(*args, **kwargs)

def _hidden_run(*args, **kwargs):
    """Gizli subprocess.run wrapper"""
    if sys.platform == "win32":
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        if 'startupinfo' not in kwargs:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = startupinfo
    return _original_run(*args, **kwargs)

def _hidden_check_call(*args, **kwargs):
    """Gizli subprocess.check_call wrapper"""
    if sys.platform == "win32":
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        if 'startupinfo' not in kwargs:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = startupinfo
    return _original_check_call(*args, **kwargs)

def _hidden_check_output(*args, **kwargs):
    """Gizli subprocess.check_output wrapper"""
    if sys.platform == "win32":
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        if 'startupinfo' not in kwargs:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = startupinfo
    return _original_check_output(*args, **kwargs)

def _patch_pydub_subprocess():
    """Pydub'un subprocess çağrılarını patch eder - Köklü ve agresif patch"""
    global _subprocess_patched
    
    # Patch zaten uygulanmışsa tekrar uygulama
    if _subprocess_patched:
        return
    
    # 1. Global subprocess modülünü tamamen patch et (en kritik)
    try:
        import subprocess as sp
        sp.Popen = _hidden_popen
        sp.call = _hidden_call
        sp.run = _hidden_run
        sp.check_call = _hidden_check_call
        sp.check_output = _hidden_check_output
        logger.debug("Global subprocess modülü patch'lendi (tüm fonksiyonlar)")
    except Exception as e:
        logger.warning(f"Global subprocess patch'i uygulanamadı: {e}")
    
    # 1.5. sys.modules'deki subprocess'i de patch et (import cache'i override et)
    # Bu, daha sonra import edilecek modüller için de geçerli olacak
    try:
        if 'subprocess' in sys.modules:
            mod = sys.modules['subprocess']
            mod.Popen = _hidden_popen
            mod.call = _hidden_call
            mod.run = _hidden_run
            mod.check_call = _hidden_check_call
            mod.check_output = _hidden_check_output
            logger.debug("sys.modules subprocess patch'lendi")
    except Exception as e:
        logger.debug(f"sys.modules subprocess patch hatası: {e}")
    
    # 2. sys.modules'deki subprocess'i de patch et (import cache'i override et)
    try:
        if 'subprocess' in sys.modules:
            sys.modules['subprocess'].Popen = _hidden_popen
            sys.modules['subprocess'].call = _hidden_call
            sys.modules['subprocess'].run = _hidden_run
            sys.modules['subprocess'].check_call = _hidden_check_call
            sys.modules['subprocess'].check_output = _hidden_check_output
            logger.debug("sys.modules subprocess patch'lendi")
    except Exception as e:
        logger.debug(f"sys.modules subprocess patch hatası: {e}")
    
    # 3. Pydub'un utils modülünü patch et
    try:
        import pydub.utils
        if hasattr(pydub.utils, 'subprocess'):
            pydub.utils.subprocess.Popen = _hidden_popen
            pydub.utils.subprocess.call = _hidden_call
            pydub.utils.subprocess.run = _hidden_run
            pydub.utils.subprocess.check_call = _hidden_check_call
            pydub.utils.subprocess.check_output = _hidden_check_output
        logger.debug("Pydub utils subprocess patch'lendi")
    except Exception as e:
        logger.debug(f"Pydub utils patch hatası (normal olabilir): {e}")
    
    # 4. Pydub'un _utils modülünü de kontrol et
    try:
        from pydub import _utils
        if hasattr(_utils, 'subprocess'):
            _utils.subprocess.Popen = _hidden_popen
            _utils.subprocess.call = _hidden_call
            _utils.subprocess.run = _hidden_run
            _utils.subprocess.check_call = _hidden_check_call
            _utils.subprocess.check_output = _hidden_check_output
        logger.debug("Pydub _utils subprocess patch'lendi")
    except:
        pass
    
    # 5. Pydub'un _run_ffmpeg veya benzeri internal fonksiyonlarını patch et
    try:
        import pydub.utils
        if hasattr(pydub.utils, '_run_ffmpeg'):
            original_run_ffmpeg = pydub.utils._run_ffmpeg
            def _patched_run_ffmpeg(*args, **kwargs):
                # subprocess çağrılarını gizli yap
                if 'popen_kwargs' not in kwargs:
                    kwargs['popen_kwargs'] = {}
                if sys.platform == "win32":
                    kwargs['popen_kwargs']['creationflags'] = subprocess.CREATE_NO_WINDOW
                    if 'startupinfo' not in kwargs['popen_kwargs']:
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        startupinfo.wShowWindow = subprocess.SW_HIDE
                        kwargs['popen_kwargs']['startupinfo'] = startupinfo
                return original_run_ffmpeg(*args, **kwargs)
            pydub.utils._run_ffmpeg = _patched_run_ffmpeg
            logger.debug("Pydub _run_ffmpeg patch'i uygulandı")
    except Exception as e:
        logger.debug(f"Pydub _run_ffmpeg patch hatası (normal olabilir): {e}")
    
    # 6. Pydub'un tüm internal modüllerini tarayarak subprocess referanslarını patch et
    try:
        import pydub
        for attr_name in dir(pydub):
            try:
                attr = getattr(pydub, attr_name)
                if hasattr(attr, 'subprocess'):
                    attr.subprocess.Popen = _hidden_popen
                    attr.subprocess.call = _hidden_call
                    attr.subprocess.run = _hidden_run
                    attr.subprocess.check_call = _hidden_check_call
                    attr.subprocess.check_output = _hidden_check_output
            except:
                pass
        logger.debug("Pydub internal modüller taranıp patch'lendi")
    except Exception as e:
        logger.debug(f"Pydub internal tarama hatası: {e}")
    
    # 7. AudioSegment.from_file metodunu da patch et (dosya yükleme için)
    # Bu metod pydub'un en çok kullanılan metodlarından biri
    try:
        _original_from_file = AudioSegment.from_file
        def _patched_from_file(file_path, format=None, codec=None, parameters=None, **kwargs):
            """Patch edilmiş from_file metodu - subprocess çağrılarını gizli yapar"""
            # Parameters'ı düzenle (eğer yoksa oluştur)
            if parameters is None:
                parameters = []
            else:
                parameters = list(parameters)  # Kopyala (değiştirilebilir liste)
            
            # -nostdin ve -loglevel quiet ekle (eğer yoksa)
            has_nostdin = any(p == "-nostdin" for p in parameters if isinstance(p, str))
            has_loglevel = any(p == "-loglevel" for p in parameters if isinstance(p, str))
            
            if not has_nostdin:
                parameters.insert(0, "-nostdin")
            if not has_loglevel:
                # -loglevel quiet ekle
                parameters.insert(1, "-loglevel")
                parameters.insert(2, "quiet")
            
            return _original_from_file(file_path, format=format, codec=codec, parameters=parameters, **kwargs)
        
        AudioSegment.from_file = _patched_from_file
        logger.debug("AudioSegment.from_file patch'i uygulandı")
    except Exception as e:
        logger.warning(f"AudioSegment.from_file patch'i uygulanamadı: {e}")
    
    # 8. AudioSegment.export metodunu da patch et (daha agresif)
    # Bu metod montaj sırasında en çok çağrılan metod
    try:
        _original_export = AudioSegment.export
        def _patched_export(self, out_f, format="mp3", codec=None, bitrate=None, parameters=None, tags=None, id3v2_version="4", cover=None):
            """Patch edilmiş export metodu - subprocess çağrılarını gizli yapar"""
            # Parameters'ı düzenle (eğer yoksa oluştur)
            if parameters is None:
                parameters = []
            else:
                parameters = list(parameters)  # Kopyala (değiştirilebilir liste)
            
            # -nostdin ve -loglevel quiet ekle (eğer yoksa)
            has_nostdin = any(p == "-nostdin" for p in parameters if isinstance(p, str))
            has_loglevel = any(p == "-loglevel" for p in parameters if isinstance(p, str))
            
            if not has_nostdin:
                parameters.insert(0, "-nostdin")
            if not has_loglevel:
                # -loglevel quiet ekle
                parameters.insert(1, "-loglevel")
                parameters.insert(2, "quiet")
            
            return _original_export(self, out_f, format=format, codec=codec, bitrate=bitrate, 
                                   parameters=parameters, tags=tags, id3v2_version=id3v2_version, cover=cover)
        
        AudioSegment.export = _patched_export
        logger.debug("AudioSegment.export patch'i uygulandı")
    except Exception as e:
        logger.warning(f"AudioSegment.export patch'i uygulanamadı: {e}")
    
    # Patch tamamlandı - flag'i set et
    _subprocess_patched = True
    logger.info("Subprocess patch'i başarıyla uygulandı (tüm subprocess çağrıları gizli çalışacak)")

def detect_and_set_ffmpeg() -> str:
    """
    FFmpeg'i tespit eder ve yapılandırır.
    
    Returns:
        FFmpeg executable yolu
        
    Raises:
        Exception: FFmpeg bulunamazsa
    """
    # Pydub'un subprocess çağrılarını patch et (CMD pencerelerini önlemek için)
    _patch_pydub_subprocess()
    
    try:
        # Önce sistem PATH'inde ara
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            AudioSegment.converter = ffmpeg_path
            logger.info(f"FFmpeg sistem PATH'inde bulundu: {ffmpeg_path}")
            return ffmpeg_path
        
        # Proje klasöründe ara
        temp_dir = tempfile.gettempdir()
        temp_ffmpeg_dir = os.path.join(temp_dir, "ses_montaj_ffmpeg")
        os.makedirs(temp_ffmpeg_dir, exist_ok=True)
        
        source_dir = get_resource_path("ffmpeg/bin")
        if os.path.exists(source_dir):
            # Gerekli dosyaları kopyala (ffplay dahil)
            required_files = ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]
            for file in required_files:
                src = os.path.join(source_dir, file)
                dst = os.path.join(temp_ffmpeg_dir, file)
                if os.path.exists(src) and not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    logger.info(f"FFmpeg dosyası kopyalandı: {file}")
            
            # DLL dosyalarını da kopyala (FFmpeg için gerekli)
            dll_patterns = ["av*.dll", "sw*.dll", "postproc*.dll"]
            for pattern in dll_patterns:
                for dll_file in glob.glob(os.path.join(source_dir, pattern)):
                    dll_name = os.path.basename(dll_file)
                    dst = os.path.join(temp_ffmpeg_dir, dll_name)
                    if not os.path.exists(dst):
                        try:
                            shutil.copy2(dll_file, dst)
                            logger.debug(f"DLL kopyalandı: {dll_name}")
                        except Exception as e:
                            logger.warning(f"DLL kopyalanamadı {dll_name}: {e}")
            
            # Tüm DLL dosyalarını kopyala (daha kapsamlı)
            for dll_file in glob.glob(os.path.join(source_dir, "*.dll")):
                dll_name = os.path.basename(dll_file)
                dst = os.path.join(temp_ffmpeg_dir, dll_name)
                if not os.path.exists(dst):
                    try:
                        shutil.copy2(dll_file, dst)
                        logger.debug(f"DLL kopyalandı: {dll_name}")
                    except Exception as e:
                        logger.warning(f"DLL kopyalanamadı {dll_name}: {e}")
            
            # PATH'e ekle
            if temp_ffmpeg_dir not in os.environ['PATH']:
                os.environ['PATH'] = temp_ffmpeg_dir + os.pathsep + os.environ['PATH']
            
            # Tekrar kontrol et
            ffmpeg_path = shutil.which("ffmpeg")
            if ffmpeg_path:
                AudioSegment.converter = ffmpeg_path
                logger.info(f"FFmpeg temp klasöründe bulundu: {ffmpeg_path}")
                
                # ffplay'i de kontrol et
                ffplay_path = shutil.which("ffplay")
                if ffplay_path:
                    logger.info(f"FFplay temp klasöründe bulundu: {ffplay_path}")
                
                return ffmpeg_path
        
        raise Exception("FFmpeg bulunamadı. Lütfen FFmpeg'in kurulu olduğundan emin olun.")
        
    except Exception as e:
        logger.error(f"FFmpeg ayarlanırken hata: {e}", exc_info=True)
        raise

