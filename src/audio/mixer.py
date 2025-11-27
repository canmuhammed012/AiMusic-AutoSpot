"""Müzikal bitiş noktası tespiti"""

import logging
import librosa
import numpy as np
from typing import Optional

from ..constants import AnalysisConfig

logger = logging.getLogger(__name__)

def find_musical_outro_point(
    fon_path: str,
    start_point_ms: float,
    sr: int = None
) -> float:
    """
    Geliştirilmiş müzikal bitiş noktası tespiti.
    
    Beat (BPM) ve düşük enerji (RMS) analizi kullanarak
    konuşma bitiminden sonra en uygun bitiş noktasını bulur.
    
    Args:
        fon_path: Fon müziği dosya yolu
        start_point_ms: Konuşma bitiş noktası (ms)
        sr: Sample rate (None ise varsayılan kullanılır)
        
    Returns:
        Önerilen bitiş noktası (ms)
    """
    if sr is None:
        sr = AnalysisConfig.SAMPLE_RATE
    
    try:
        logger.debug(f"Müzikal bitiş analizi: {fon_path}, başlangıç: {start_point_ms}ms")
        
        # Ses dosyasını yükle
        y, sr = librosa.load(fon_path, sr=sr, mono=True)
        duration_ms = len(y) / sr * 1000.0
        
        # Beat analizi
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beats, sr=sr) * 1000.0  # ms
        
        # Enerji (RMS) analizi
        frame_length = AnalysisConfig.FRAME_LENGTH
        hop_length = AnalysisConfig.HOP_LENGTH
        rms = librosa.feature.rms(
            y=y,
            frame_length=frame_length,
            hop_length=hop_length,
            center=True
        )[0]
        rms_times = librosa.frames_to_time(
            np.arange(len(rms)),
            sr=sr,
            hop_length=hop_length
        ) * 1000.0
        
        # Düşük enerji eşiği: medyanın %70'i
        thr = float(np.median(rms) * AnalysisConfig.RMS_THRESHOLD_RATIO)
        low_energy_times = rms_times[rms < thr]
        
        # Konuşma bitimi + minimum tutma süresi
        min_hold_ms = AnalysisConfig.MIN_HOLD_MS
        target_start = start_point_ms + min_hold_ms
        
        # Adaylar: target_start sonrasındaki beat'ler + düşük enerji anları
        candidates = sorted(set([
            t for t in np.concatenate((beat_times, low_energy_times))
            if t > target_start
        ]))
        
        if not candidates:
            # Aday yoksa: güvenli fallback
            fallback = min(duration_ms, target_start + AnalysisConfig.FALLBACK_OUTRO_MS)
            logger.debug(f"Aday bulunamadı, fallback kullanılıyor: {fallback}ms")
            return fallback
        
        first = candidates[0]
        
        # 1 ölçü süresi (4 beat) tahmini
        if len(beat_times) > 4:
            one_measure = float(np.median(np.diff(beat_times)) * 4.0)
        else:
            # Tempo bilgisi yoksa ölçüyü varsayılan değerle
            one_measure = AnalysisConfig.ONE_MEASURE_FALLBACK_MS
        
        outro_point = first + one_measure
        # Müziğin sonunu aşma
        outro_point = min(outro_point, duration_ms)
        
        # Eğer outro_point, target_start'tan toplamda çok kısa kalıyorsa biraz daha uzat
        if outro_point - start_point_ms < AnalysisConfig.MIN_TOTAL_OUTRO_MS:
            outro_point = min(duration_ms, start_point_ms + AnalysisConfig.FALLBACK_OUTRO_MS)
        
        logger.debug(f"Müzikal bitiş noktası bulundu: {outro_point}ms")
        return float(outro_point)
        
    except Exception as e:
        logger.warning(f"Müzikal bitiş analizi başarısız: {e}, fallback kullanılıyor")
        # En az 7 sn sonrasına koy
        return float(start_point_ms + AnalysisConfig.FALLBACK_OUTRO_MS)

