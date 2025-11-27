"""Ses efektleri ve işleme fonksiyonları"""

from typing import Literal
import numpy as np
from pydub import AudioSegment
from io import BytesIO
import logging

from ..constants import AnalysisConfig

logger = logging.getLogger(__name__)

def normalize_audio_in_memory(audio_segment: AudioSegment) -> AudioSegment:
    """
    Ses segmentini bellekte normalize eder (gerçek normalizasyon).
    Peak normalizasyonu uygular ve ses seviyesini optimize eder.
    
    Args:
        audio_segment: Normalize edilecek ses segmenti
        
    Returns:
        Normalize edilmiş ses segmenti
    """
    try:
        if len(audio_segment) == 0:
            return audio_segment
        
        # Peak normalizasyonu - maksimum seviyeye normalize et
        # -0.1 dB headroom bırak (clipping önleme)
        target_dBFS = -0.1
        change_in_dB = target_dBFS - audio_segment.max_dBFS
        
        if abs(change_in_dB) > 0.1:  # Sadece önemli farklar için normalize et
            normalized = audio_segment.apply_gain(change_in_dB)
            logger.debug(f"Normalizasyon uygulandı: {audio_segment.max_dBFS:.2f} dB -> {normalized.max_dBFS:.2f} dB")
            return normalized
        
        return audio_segment
    except Exception as e:
        logger.warning(f"Normalizasyon hatası, orijinal segment döndürülüyor: {e}")
        return audio_segment

def apply_linear_gain_ramp(
    segment: AudioSegment,
    start_gain_db: float,
    end_gain_db: float,
    step_ms: int = None
) -> AudioSegment:
    """
    Doğrusal gain ramp uygular.
    
    Args:
        segment: İşlenecek ses segmenti
        start_gain_db: Başlangıç gain (dB)
        end_gain_db: Bitiş gain (dB)
        step_ms: Adım süresi (ms), None ise varsayılan kullanılır
        
    Returns:
        İşlenmiş ses segmenti
    """
    if step_ms is None:
        step_ms = AnalysisConfig.LINEAR_GAIN_RAMP_STEP_MS
    
    try:
        if len(segment) == 0 or start_gain_db == end_gain_db:
            return segment.apply_gain(start_gain_db)
        
        total_ms = len(segment)
        steps = max(1, total_ms // step_ms)
        output = AudioSegment.silent(duration=0, frame_rate=segment.frame_rate)
        
        for i in range(steps):
            seg_start = i * step_ms
            seg_end = total_ms if i == steps - 1 else (i + 1) * step_ms
            t = (seg_start + seg_end) / 2.0 / max(1, total_ms)
            current_gain = start_gain_db + (end_gain_db - start_gain_db) * t
            output += segment[seg_start:seg_end].apply_gain(current_gain)
        
        return output
    except Exception as e:
        logger.warning(f"Linear gain ramp hatası: {e}, sabit gain uygulanıyor")
        return segment.apply_gain(start_gain_db)

def apply_eased_gain_ramp(
    segment: AudioSegment,
    start_gain_db: float,
    end_gain_db: float,
    step_ms: int = None,
    curve: Literal["linear", "ease_in", "ease_out", "ease_in_out"] = "ease_in"
) -> AudioSegment:
    """
    Müzikal gain ramp uygular (easing eğrileri ile).
    
    Args:
        segment: İşlenecek ses segmenti
        start_gain_db: Başlangıç gain (dB)
        end_gain_db: Bitiş gain (dB)
        step_ms: Adım süresi (ms), None ise varsayılan kullanılır
        curve: Eğri tipi
            - 'linear': Doğrusal
            - 'ease_in': Yavaş başlar, hızlanır (bitiriş için ideal)
            - 'ease_out': Hızlı başlar, yavaşlar
            - 'ease_in_out': Yavaş-hızlı-yavaş (S-curve)
        
    Returns:
        İşlenmiş ses segmenti
    """
    if step_ms is None:
        step_ms = AnalysisConfig.GAIN_RAMP_STEP_MS
    
    try:
        if len(segment) == 0 or start_gain_db == end_gain_db:
            return segment.apply_gain(start_gain_db)
        
        total_ms = len(segment)
        steps = max(1, total_ms // step_ms)
        out = AudioSegment.silent(duration=0, frame_rate=segment.frame_rate)
        
        def map_t(t: float) -> float:
            """Eğri fonksiyonu"""
            if curve == "linear":
                return t
            if curve == "ease_out":
                return 1.0 - (1.0 - t) ** 2
            if curve == "ease_in_out":
                return 0.5 * (1 - np.cos(np.pi * t))
            # default: ease_in (yumuşak başlar, sonda hızlanır)
            return t ** 2
        
        for i in range(steps):
            seg_start = i * step_ms
            seg_end = total_ms if i == steps - 1 else (i + 1) * step_ms
            # Segmentin ortasına göre t
            t = (seg_start + seg_end) / 2.0 / max(1, total_ms)
            t = float(np.clip(map_t(t), 0.0, 1.0))
            current = start_gain_db + (end_gain_db - start_gain_db) * t
            out += segment[seg_start:seg_end].apply_gain(current)
        
        return out
    except Exception as e:
        logger.warning(f"Eased gain ramp hatası: {e}, sabit gain uygulanıyor")
        return segment.apply_gain(start_gain_db)

