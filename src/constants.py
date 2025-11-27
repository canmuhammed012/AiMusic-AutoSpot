"""Ses Montaj Uygulaması - Sabitler ve Yapılandırma"""

# Uygulama Bilgileri
APP_VERSION = "8.0.0"
APP_NAME = "Ai Music AutoSpot"
FONT_FAMILY = "Roboto"

# Ses İşleme Sabitleri
class AudioConfig:
    """Ses işleme zamanlama sabitleri (milisaniye)"""
    INTRO_DURATION_MS = 3000
    OUTRO_RISE_DURATION_MS = 2000
    OUTRO_FALL_DURATION_MS = 3000
    SILENCE_GAP_MS = 50
    MIN_OUTRO_BODY_MS = 3500
    MIN_PLATEAU_DURATION_MS = 4000
    FADE_OVERLAP_FIX_MS = 250
    PLATEAU_SILENCE_GAP_MS = 180

# Ses Seviyesi Sabitleri (dB)
class AudioLevels:
    """Ses seviyesi ayarları"""
    START_FON_DB = -5.0  # Fon müziği giriş seviyesi (sabit)
    DUCKED_FON_DB = -10.2  # %35 seviyesi (ham ses boyunca)
    MID_FON_DB = -1.94  # %80 seviyesi (çıkış yükselişi)
    VOICE_DB = -4.0  # Konuşma seviyesi (ham ses)
    PEAK_HEADROOM_DB = -1.0
    SILENCE_DB = -80.0  # %0 seviyesi (fade-out için)

# Kompresör Ayarları
class CompressorConfig:
    """Dinamik aralık kompresörü ayarları"""
    THRESHOLD = -22.0
    RATIO = 3.0
    ATTACK = 8.0
    RELEASE = 80.0

# Ses Analizi Sabitleri
class AnalysisConfig:
    """Ses analizi parametreleri"""
    MIN_SILENCE_LEN = 400
    SILENCE_THRESH = -45
    SAMPLE_RATE = 22050
    FRAME_LENGTH = 2048
    HOP_LENGTH = 512
    RMS_THRESHOLD_RATIO = 0.7
    MIN_HOLD_MS = 4000
    ONE_MEASURE_FALLBACK_MS = 2500
    MIN_TOTAL_OUTRO_MS = 5000
    FALLBACK_OUTRO_MS = 7000
    GAIN_RAMP_STEP_MS = 15
    LINEAR_GAIN_RAMP_STEP_MS = 20
    MAX_GAP_MS = 1400  # Segment birleştirme için maksimum boşluk
    MIN_SEGMENT_LENGTH_MS = 1000  # Minimum geçerli segment uzunluğu

# Çıktı Ayarları
class OutputConfig:
    """Çıktı formatı ve kalite ayarları"""
    DEFAULT_FORMAT = "wav"
    MP3_BITRATE = "320k"
    DEFAULT_OUTPUT_FOLDER = "Desktop/Montajlanan"

# UI Sabitleri
class UIConfig:
    """Kullanıcı arayüzü sabitleri"""
    WINDOW_WIDTH = 1100
    WINDOW_HEIGHT = 360
    MIN_WINDOW_WIDTH = 1000
    MIN_WINDOW_HEIGHT = 340
    DEFAULT_THEME = "light"
    ANIMATION_DURATION = 200  # ms
    CARD_CORNER_RADIUS = 16
    BUTTON_CORNER_RADIUS = 12

# Desteklenen Dosya Formatları
SUPPORTED_AUDIO_FORMATS = ["*.wav", "*.mp3", "*.m4a", "*.flac", "*.aac", "*.ogg"]
AUDIO_FILE_TYPES = [("Ses dosyaları", " ".join(SUPPORTED_AUDIO_FORMATS))]

# Preset Kategorileri
PRESET_CATEGORIES = {
    "AI Music": "presets/ai-music",
    "Yeni Fonlar": "presets/yeni-fonlar",
    "Best Of": "presets/best-of",
    "Firma Fonları": "presets/firma-fonları",
    "Enerjik": "presets/enerjik",
    "Orta Ritimli": "presets/orta",
    "Düşük Ritimli": "presets/dusuk",
    "Dramatik": "presets/dramatik",
}

# Bitiş Kategorileri
ENDING_CATEGORIES = {
    "Bitiş Sesleri": "presets/bitis",
}

