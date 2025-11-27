"""Ana ses montaj işlemcisi"""

import os
import math
import logging
from typing import List, Tuple, Optional, Callable, Dict
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize

from .analyzer import analyze_audio_segments
from .effects import normalize_audio_in_memory, apply_eased_gain_ramp
from .mixer import find_musical_outro_point
from ..constants import (
    AudioConfig, AudioLevels, CompressorConfig, AnalysisConfig
)

logger = logging.getLogger(__name__)

def ses_montaj(
    ham_path: str,
    output_dir: str,
    output_format: str,
    fon_path: Optional[str] = None,
    merged_ranges: Optional[List[Tuple[int, int]]] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    is_cancelled: Callable[[], bool] = lambda: False,
    advanced_settings: Optional[Dict[str, float]] = None,
    start_fon_db: Optional[float] = None,
    ducked_fon_db: Optional[float] = None,
    mid_fon_db: Optional[float] = None,
    voice_db: Optional[float] = None,
    intro_duration: Optional[int] = None,
    outro_rise_duration: Optional[int] = None,
    outro_fall_duration: Optional[int] = None,
    spot_index_offset: int = 0,
    ending_path: Optional[str] = None
) -> List[str]:
    """
    Ana ses montaj fonksiyonu.
    
    Ham ses dosyasından spotları tespit eder, fon müziği ekler ve
    profesyonel montajlı çıktılar üretir.
    
    Args:
        ham_path: Ham ses dosyası yolu
        output_dir: Çıktı klasörü
        output_format: Çıktı formatı ("wav" veya "mp3")
        fon_path: Fon müziği dosya yolu
        merged_ranges: Önceden analiz edilmiş segmentler (opsiyonel)
        progress_callback: İlerleme callback fonksiyonu (progress, message)
        is_cancelled: İptal kontrolü fonksiyonu
        start_fon_db: Fon başlangıç seviyesi (dB, opsiyonel)
        ducked_fon_db: Ducking seviyesi (dB, opsiyonel)
        mid_fon_db: Orta seviye (dB, opsiyonel)
        voice_db: Ses seviyesi (dB, opsiyonel)
        intro_duration: Intro süresi (ms, opsiyonel)
        outro_rise_duration: Outro yükseliş süresi (ms, opsiyonel)
        outro_fall_duration: Outro düşüş süresi (ms, opsiyonel)
        spot_index_offset: Spot index offset (dosya isimlendirme için, varsayılan: 0)
        ending_path: Bitiş sesi dosya yolu (opsiyonel, seçilirse ham ses bitimiyle fon bitimi aynı ana getirilir ve bitiş eklenir)
        
    Returns:
        Oluşturulan dosya yollarının listesi
        
    Raises:
        Exception: Montaj sırasında hata oluşursa
    """
    try:
        logger.info(f"Montaj başlatılıyor: {ham_path}")
        
        # Gelişmiş ayarları kullan veya parametreleri kontrol et
        if advanced_settings:
            intro_duration_val = int(advanced_settings.get("intro_duration", AudioConfig.INTRO_DURATION_MS))
            outro_rise_duration_val = int(advanced_settings.get("outro_rise", AudioConfig.OUTRO_RISE_DURATION_MS))
            outro_fall_duration_val = int(advanced_settings.get("outro_fall", AudioConfig.OUTRO_FALL_DURATION_MS))
            start_fon_db_val = float(advanced_settings.get("start_fon_db", AudioLevels.START_FON_DB))
            ducked_fon_db_val = float(advanced_settings.get("ducked_fon_db", AudioLevels.DUCKED_FON_DB))
            mid_fon_db_val = float(advanced_settings.get("mid_fon_db", AudioLevels.MID_FON_DB))
            voice_db_val = float(advanced_settings.get("voice_db", AudioLevels.VOICE_DB))
            max_gap_ms_val = int(advanced_settings.get("max_gap_ms", AnalysisConfig.MAX_GAP_MS))
        else:
            # Parametrelerden al veya varsayılanları kullan
            intro_duration_val = int(intro_duration) if intro_duration is not None else AudioConfig.INTRO_DURATION_MS
            outro_rise_duration_val = int(outro_rise_duration) if outro_rise_duration is not None else AudioConfig.OUTRO_RISE_DURATION_MS
            outro_fall_duration_val = int(outro_fall_duration) if outro_fall_duration is not None else AudioConfig.OUTRO_FALL_DURATION_MS
            start_fon_db_val = float(start_fon_db) if start_fon_db is not None else AudioLevels.START_FON_DB
            ducked_fon_db_val = float(ducked_fon_db) if ducked_fon_db is not None else AudioLevels.DUCKED_FON_DB
            mid_fon_db_val = float(mid_fon_db) if mid_fon_db is not None else AudioLevels.MID_FON_DB
            voice_db_val = float(voice_db) if voice_db is not None else AudioLevels.VOICE_DB
            max_gap_ms_val = AnalysisConfig.MAX_GAP_MS
        
        # Yerel değişkenlere atama (kodun geri kalanında kullanım için)
        intro_duration = intro_duration_val
        outro_rise_duration = outro_rise_duration_val
        outro_fall_duration = outro_fall_duration_val
        start_fon_db = start_fon_db_val
        ducked_fon_db = ducked_fon_db_val
        mid_fon_db = mid_fon_db_val
        voice_db = voice_db_val
        silence_gap_ms = AudioConfig.SILENCE_GAP_MS
        peak_headroom_db = AudioLevels.PEAK_HEADROOM_DB
        
        # Ses dosyalarını yükle
        logger.debug("Ses dosyaları yükleniyor...")
        ham_raw = AudioSegment.from_file(ham_path)
        fon_raw = AudioSegment.from_file(fon_path) if fon_path else None
        
        if fon_raw is None:
            raise ValueError("Fon müziği dosyası belirtilmedi")
        
        # Frame rate uyumluluğu - önemli!
        # Tüm sesler aynı frame rate'de olmalı (senkronizasyon için)
        target_frame_rate = 44100  # Profesyonel kalite
        
        if ham_raw.frame_rate != target_frame_rate:
            logger.debug(f"Ham ses frame rate dönüştürülüyor: {ham_raw.frame_rate} -> {target_frame_rate}")
            ham_raw = ham_raw.set_frame_rate(target_frame_rate)
        
        if fon_raw.frame_rate != target_frame_rate:
            logger.debug(f"Fon müziği frame rate dönüştürülüyor: {fon_raw.frame_rate} -> {target_frame_rate}")
            fon_raw = fon_raw.set_frame_rate(target_frame_rate)
        
        # Channels uyumluluğu (mono'ya çevir, daha stabil)
        if ham_raw.channels != 1:
            logger.debug(f"Ham ses mono'ya dönüştürülüyor: {ham_raw.channels} kanal")
            ham_raw = ham_raw.set_channels(1)
        
        if fon_raw.channels != 1:
            logger.debug(f"Fon müziği mono'ya dönüştürülüyor: {fon_raw.channels} kanal")
            fon_raw = fon_raw.set_channels(1)
        
        # Normalize et (sadece gerektiğinde - hız optimizasyonu)
        # Ham ses için normalize kontrolü
        if ham_raw.max_dBFS < -0.5:  # Eğer çok düşükse normalize et
            ham = normalize_audio_in_memory(ham_raw)
        else:
            ham = ham_raw  # Normalize etme (hız artışı)
        
        # Fon müziği için normalize kontrolü
        if fon_raw.max_dBFS < -0.5:  # Eğer çok düşükse normalize et
            fon = normalize_audio_in_memory(fon_raw)
        else:
            fon = fon_raw  # Normalize etme (hız artışı)
        
        # Frame rate kontrolü (normalize sonrası)
        if ham.frame_rate != fon.frame_rate:
            logger.warning(f"Frame rate uyumsuzluğu: ham={ham.frame_rate}, fon={fon.frame_rate}")
            # Fon'u ham'in frame rate'ine uyarla
            fon = fon.set_frame_rate(ham.frame_rate)
        
        # Segment analizi
        if not merged_ranges:
            logger.debug("Ses analizi yapılıyor...")
            merged_ranges = analyze_audio_segments(ham_path, max_gap_ms=max_gap_ms_val)
        
        if not merged_ranges:
            raise ValueError("Analiz sonucu konuşma bölümü bulunamadı")
        
        # Minimum uzunluk filtresi
        min_length = AnalysisConfig.MIN_SEGMENT_LENGTH_MS
        valid_segments = [
            seg for seg in merged_ranges
            if (seg[1] - seg[0]) >= min_length
        ]
        
        if not valid_segments:
            raise ValueError(f"Geçerli uzunlukta spot bulunamadı (minimum {min_length}ms)")
        
        out_files = []
        total_segments = len(valid_segments)
        logger.info(f"{total_segments} spot işlenecek")
        
        # Her segment için montaj
        for idx, (start, end) in enumerate(valid_segments, 1):
            if is_cancelled():
                logger.info("Montaj kullanıcı tarafından iptal edildi")
                return []
            
            if progress_callback:
                progress = int((idx / total_segments) * 95)
                progress_callback(progress, f"Bölüm {idx}/{total_segments} işleniyor...")
            
            logger.debug(f"Spot {idx}/{total_segments} işleniyor: {start}ms - {end}ms")
            
            # Ham ses segmenti
            ham_segment = ham[start:end]
            base_len = intro_duration + len(ham_segment)
            
            # Müzikal bitiş noktası
            if ending_path:
                # Bitiş seçilmişse: Ham ses bitiminde fon sesini kes
                outro_target_ms = intro_duration + len(ham_segment)
                total_needed = outro_target_ms
            else:
                # Bitiş seçilmemişse: Normal müzikal bitiş
                outro_target_ms = find_musical_outro_point(fon_path, base_len)
                total_needed = int(outro_target_ms) + outro_fall_duration
            
            # Fon müziğini uzat (gerekirse)
            if len(fon) < total_needed:
                repeat_count = math.ceil(total_needed / len(fon))
                fon_extended = fon * repeat_count
            else:
                fon_extended = fon
            
            # === INTRO ===
            # Ham ses seviyesi (VOICE_DB) → %35 seviyesi giriş fade-out (ease_out: hızlı başlar, yavaşlar)
            raw_intro = fon_extended[:intro_duration]
            intro_fon = apply_eased_gain_ramp(
                raw_intro,
                start_fon_db,  # Ham ses seviyesi ile aynı (VOICE_DB = -3.0 dB)
                ducked_fon_db,  # %35 seviyesi (-10.2 dB)
                curve="ease_out"
            )
            
            # === BODY ===
            # Ham ses boyunca sabit %35 seviyesi
            body_fon = fon_extended[
                intro_duration:intro_duration + len(ham_segment)
            ].apply_gain(ducked_fon_db)
            
            # === OUTRO ===
            outro_start = intro_duration + len(ham_segment)
            
            if ending_path:
                # Bitiş seçilmişse: Ham ses bitimiyle fon ses bitimini aynı ana getir
                # Fon sesini ham ses bitiminde kes (fade-out yok)
                outro_down = AudioSegment.silent(duration=0, frame_rate=fon.frame_rate)
                
                # Bitiş dosyasını yükle ve hazırla
                ending_raw = AudioSegment.from_file(ending_path)
                
                # Frame rate uyumluluğu (target_frame_rate fonksiyon başında tanımlı)
                if ending_raw.frame_rate != target_frame_rate:
                    ending_raw = ending_raw.set_frame_rate(target_frame_rate)
                
                # Channels uyumluluğu
                if ending_raw.channels != 1:
                    ending_raw = ending_raw.set_channels(1)
                
                # Normalize et
                ending_segment = normalize_audio_in_memory(ending_raw)
                
                # Bitiş sesini ham ses seviyesine indir (voice_db seviyesi)
                # Normalize edilmiş bitiş (-0.1 dB) → ham ses seviyesi (voice_db)
                ending_segment = ending_segment.apply_gain(voice_db - (-0.1))
                logger.debug(f"Bitiş sesi seviyesi ayarlandı: {voice_db:.2f} dB (ham ses ile aynı)")
            else:
                # Bitiş seçilmemişse: Normal fon müziği bitişi
                outro_total_end = int(outro_target_ms)  # Toplam outro bitiş noktası (fon müziğinin başından itibaren)
                
                # Minimum outro body kontrolü
                if outro_total_end - outro_start < AudioConfig.MIN_OUTRO_BODY_MS:
                    outro_total_end = outro_start + AudioConfig.MIN_OUTRO_BODY_MS
                
                # Fade-out direkt ham ses bitiminden başlamalı (geriye dönme yok)
                # outro_start'ten başla, outro_total_end'e kadar fade-out yap
                actual_fade_start = outro_start  # Ham ses bitimi = fade-out başlangıcı
                
                # Fade-out için yeterli ses var mı kontrol et
                available_audio = len(fon_extended) - actual_fade_start
                # Fade-out süresi: outro_total_end'e kadar veya mevcut ses kadar
                fade_out_end = min(outro_total_end, len(fon_extended))
                actual_fall_duration = fade_out_end - actual_fade_start
                
                if actual_fall_duration > 100:  # Minimum 100ms fade-out
                    raw_outro_fall = fon_extended[
                        actual_fade_start:fade_out_end
                    ]
                    
                    # %35 (ducked_fon_db) → %0 (sessizlik), yumuşak bitiş (ease_in)
                    # Ham ses bitimindeki seviyeden direkt fade-out
                    outro_down = apply_eased_gain_ramp(
                        raw_outro_fall,
                        ducked_fon_db,  # %35 seviyesi (ham ses boyunca olan seviye)
                        AudioLevels.SILENCE_DB,  # %0 seviyesi
                        curve="ease_in"
                    )
                else:
                    # Yeterli ses yoksa, mevcut sesi fade-out yap
                    if available_audio > 0:
                        raw_outro_fall = fon_extended[actual_fade_start:]
                        # %35'den başlayarak fade-out uygula
                        outro_down = apply_eased_gain_ramp(
                            raw_outro_fall,
                            ducked_fon_db,  # %35 seviyesi
                            AudioLevels.SILENCE_DB,  # %0 seviyesi
                            curve="ease_in"
                        )
                    else:
                        # Hiç ses yoksa sessizlik ekle
                        outro_down = AudioSegment.silent(
                            duration=outro_fall_duration,
                            frame_rate=fon.frame_rate
                        )
                
                ending_segment = None
            
            # === KOMPOZİSYON ===
            # Tüm segmentlerin frame rate'ini uyumlu hale getir (optimize edilmiş)
            target_frame_rate = intro_fon.frame_rate
            
            # Frame rate dönüşümlerini sadece gerektiğinde yap (hız optimizasyonu)
            if body_fon.frame_rate != target_frame_rate:
                body_fon = body_fon.set_frame_rate(target_frame_rate)
            if outro_down.frame_rate != target_frame_rate:
                outro_down = outro_down.set_frame_rate(target_frame_rate)
            
            # Fon müziği arka planını oluştur (kompresör henüz uygulanmayacak)
            prelim_background = (
                intro_fon
                .append(body_fon, crossfade=0)
            )
            
            # Frame rate kontrolü (append sonrası - genelde aynı kalır, kontrol et)
            if prelim_background.frame_rate != target_frame_rate:
                prelim_background = prelim_background.set_frame_rate(target_frame_rate)
            
            # Fade-out kısmı ekle (veya bitiş ekleme)
            if ending_path and ending_segment:
                # Bitiş seçilmişse: Fon sesini ham ses bitiminde kes, ardına bitişi ekle
                # Fon sesini ham ses bitimine kadar kullan (fade-out yok)
                final_background = prelim_background
                # Bitişi ekle
                if ending_segment.frame_rate != final_background.frame_rate:
                    ending_segment = ending_segment.set_frame_rate(final_background.frame_rate)
                final_background = final_background.append(ending_segment, crossfade=0)
            else:
                # Bitiş seçilmemişse: Normal fade-out
                final_background = (
                    prelim_background
                    .append(outro_down, crossfade=0)
                )
            
            # Frame rate final kontrolü ve ham ses uyumu
            if final_background.frame_rate != ham_segment.frame_rate:
                logger.debug(f"Frame rate uyumluluğu: final_background={final_background.frame_rate}, ham={ham_segment.frame_rate}")
                # Ham'i final_background'in frame rate'ine uyarla
                ham_segment = ham_segment.set_frame_rate(final_background.frame_rate)
            
            # Konuşma bindirme (frame rate uyumlu)
            final_voice = ham_segment.apply_gain(voice_db)
            
            # Overlay işlemi - timing kontrolü (sample-perfect alignment)
            overlay_position = intro_duration
            
            # Pozisyonu frame rate'e göre ayarla (tam sample'a hizala - kayma önleme)
            sample_rate = final_background.frame_rate
            samples_per_ms = sample_rate / 1000.0
            overlay_position_samples = int(overlay_position * samples_per_ms)
            overlay_position_ms = overlay_position_samples / samples_per_ms
            
            logger.debug(f"Overlay pozisyonu: {overlay_position_ms}ms (frame_rate: {sample_rate})")
            
            # Overlay - crossfade yok, kesin timing
            final_result = final_background.overlay(
                final_voice,
                position=int(overlay_position_ms),
                gain_during_overlay=0  # Overlay sırasında background gain değişmez
            )
            
            # === KOMPRESÖR ===
            # Ham ses ve fon sesin üst üste geldiği final sonuç üzerinde kompresör uygula
            # Bu sayede ham ses ve fon sesin birleştiği kısım analiz edilir ve kompresör uygulanır
            try:
                peak_before = final_result.max_dBFS
                if peak_before < CompressorConfig.THRESHOLD + 5:  # Threshold'a yakınsa kompresör atla
                    logger.debug(f"Kompresör atlandı (peak zaten uygun: {peak_before:.2f} dB)")
                else:
                    logger.debug(f"Kompresör uygulanıyor (ham ses + fon ses birleşimi): peak={peak_before:.2f} dB")
                    final_result = compress_dynamic_range(
                        final_result,
                        threshold=CompressorConfig.THRESHOLD,
                        ratio=CompressorConfig.RATIO,
                        attack=CompressorConfig.ATTACK,
                        release=CompressorConfig.RELEASE
                    )
                    peak_after = final_result.max_dBFS
                    logger.debug(f"Kompresör tamamlandı: {peak_before:.2f} dB -> {peak_after:.2f} dB")
            except Exception as e:
                logger.warning(f"Kompresör hatası, devam ediliyor: {e}")
            
            # === MASTERING ===
            # 1. Peak sınırlama (clipping önleme)
            peak = getattr(final_result, "max_dBFS", None)
            if peak is not None and peak > peak_headroom_db:
                gain_reduction = peak_headroom_db - peak
                final_result = final_result.apply_gain(gain_reduction)
                logger.debug(f"Peak sınırlama uygulandı: {peak:.2f} dB -> {final_result.max_dBFS:.2f} dB")
            
            # 2. Dinamik aralık normalizasyonu (pürüzsüz çıkış için)
            # Optimize edilmiş: Sadece gerekli durumlarda normalize et
            try:
                current_peak = final_result.max_dBFS
                # Eğer peak zaten uygun aralıktaysa normalize etme (hız artışı)
                if current_peak < -0.3 or current_peak > 0.0:
                    # Önce normalize et (peak normalizasyonu)
                    final_result = normalize(final_result)
                    
                    # Sonra hafif bir soft limiting uygula (pürüzsüz geçişler için)
                    # Peak'i -0.3 dB'e sınırla (clipping önleme + headroom)
                    current_peak = final_result.max_dBFS
                    if current_peak > -0.3:
                        final_result = final_result.apply_gain(-0.3 - current_peak)
                        logger.debug(f"Soft limiting uygulandı: {current_peak:.2f} dB -> {final_result.max_dBFS:.2f} dB")
                else:
                    logger.debug(f"Normalizasyon atlandı (peak zaten uygun: {current_peak:.2f} dB)")
            except Exception as e:
                logger.warning(f"Mastering hatası, devam ediliyor: {e}")
            
            # === KAYIT ===
            ham_name = os.path.splitext(os.path.basename(ham_path))[0]
            # Spot index'i offset ile ayarla (birden fazla spot için doğru numaralandırma)
            spot_num = idx + spot_index_offset
            out_name = f"{ham_name} {spot_num}.{output_format}"
            out_path = os.path.join(output_dir, out_name)
            
            # Eski dosyayı sil
            if os.path.exists(out_path):
                try:
                    os.remove(out_path)
                except Exception as e:
                    logger.warning(f"Eski dosya silinemedi: {e}")
            
            # Export - optimize edilmiş parametreler (hız + kalite dengesi)
            # Not: -nostdin ve -loglevel quiet otomatik olarak patch tarafından ekleniyor
            if output_format.lower() == "mp3":
                final_result.export(
                    out_path,
                    format=output_format,
                    bitrate="320k",
                    parameters=[
                        "-q:a", "0",  # En yüksek kalite
                        "-threads", "0"  # Tüm CPU çekirdeklerini kullan
                    ]
                )
            else:
                # WAV için optimize edilmiş parametreler
                final_result.export(
                    out_path,
                    format=output_format,
                    parameters=[
                        "-acodec", "pcm_s24le",  # 24-bit PCM (yüksek kalite)
                        "-threads", "0"  # Tüm CPU çekirdeklerini kullan
                    ]
                )
            
            out_files.append(out_path)
            logger.debug(f"Spot kaydedildi: {out_path}")
        
        if progress_callback:
            progress_callback(100, "Montaj tamamlandı!")
        
        logger.info(f"Montaj tamamlandı: {len(out_files)} dosya oluşturuldu")
        return out_files
        
    except Exception as e:
        logger.error(f"Ses montajı sırasında hata: {e}", exc_info=True)
        raise

