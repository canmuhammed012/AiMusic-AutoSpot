"""Ana pencere - modern animasyonlu GUI"""

import os
import sys
import threading
import random
import json
import time
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
from typing import List, Optional, Dict, Tuple
import logging

from ..constants import (
    APP_NAME, APP_VERSION, FONT_FAMILY, UIConfig,
    AUDIO_FILE_TYPES, PRESET_CATEGORIES, ENDING_CATEGORIES
)
from ..utils import (
    get_resource_path, format_path_display, validate_audio_file,
    ConfigManager, detect_and_set_ffmpeg
)
from ..audio import analyze_audio_segments, ses_montaj
from .components.step_card import StepCard
from .components.control_panel import ControlPanel
from .components.preset_browser import PresetBrowser
from .components.progress_modal import ProgressModal
from .components.update_modal import UpdateModal
from ..utils.updater import check_for_updates

logger = logging.getLogger(__name__)

class MainWindow(ctk.CTk):
    """Ana uygulama penceresi"""
    
    def __init__(self):
        """MainWindow başlatır"""
        super().__init__()
        
        # Veri yapıları
        self.ham_paths: List[str] = []
        self.fon_paths: List[str] = []
        self.ending_paths: List[str] = []  # Bitiş sesleri
        self.output_path: Optional[str] = None
        self.analyzed_segments_map: Dict[str, List[Tuple[int, int]]] = {}
        self.analysis_done = False
        self.is_cancelled = False
        
        # UI referansları
        self.icons: Dict[str, ctk.CTkImage] = {}
        self.step_cards: Dict[str, StepCard] = {}
        self.control_panel: Optional[ControlPanel] = None
        
        # Yapılandırma
        self.config = ConfigManager()
        
        # FFmpeg kurulumu
        try:
            detect_and_set_ffmpeg()
        except Exception as e:
            messagebox.showerror("Kritik Hata", f"FFmpeg başlatılamadı:\n\n{e}")
            self.destroy()
            return
        
        # UI kurulumu
        self._setup_window()
        self._load_icons()
        self._setup_gui()
        self.update_idletasks()
    
    def _setup_window(self):
        """Pencere ayarlarını yapar"""
        self.title(f"{APP_NAME} v{APP_VERSION}")
        
        # Pencere boyutu
        width = self.config.get("window_geometry.width", UIConfig.WINDOW_WIDTH)
        height = self.config.get("window_geometry.height", UIConfig.WINDOW_HEIGHT)
        self.geometry(f"{width}x{height}")
        self.minsize(UIConfig.MIN_WINDOW_WIDTH, UIConfig.MIN_WINDOW_HEIGHT)
        
        # Arka plan rengi
        self.configure(fg_color=("#F0F2F5", "#202124"))
        
        # İkon
        try:
            ico_path = get_resource_path("img/ico/1-1-logo.ico")
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
        except Exception as e:
            logger.warning(f"İkon yüklenemedi: {e}")
        
        # Kapatma handler'ı
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _load_icons(self):
        """İkonları yükler"""
        try:
            # Ana logo
            light_logo_path = get_resource_path("img/logo/aimusiclogo2.png")
            dark_logo_path = get_resource_path("img/logo/aimusiclogo3.png")
            
            if os.path.exists(light_logo_path) and os.path.exists(dark_logo_path):
                light_logo_img = Image.open(light_logo_path)
                dark_logo_img = Image.open(dark_logo_path)
                
                if light_logo_img.size != dark_logo_img.size:
                    dark_logo_img = dark_logo_img.resize(
                        light_logo_img.size,
                        Image.Resampling.LANCZOS
                    )
                
                original_width, original_height = light_logo_img.size
                new_width = 320
                new_height = int(new_width * (original_height / original_width))
                
                self.icons["main_logo"] = ctk.CTkImage(
                    light_image=light_logo_img,
                    dark_image=dark_logo_img,
                    size=(new_width, new_height)
                )
        except Exception as e:
            logger.warning(f"Logo yüklenemedi: {e}")
        
        # Diğer ikonlar
        icon_data = {
            "mic": ("img/ico/mic.png", "img/ico/mic2.png"),
            "music": ("img/ico/music.png", "img/ico/music2.png"),
            "folder": ("img/ico/folder.png", "img/ico/folder2.png"),
        }
        
        for name, (light_path, dark_path) in icon_data.items():
            try:
                light_img = Image.open(get_resource_path(light_path))
                dark_img = Image.open(get_resource_path(dark_path))
                self.icons[name] = ctk.CTkImage(
                    light_image=light_img,
                    dark_image=dark_img,
                    size=(24, 24)
                )
            except Exception as e:
                logger.warning(f"İkon yüklenemedi: {name} - {e}")
    
    def _setup_gui(self):
        """GUI elemanlarını oluşturur"""
        # Ana container
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=25, pady=15)
        
        # Header
        self._create_header(main_container)
        
        # İçerik frame
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=(15, 0))
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=0)
        
        # Sol panel (workflow)
        workflow_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        workflow_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Sağ panel (kontrol) - sol panelin bitişine hizalı
        right_panel = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nw", padx=(10, 0))
        
        # Adım kartları
        self._create_step_cards(workflow_container)
        
        # Kontrol paneli
        self.control_panel = ControlPanel(
            right_panel,
            on_theme_change=self._on_theme_change,
            on_format_change=self._on_format_change,
            on_start=self._start_montaj,
            on_cancel=self._cancel_montaj,
            on_advanced=self._open_advanced_settings,
            on_check_updates=self._check_for_updates
        )
        self.control_panel.pack(fill="both", expand=True)
        
        # Footer
        footer_label = ctk.CTkLabel(
            main_container,
            text="© 2025 Kavartkurt A.Ş. All Rights Reserved.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color="gray60"
        )
        footer_label.pack(side="bottom", pady=(10, 0))
        
        # Ayarları yükle (control_panel oluşturulduktan sonra)
        self._load_settings()
        
        # Gelişmiş ayarlar değişkeni
        self.advanced_settings = {}
        
        # Uygulama başlangıcında otomatik güncelleme kontrolü (5 saniye sonra)
        self.after(5000, self._auto_check_updates)
    
    def _open_advanced_settings(self):
        """Gelişmiş ayarlar penceresini açar"""
        from .components.advanced_settings import AdvancedSettings
        
        current_settings = self.advanced_settings.copy() if self.advanced_settings else {
            "start_fon_db": -1.94,
            "ducked_fon_db": -10.46,
            "mid_fon_db": -3.10,
            "voice_db": -0.91,
            "intro_duration": 3000,
            "outro_rise": 2000,
            "outro_fall": 3000,
            "max_gap_ms": 1400
        }
        
        def on_save(settings):
            """Ayarları kaydet"""
            self.advanced_settings = settings
            logger.info(f"Gelişmiş ayarlar kaydedildi: {settings}")
            # Config'e kaydet
            self.config.set("advanced_settings", settings)
            self.config.save()
        
        AdvancedSettings(self, current_settings, on_save)
    
    def _create_header(self, parent):
        """Header oluşturur"""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x")
        
        if self.icons.get("main_logo"):
            ctk.CTkLabel(
                header_frame,
                image=self.icons["main_logo"],
                text=""
            ).pack(pady=(0, 5))
        
        ctk.CTkLabel(
            header_frame,
            text="Otomatik Spot Montajlayıcı",
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
            text_color=("#333", "#EEE")
        ).pack(pady=(5, 0))
    
    def _create_step_cards(self, parent):
        """Adım kartlarını oluşturur"""
        # 1. Ham Ses
        ham_card = StepCard(
            parent,
            title="1. Ham Ses Kaydı",
            description="İçinde spotların bulunduğu ham ses kaydını seçin. Birden fazla dosya seçebilirsiniz.",
            btn_text="📁 Dosya Seç",
            command=lambda: self._select_file("ham"),
            icon=self.icons.get("mic")
        )
        ham_card.pack(fill="x", pady=10)
        self.step_cards["ham"] = ham_card
        
        # 2. Fon Müziği
        fon_card = StepCard(
            parent,
            title="2. Fon Müziği",
            description="Spotların arkasında çalacak olan müziği seçin. Katalogdan hazır müzikler de seçebilirsiniz.",
            btn_text="📁 Dosya Seç",
            command=lambda: self._select_file("fon"),
            icon=self.icons.get("music"),
            extra_button={
                "text": "🎵 Katalogdan Seç",
                "command": self._open_preset_browser
            }
        )
        fon_card.pack(fill="x", pady=10)
        self.step_cards["fon"] = fon_card
        
        # 3. Bitiş Ekle
        ending_card = StepCard(
            parent,
            title="3. Bitiş Ekle",
            description="Spotların sonuna eklenecek bitiş sesini seçin. Seçmezseniz fon müziğinin normal bitişi kullanılır.",
            btn_text="📁 Dosya Seç",
            command=lambda: self._select_file("ending"),
            icon=self.icons.get("music"),
            extra_button={
                "text": "🎵 Katalogdan Seç",
                "command": self._open_ending_browser
            }
        )
        ending_card.pack(fill="x", pady=10)
        self.step_cards["ending"] = ending_card
        
        # 4. Çıktı Klasörü
        output_card = StepCard(
            parent,
            title="4. Kayıt Klasörü",
            description="Oluşturulan spotların kaydedileceği klasörü seçin. Seçmezseniz varsayılan klasör kullanılır.",
            btn_text="📂 Klasör Seç",
            command=self._select_output_folder,
            icon=self.icons.get("folder")
        )
        output_card.pack(fill="x", pady=10)
        self.step_cards["output"] = output_card
    
    def _select_file(self, file_type: str):
        """Dosya seçim dialogu"""
        if file_type == "ham":
            paths = filedialog.askopenfilenames(
                title="Ham ses dosyası seç (çoklu)",
                filetypes=AUDIO_FILE_TYPES
            )
            if paths:
                # Dosya validasyonu
                valid_paths = []
                for path in paths:
                    is_valid, error = validate_audio_file(path)
                    if is_valid:
                        valid_paths.append(path)
                    else:
                        messagebox.showwarning(
                            "Geçersiz Dosya",
                            f"{os.path.basename(path)}: {error}"
                        )
                
                if valid_paths:
                    self.ham_paths = valid_paths
                    self.analyzed_segments_map = {}
                    self.analysis_done = False
                    
                    # UI güncelle
                    if len(self.ham_paths) > 1:
                        label_text = f"{len(self.ham_paths)} dosya seçildi"
                    else:
                        label_text = format_path_display(self.ham_paths[0])
                    
                    self.step_cards["ham"].update_path(label_text)
                    self.step_cards["ham"].update_analysis("Analiz ediliyor...", "gray")
                    
                    # Arka planda analiz
                    self._run_analysis_in_background(self.ham_paths)
        elif file_type == "fon":
            # Fon müziği seçimi
            if not self.ham_paths or not self.analysis_done:
                messagebox.showwarning(
                    "Bilgi",
                    "Öncelikle Ham Ses Dosyanızı Seçmelisiniz!"
                )
                return
            
            paths = filedialog.askopenfilenames(
                title="Fon müziği seç (çoklu)",
                filetypes=AUDIO_FILE_TYPES
            )
            if paths:
                # Dosya validasyonu
                valid_paths = []
                for path in paths:
                    is_valid, error = validate_audio_file(path)
                    if is_valid:
                        valid_paths.append(path)
                    else:
                        messagebox.showwarning(
                            "Geçersiz Dosya",
                            f"{os.path.basename(path)}: {error}"
                        )
                
                if valid_paths:
                    # Tek spot kuralı
                    total_spots = sum(
                        len(v) for v in self.analyzed_segments_map.values()
                    ) if self.analyzed_segments_map else 0
                    
                    if total_spots == 1 and len(valid_paths) > 1:
                        valid_paths = [valid_paths[0]]
                    
                    self.fon_paths = valid_paths
                    
                    # UI güncelle
                    if len(self.fon_paths) > 1:
                        label_text = f"{len(self.fon_paths)} dosya seçildi"
                    else:
                        label_text = format_path_display(self.fon_paths[0])
                    
                    self.step_cards["fon"].update_path(label_text)
        elif file_type == "ending":
            # Bitiş seçimi
            if not self.ham_paths or not self.analysis_done:
                messagebox.showwarning(
                    "Bilgi",
                    "Öncelikle Ham Ses Dosyanızı Seçmelisiniz!"
                )
                return
            
            paths = filedialog.askopenfilenames(
                title="Bitiş sesi seç (çoklu)",
                filetypes=AUDIO_FILE_TYPES
            )
            if paths:
                # Dosya validasyonu
                valid_paths = []
                for path in paths:
                    is_valid, error = validate_audio_file(path)
                    if is_valid:
                        valid_paths.append(path)
                    else:
                        messagebox.showwarning(
                            "Geçersiz Dosya",
                            f"{os.path.basename(path)}: {error}"
                        )
                
                if valid_paths:
                    # Tek spot kuralı
                    total_spots = sum(
                        len(v) for v in self.analyzed_segments_map.values()
                    ) if self.analyzed_segments_map else 0
                    
                    if total_spots == 1 and len(valid_paths) > 1:
                        valid_paths = [valid_paths[0]]
                    
                    self.ending_paths = valid_paths
                    
                    # UI güncelle
                    if len(self.ending_paths) > 1:
                        label_text = f"{len(self.ending_paths)} dosya seçildi"
                    else:
                        label_text = format_path_display(self.ending_paths[0])
                    
                    self.step_cards["ending"].update_path(label_text)
        
        self._update_status()
    
    def _select_output_folder(self):
        """Çıktı klasörü seçim dialogu"""
        folder_path = filedialog.askdirectory(title="Çıktı klasörü seç")
        if folder_path:
            self.output_path = folder_path
            display_path = format_path_display(folder_path)
            self.step_cards["output"].update_path(display_path)
            self._update_status()
    
    def _open_preset_browser(self):
        """Preset browser penceresini açar"""
        # Ham ses analizi kontrolü
        if not self.ham_paths:
            messagebox.showwarning(
                "Ham Ses Gerekli",
                "Lütfen önce ham ses dosyasını yükleyin ve analiz edin."
            )
            return
        
        if not self.analyzed_segments_map or not any(self.analyzed_segments_map.values()):
            messagebox.showwarning(
                "Analiz Gerekli",
                "Lütfen önce ham ses dosyasını analiz edin.\n\n"
                "Ham ses yüklendikten sonra analiz otomatik başlar. "
                "Analiz tamamlanana kadar bekleyin."
            )
            return
        
        total_spots = sum(
            len(v) for v in self.analyzed_segments_map.values()
        ) if self.analyzed_segments_map else None
        
        browser = PresetBrowser(
            self,
            on_selection=self._on_preset_selection,
            total_spots=total_spots
        )
    
    def _on_preset_selection(self, selected_paths: List[str]):
        """Preset seçim callback'i"""
        self.fon_paths = selected_paths
        
        if len(self.fon_paths) > 1:
            label_text = f"{len(self.fon_paths)} dosya seçildi"
        else:
            label_text = format_path_display(self.fon_paths[0])
        
        self.step_cards["fon"].update_path(label_text)
        self._update_status()
    
    def _open_ending_browser(self):
        """Bitiş browser penceresini açar"""
        # Ham ses analizi kontrolü
        if not self.ham_paths:
            messagebox.showwarning(
                "Ham Ses Gerekli",
                "Lütfen önce ham ses dosyasını yükleyin ve analiz edin."
            )
            return
        
        if not self.analyzed_segments_map or not any(self.analyzed_segments_map.values()):
            messagebox.showwarning(
                "Analiz Gerekli",
                "Lütfen önce ham ses dosyasını analiz edin.\n\n"
                "Ham ses yüklendikten sonra analiz otomatik başlar. "
                "Analiz tamamlanana kadar bekleyin."
            )
            return
        
        total_spots = sum(
            len(v) for v in self.analyzed_segments_map.values()
        ) if self.analyzed_segments_map else None
        
        browser = PresetBrowser(
            self,
            on_selection=self._on_ending_selection,
            total_spots=total_spots,
            categories=ENDING_CATEGORIES,
            title="Bitiş Sesleri Kataloğu",
            default_category="Bitiş Sesleri"
        )
    
    def _on_ending_selection(self, selected_paths: List[str]):
        """Bitiş seçim callback'i"""
        self.ending_paths = selected_paths
        
        if len(self.ending_paths) > 1:
            label_text = f"{len(self.ending_paths)} dosya seçildi"
        else:
            label_text = format_path_display(self.ending_paths[0])
        
        self.step_cards["ending"].update_path(label_text)
        self._update_status()
    
    def _run_analysis_in_background(self, paths: List[str]):
        """Arka planda ses analizi yapar"""
        def analysis_thread():
            result = {}
            for path in paths:
                try:
                    segments = analyze_audio_segments(path)
                    result[path] = segments
                except Exception as e:
                    logger.error(f"Analiz hatası ({path}): {e}")
                    result[path] = []
            
            self.analyzed_segments_map = result
            self.after(0, self._update_analysis_ui)
        
        threading.Thread(target=analysis_thread, daemon=True).start()
    
    def _update_analysis_ui(self):
        """Analiz sonuçlarını UI'da gösterir"""
        count = sum(len(v) for v in self.analyzed_segments_map.values())
        
        if count > 0:
            self.step_cards["ham"].update_analysis(
                f"{count} spot bulundu ✓",
                "#27AE60"
            )
            self.analysis_done = True
        else:
            self.step_cards["ham"].update_analysis(
                "Konuşma bulunamadı ✗",
                "#E74C3C"
            )
            self.analysis_done = False
        
        self._update_status()
    
    def _update_status(self):
        """Durum mesajını günceller"""
        if self.ham_paths and self.fon_paths:
            if not self.output_path:
                # Varsayılan çıktı yolu
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                ham_folder_name = os.path.splitext(
                    os.path.basename(self.ham_paths[0])
                )[0]
                default_path = os.path.join(desktop, "Montajlanan", ham_folder_name)
                self.step_cards["output"].update_path(
                    f"Varsayılan: {format_path_display(default_path)}",
                    "gray50"
                )
            
            self.control_panel.update_status(
                "Tüm dosyalar hazır. Montajı başlatabilirsiniz!",
                "#27AE60"
            )
            self.control_panel.start_button.configure(state="normal")
        else:
            self.control_panel.update_status(
                "Başlamak için dosyaları seçin...",
                "gray60"
            )
            self.control_panel.start_button.configure(state="disabled")
    
    def _start_montaj(self):
        """Montaj işlemini başlatır"""
        if not (self.ham_paths and self.fon_paths):
            messagebox.showwarning(
                "Eksik Dosya",
                "Lütfen Ham Ses ve Fon Müziği seçin."
            )
            return
        
        # UI'ı işlem moduna al
        self.control_panel.set_processing(True)
        self.is_cancelled = False
        
        # Doğrulama thread'i
        threading.Thread(target=self._validation_thread, daemon=True).start()
    
    def _validation_thread(self):
        """Dosya doğrulama thread'i"""
        self.after(0, lambda: self.control_panel.update_status(
            "Ses dosyaları doğrulanıyor...",
            "gray60"
        ))
        
        try:
            from pydub import AudioSegment
            import json
            
            # Dosyaları test et
            for p in self.ham_paths:
                try:
                    audio = AudioSegment.from_file(p)
                    if len(audio) == 0:
                        raise ValueError(f"Dosya boş: {os.path.basename(p)}")
                except json.JSONDecodeError:
                    # Bazı dosyalarda metadata JSON hatası olabilir, görmezden gel
                    logger.warning(f"Metadata okuma hatası (görmezden geliniyor): {p}")
                except Exception as e:
                    raise Exception(f"Ham ses dosyası okunamadı ({os.path.basename(p)}): {str(e)}")
            
            for p in self.fon_paths:
                try:
                    audio = AudioSegment.from_file(p)
                    if len(audio) == 0:
                        raise ValueError(f"Dosya boş: {os.path.basename(p)}")
                except json.JSONDecodeError:
                    # Bazı dosyalarda metadata JSON hatası olabilir, görmezden gel
                    logger.warning(f"Metadata okuma hatası (görmezden geliniyor): {p}")
                except Exception as e:
                    raise Exception(f"Fon müziği dosyası okunamadı ({os.path.basename(p)}): {str(e)}")
            
            self.after(0, self._start_montage_after_validation)
        except Exception as e:
            logger.error(f"Dosya doğrulama hatası: {e}", exc_info=True)
            error_msg = f"Bir ses dosyası okunamadı.\n\nDosya: {os.path.basename(str(e).split(':')[0]) if ':' in str(e) else 'Bilinmeyen'}\n\nTeknik Detay: {str(e)}"
            self.after(0, self._montaj_hatasi, Exception(error_msg))
    
    def _start_montage_after_validation(self):
        """Doğrulama sonrası montajı başlatır"""
        # Çıktı klasörü
        if self.output_path:
            output_folder = self.output_path
        else:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            # Bugünün tarihini DD.MM.YYYY formatında al
            today = datetime.now().strftime("%d.%m.%Y")
            ham_folder_name = os.path.splitext(
                os.path.basename(self.ham_paths[0])
            )[0]
            # Montajlanan/tarih/klasör_adı formatında oluştur
            output_folder = os.path.join(desktop, "Montajlanan", today, ham_folder_name)
        
        try:
            os.makedirs(output_folder, exist_ok=True)
        except OSError as e:
            self._montaj_hatasi(e)
            return
        
        # Ayarları kaydet
        self._save_settings()
        
        # Progress modal'ı aç
        self.progress_modal = ProgressModal(self)
        
        # Montaj thread'i
        output_format = self.control_panel.get_format()
        threading.Thread(
            target=self._montaj_thread,
            args=(output_folder, output_format),
            daemon=True
        ).start()
    
    def _montaj_thread(self, output_folder: str, output_format: str):
        """Montaj işlem thread'i"""
        try:
            out_files = self._run_multi_montaj(output_folder, output_format)
            
            if self.is_cancelled:
                self.after(0, self._montaj_iptal_edildi)
            elif out_files:
                self.after(0, self._montaj_tamamlandi, out_files, output_folder)
            else:
                if not self.is_cancelled:
                    raise Exception("Montaj bilinmeyen bir nedenle başarısız oldu.")
        except Exception as e:
            self.after(0, self._montaj_hatasi, e)
    
    def _run_multi_montaj(
        self,
        output_folder: str,
        output_format: str
    ) -> List[str]:
        """Çoklu dosya montaj işlemi"""
        # Aşama 1: Ham Ses Analiz Ediliyor (zaten tamamlandı, sadece göster)
        if hasattr(self, 'progress_modal') and self.progress_modal:
            self.after(0, lambda: self.progress_modal.update_stage(0))
            time.sleep(0.3)  # Kısa bir gecikme (görsel efekt için)
        
        all_out_files = []
        segments_total = sum(
            len(v) for v in self.analyzed_segments_map.values()
        )
        
        # Toplam geçerli spot sayısını hesapla (minimum 1000ms uzunluğunda olanlar)
        total_valid_spots = 0
        for ranges in self.analyzed_segments_map.values():
            valid_count = sum(1 for seg in ranges if (seg[1] - seg[0]) >= 1000)
            total_valid_spots += valid_count
        
        # Tek spot kuralı: çoklu fon seçildiyse ilkini kullan
        effective_fons = self.fon_paths
        if segments_total == 1 and len(effective_fons) > 1:
            effective_fons = [effective_fons[0]]
        
        # Aşama 2: Fon Sesi Entegre Ediliyor
        if hasattr(self, 'progress_modal') and self.progress_modal:
            self.after(0, lambda: self.progress_modal.update_stage(1))
        
        # Her spot için fon ata ve montajla
        global_spot_index = 0  # Tüm spotlar için global sayaç
        current_spot_number = 0  # Mevcut spot numarası (1'den başlar)
        for ham_path, ranges in self.analyzed_segments_map.items():
            valid_ranges = [
                seg for seg in ranges
                if (seg[1] - seg[0]) >= 1000
            ]
            
            for idx, (start, end) in enumerate(valid_ranges, 1):
                if self.is_cancelled:
                    return []
                
                # Fon seçimi
                chosen_fon = (
                    effective_fons[0]
                    if len(effective_fons) == 1
                    else random.choice(effective_fons)
                )
                
                # Tek spot montaj
                partial_ranges = [(start, end)]
                
                # Mevcut spot numarasını artır
                current_spot_number += 1
                
                # Closure için spot numarasını yakala
                spot_num = current_spot_number
                total_spots = total_valid_spots
                
                def progress_callback(progress: int, message: str):
                    self.after(0, lambda: self.control_panel.update_progress(
                        progress, message
                    ))
                    # Progress modal'a spot bilgisini gönder (toplam spot sayısı ile)
                    if hasattr(self, 'progress_modal') and self.progress_modal:
                        # Kendi spot bilgimizi oluştur
                        spot_info = f"Spot {spot_num}/{total_spots} İşleniyor..."
                        if "Montaj tamamlandı" not in message:
                            self.after(0, lambda info=spot_info: self.progress_modal.update_spot_info(info))
                        else:
                            self.after(0, lambda: self.progress_modal.update_spot_info(""))
                
                # Gelişmiş ayarları kullan (varsa)
                # Gelişmiş ayarları geçir
                advanced_settings_dict = self.advanced_settings if self.advanced_settings else None
                
                # Spot index offset'i geçir (dosya isimlendirme için)
                # global_spot_index kullanarak her spot için benzersiz numara
                
                # Bitiş seçimi (spot başına veya genel)
                chosen_ending = None
                if self.ending_paths:
                    if len(self.ending_paths) == 1:
                        chosen_ending = self.ending_paths[0]
                    else:
                        # Çoklu bitiş varsa rastgele seç (veya spot index'e göre)
                        chosen_ending = random.choice(self.ending_paths)
                
                out_files = ses_montaj(
                    ham_path,
                    output_dir=output_folder,
                    output_format=output_format,
                    fon_path=chosen_fon,
                    merged_ranges=partial_ranges,
                    progress_callback=progress_callback,
                    is_cancelled=lambda: self.is_cancelled,
                    advanced_settings=advanced_settings_dict,
                    spot_index_offset=global_spot_index,
                    ending_path=chosen_ending
                )
                
                all_out_files.extend(out_files)
                global_spot_index += len(out_files)  # Kaydedilen dosya sayısı kadar artır
        
        # Aşama 3: Montaj Tamamlanıyor
        if hasattr(self, 'progress_modal') and self.progress_modal:
            self.after(0, lambda: self.progress_modal.update_stage(2))
            time.sleep(0.3)  # Kısa bir gecikme
        
        return all_out_files
    
    def _cancel_montaj(self):
        """Montajı iptal eder"""
        self.is_cancelled = True
        self.control_panel.cancel_button.configure(
            state="disabled",
            text="İptal ediliyor...",
            text_color="#FFFFFF"
        )
    
    def _montaj_tamamlandi(self, out_files: List[str], output_folder: str):
        """Montaj tamamlandı handler'ı"""
        self.control_panel.set_processing(False)
        self.control_panel.update_status(
            f"✅ Başarılı! {len(out_files)} adet spot oluşturuldu.",
            "#28A745"
        )
        
        # ZIP dosyası oluştur (arka planda thread'de)
        def create_zip_in_background():
            try:
                zip_path = self._create_zip_archive(out_files, output_folder)
                if zip_path and hasattr(self, 'progress_modal') and self.progress_modal:
                    # ZIP oluşturulduğunda mesajı güncelle
                    import os
                    folder_name = os.path.basename(output_folder) if output_folder else "Klasör"
                    zip_info = f"\n📦 ZIP: {os.path.basename(zip_path)}"
                    message = (
                        f"Montaj başarıyla tamamlandı!\n\n"
                        f"📊 Toplam {len(out_files)} adet spot kaydedildi.\n\n"
                        f"📁 {folder_name}{zip_info}"
                    )
                    self.after(0, lambda: self.progress_modal.result_label.configure(
                        text=message, text_color="#28A745"
                    ))
            except Exception as e:
                logger.warning(f"ZIP oluşturulamadı: {e}", exc_info=True)
        
        threading.Thread(target=create_zip_in_background, daemon=True).start()
        
        # Progress modal'da tamamlanma mesajını göster
        if hasattr(self, 'progress_modal') and self.progress_modal:
            # Kısa mesaj (uzun dizin yolunu kısalt)
            import os
            folder_name = os.path.basename(output_folder) if output_folder else "Klasör"
            message = (
                f"Montaj başarıyla tamamlandı!\n\n"
                f"📊 Toplam {len(out_files)} adet spot kaydedildi.\n\n"
                f"📁 {folder_name}\n\n"
                f"📦 ZIP arşivi oluşturuluyor..."
            )
            self.progress_modal.show_completion(message)
        
        # Çıktı klasörünü aç (Windows)
        try:
            import subprocess
            subprocess.Popen(f'explorer "{output_folder}"', shell=True)
        except Exception:
            pass
        
        # Tüm seçimleri temizle
        self._clear_all_selections()
    
    def _create_zip_archive(self, out_files: List[str], output_folder: str) -> Optional[str]:
        """Çıktı dosyalarını ZIP arşivine paketler"""
        try:
            import zipfile
            import os
            import re
            
            # ZIP dosya adı: klasör adından tarih/saat bilgisini temizle
            folder_name = os.path.basename(output_folder)
            # Tarih/saat formatını kaldır: _20251126_211943 veya benzeri
            # Pattern: _YYYYMMDD_HHMMSS veya _YYYYMMDDHHMMSS
            folder_name = re.sub(r'_\d{8}_?\d{0,6}$', '', folder_name)
            zip_filename = f"{folder_name}.zip"
            zip_path = os.path.join(os.path.dirname(output_folder), zip_filename)
            
            # ZIP oluştur
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in out_files:
                    if os.path.exists(file_path):
                        # ZIP içinde sadece dosya adını kullan
                        arcname = os.path.basename(file_path)
                        zipf.write(file_path, arcname)
                        logger.debug(f"ZIP'e eklendi: {arcname}")
            
            logger.info(f"ZIP arşivi oluşturuldu: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"ZIP oluşturma hatası: {e}", exc_info=True)
            return None
    
    def _clear_all_selections(self):
        """Tüm seçimleri temizler"""
        # Veri yapılarını temizle
        self.ham_paths = []
        self.fon_paths = []
        self.output_path = None
        self.analyzed_segments_map = {}
        self.analysis_done = False
        
        # Step card'ları güncelle
        if "ham" in self.step_cards:
            self.step_cards["ham"].update_path("Ham ses dosyası seçilmedi")
            self.step_cards["ham"].update_analysis("")
        
        if "fon" in self.step_cards:
            self.step_cards["fon"].update_path("Fon müziği seçilmedi")
        
        if "output" in self.step_cards:
            self.step_cards["output"].update_path("Çıktı klasörü seçilmedi")
        
        # Status'u güncelle
        self._update_status()
    
    def _montaj_hatasi(self, exc: Exception):
        """Montaj hatası handler'ı"""
        self.control_panel.set_processing(False)
        self.control_panel.update_status("Bir hata oluştu!", "#E74C3C")
        
        # Progress modal'ı kapat
        if hasattr(self, 'progress_modal') and self.progress_modal:
            try:
                self.progress_modal.destroy()
            except Exception:
                pass
        
        messagebox.showerror("Montaj Hatası", f"Bir hata oluştu:\n\n{str(exc)}")
    
    def _montaj_iptal_edildi(self):
        """Montaj iptal edildi handler'ı"""
        self.control_panel.set_processing(False)
        self.control_panel.update_status(
            "İşlem kullanıcı tarafından iptal edildi.",
            "gray60"
        )
        
        # Progress modal'ı kapat
        if hasattr(self, 'progress_modal') and self.progress_modal:
            try:
                self.progress_modal.destroy()
            except Exception:
                pass
    
    def _on_theme_change(self, is_dark: bool):
        """Tema değişim handler'ı"""
        new_mode = "dark" if is_dark else "light"
        ctk.set_appearance_mode(new_mode)
        self._save_settings()
    
    def _on_format_change(self, value: str):
        """Format değişim handler'ı"""
        self._save_settings()
    
    def _save_settings(self):
        """Ayarları kaydeder"""
        try:
            self.config.set("output_format", self.control_panel.get_format())
            self.config.set("theme", "dark" if self.control_panel.get_theme() else "light")
            
            # Pencere boyutu
            width = self.winfo_width()
            height = self.winfo_height()
            self.config.set("window_geometry.width", width)
            self.config.set("window_geometry.height", height)
            
            self.config.save()
        except Exception as e:
            logger.warning(f"Ayarlar kaydedilemedi: {e}")
    
    def _load_settings(self):
        """Ayarları yükler"""
        try:
            # Format
            format_val = self.config.get("output_format", "wav")
            self.control_panel.format_var.set(format_val)
            
            # Tema
            theme = self.config.get("theme", "light")
            is_dark = theme == "dark"
            self.control_panel.set_theme(is_dark)
            ctk.set_appearance_mode(theme)
        except Exception as e:
            logger.warning(f"Ayarlar yüklenemedi: {e}")
    
    def _open_advanced_settings(self):
        """Gelişmiş ayarlar penceresini açar"""
        from .components.advanced_settings import AdvancedSettings
        
        current_settings = {
            "start_fon_db": -1.94,
            "ducked_fon_db": -10.46,
            "mid_fon_db": -3.10,
            "voice_db": -0.91,
            "intro_duration": 3000,
            "outro_rise": 2000,
            "outro_fall": 3000
        }
        
        def on_save(settings):
            # Ayarları kaydet (şimdilik sadece log)
            logger.info(f"Gelişmiş ayarlar kaydedildi: {settings}")
            # TODO: Ayarları processor'a aktar
        
        AdvancedSettings(self, current_settings, on_save)
    
    def _check_for_updates(self):
        """Güncellemeleri kontrol eder"""
        # Butonu devre dışı bırak
        self.control_panel.update_btn.configure(
            state="disabled",
            text="Kontrol ediliyor..."
        )
        
        def check_in_thread():
            """Thread'de güncelleme kontrolü yapar"""
            try:
                update_info = check_for_updates(APP_VERSION)
                
                # UI güncellemesi ana thread'de yapılmalı
                self.after(0, lambda: self._handle_update_result(update_info))
            except Exception as e:
                logger.error(f"Güncelleme kontrolü hatası: {e}", exc_info=True)
                self.after(0, lambda: self._handle_update_error(str(e)))
        
        # Arka planda kontrol et
        thread = threading.Thread(target=check_in_thread, daemon=True)
        thread.start()
    
    def _handle_update_result(self, update_info: Dict):
        """Güncelleme kontrolü sonucunu işler"""
        # Butonu tekrar aktif et
        self.control_panel.update_btn.configure(
            state="normal",
            text="🔄 Güncellemeleri Kontrol Et"
        )
        
        if update_info.get("available", False):
            # Güncelleme var - modal göster
            UpdateModal(
                self, 
                update_info, 
                APP_VERSION,
                on_install_now=self._install_update_now,
                on_remind_later=self._remind_later
            )
        else:
            # Güncelleme yok veya hata
            error = update_info.get("error")
            if error:
                messagebox.showinfo(
                    "Güncelleme Kontrolü",
                    f"Güncelleme kontrol edilemedi:\n\n{error}"
                )
            else:
                messagebox.showinfo(
                    "Güncelleme Kontrolü",
                    "Uygulamanız güncel!\n\n"
                    f"Mevcut versiyon: {APP_VERSION}"
                )
    
    def _handle_update_error(self, error_msg: str):
        """Güncelleme kontrolü hatasını işler"""
        # Butonu tekrar aktif et
        self.control_panel.update_btn.configure(
            state="normal",
            text="🔄 Güncellemeleri Kontrol Et"
        )
        
        messagebox.showerror(
            "Güncelleme Kontrolü",
            f"Güncelleme kontrol edilirken bir hata oluştu:\n\n{error_msg}"
        )
    
    def _auto_check_updates(self):
        """Uygulama başlangıcında otomatik güncelleme kontrolü (sessiz)"""
        def check_in_thread():
            try:
                update_info = check_for_updates(APP_VERSION)
                
                # Sadece güncelleme varsa ve "daha sonra hatırlat" seçilmişse göster
                if update_info.get("available", False):
                    remind_version = self.config.get("update.remind_later_version", "")
                    if remind_version != update_info.get("version", ""):
                        # Yeni güncelleme veya hatırlatma zamanı geldi
                        self.after(0, lambda: self._show_update_modal(update_info))
            except Exception as e:
                logger.debug(f"Otomatik güncelleme kontrolü hatası: {e}")
        
        thread = threading.Thread(target=check_in_thread, daemon=True)
        thread.start()
    
    def _show_update_modal(self, update_info: Dict):
        """Güncelleme modal'ını göster"""
        UpdateModal(
            self, 
            update_info, 
            APP_VERSION,
            on_install_now=self._install_update_now,
            on_remind_later=self._remind_later
        )
    
    def _install_update_now(self, download_url: str):
        """Güncellemeyi şimdi yükle - programı kapat ve setup'ı çalıştır"""
        try:
            import tempfile
            import requests
            
            logger.info(f"Güncelleme indiriliyor: {download_url}")
            
            # Setup dosyasını indir
            response = requests.get(download_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Geçici dosyaya kaydet
            temp_dir = tempfile.gettempdir()
            setup_path = os.path.join(temp_dir, "AiMusicAutoSpot_Update.exe")
            
            with open(setup_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Setup dosyası indirildi: {setup_path}")
            
            # Setup'ı çalıştır ve programı kapat
            subprocess.Popen([setup_path], shell=True)
            
            # Programı kapat
            self.after(1000, lambda: self._force_close())
            
        except Exception as e:
            logger.error(f"Güncelleme indirme hatası: {e}", exc_info=True)
            messagebox.showerror(
                "Güncelleme Hatası",
                f"Güncelleme indirilemedi:\n\n{e}\n\n"
                "Lütfen manuel olarak GitHub'dan indirin."
            )
    
    def _remind_later(self, version: str, download_url: str):
        """Daha sonra hatırlat - flag'i kaydet"""
        try:
            self.config.set("update.remind_later_version", version)
            self.config.set("update.download_url", download_url)
            self.config.save()
            logger.info(f"Güncelleme hatırlatması kaydedildi: {version}")
        except Exception as e:
            logger.warning(f"Güncelleme hatırlatması kaydedilemedi: {e}")
    
    def _force_close(self):
        """Programı zorla kapat"""
        try:
            self._save_settings()
            self.is_cancelled = True
            self.destroy()
            sys.exit(0)
        except Exception:
            os._exit(0)
    
    def _on_closing(self):
        """Pencere kapatma handler'ı"""
        try:
            # "Daha sonra hatırlat" seçilmişse, kapanışta güncellemeyi kontrol et ve yükle
            remind_version = self.config.get("update.remind_later_version", "")
            download_url = self.config.get("update.download_url", "")
            
            if remind_version and download_url:
                # Güncelleme var, kapanışta yükle
                logger.info(f"Kapanışta güncelleme yükleniyor: {remind_version}")
                try:
                    import tempfile
                    import requests
                    
                    # Setup dosyasını indir
                    response = requests.get(download_url, timeout=30, stream=True)
                    response.raise_for_status()
                    
                    temp_dir = tempfile.gettempdir()
                    setup_path = os.path.join(temp_dir, "AiMusicAutoSpot_Update.exe")
                    
                    with open(setup_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Setup'ı çalıştır
                    subprocess.Popen([setup_path], shell=True)
                    
                    # Flag'leri temizle
                    self.config.set("update.remind_later_version", "")
                    self.config.set("update.download_url", "")
                    self.config.save()
                    
                except Exception as e:
                    logger.error(f"Kapanışta güncelleme hatası: {e}")
            
            self._save_settings()
            self.is_cancelled = True
            self.destroy()
            sys.exit(0)
        except Exception:
            pass

