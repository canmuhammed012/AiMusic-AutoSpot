"""Ses analizi modülü - spot tespiti ve segment analizi"""

from typing import List, Tuple
import logging
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from .effects import normalize_audio_in_memory
from ..constants import AnalysisConfig

logger = logging.getLogger(__name__)

def merge_close_segments(
    segments: List[Tuple[int, int]],
    max_gap: int = None
) -> List[Tuple[int, int]]:
    """
    Yakın segmentleri birleştirir (kısa sessizlikleri atlar).
    
    Args:
        segments: (başlangıç, bitiş) tuple'larının listesi (ms)
        max_gap: Birleştirme için maksimum boşluk (ms)
        
    Returns:
        Birleştirilmiş segmentler listesi
    """
    if max_gap is None:
        max_gap = AnalysisConfig.MAX_GAP_MS
    
    if not segments:
        return []
    
    sorted_segments = sorted(segments, key=lambda x: x[0])
    merged = []
    current_start, current_end = sorted_segments[0]
    
    for start, end in sorted_segments[1:]:
        if start - current_end <= max_gap:
            current_end = max(current_end, end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end
    
    merged.append((current_start, current_end))
    return merged

def analyze_audio_segments(audio_path: str, max_gap_ms: int = None) -> List[Tuple[int, int]]:
    """
    Ses dosyasından konuşma bölümlerini tespit eder.
    
    Args:
        audio_path: Analiz edilecek ses dosyasının yolu
        max_gap_ms: Segment birleştirme için maksimum boşluk (ms). None ise varsayılan değer kullanılır.
        
    Returns:
        Konuşma bölümlerinin (başlangıç, bitiş) tuple'larının listesi (milisaniye)
        
    Raises:
        FileNotFoundError: Dosya bulunamazsa
        Exception: Ses işleme hatası
    """
    try:
        logger.info(f"Ses analizi başlatılıyor: {audio_path}")
        
        # Ses dosyasını yükle
        ham_raw = AudioSegment.from_file(audio_path)
        
        # Normalize et
        ham = normalize_audio_in_memory(ham_raw)
        
        # Sessizlik tespiti
        ranges = detect_nonsilent(
            ham,
            min_silence_len=AnalysisConfig.MIN_SILENCE_LEN,
            silence_thresh=AnalysisConfig.SILENCE_THRESH
        )
        
        # Yakın segmentleri birleştir (max_gap_ms parametresi ile)
        merged_ranges = merge_close_segments(ranges, max_gap=max_gap_ms)
        
        # Minimum uzunluk filtresi
        min_length = AnalysisConfig.MIN_SEGMENT_LENGTH_MS
        valid_ranges = [
            (start, end) for start, end in merged_ranges
            if (end - start) >= min_length
        ]
        
        logger.info(f"Analiz tamamlandı: {len(valid_ranges)} spot bulundu")
        return valid_ranges
        
    except FileNotFoundError:
        logger.error(f"Dosya bulunamadı: {audio_path}")
        raise
    except Exception as e:
        logger.error(f"Ses analizi hatası ({audio_path}): {e}", exc_info=True)
        raise

