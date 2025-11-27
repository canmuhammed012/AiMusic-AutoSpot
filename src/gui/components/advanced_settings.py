"""Gelişmiş ayarlar paneli"""

import customtkinter as ctk
from typing import Optional, Callable, Dict, Any
import logging

from ...constants import FONT_FAMILY, UIConfig

logger = logging.getLogger(__name__)

class AdvancedSettings(ctk.CTkToplevel):
    """Gelişmiş ayarlar penceresi"""
    
    def __init__(
        self,
        parent,
        current_settings: Dict[str, Any],
        on_save: Callable[[Dict[str, Any]], None],
        **kwargs
    ):
        """
        AdvancedSettings oluşturur.
        
        Args:
            parent: Parent window
            current_settings: Mevcut ayarlar
            on_save: Kaydet callback'i
        """
        super().__init__(parent, **kwargs)
        
        self.current_settings = current_settings
        self.on_save = on_save
        self.settings_vars = {}
        
        self._setup_window()
        self._setup_ui()
    
    def _setup_window(self):
        """Pencere ayarlarını yapar"""
        self.title("Gelişmiş Ayarlar")
        modal_w, modal_h = 600, 700
        
        parent = self.master
        parent.update_idletasks()
        
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        
        x = parent_x + (parent_w // 2 - modal_w // 2)
        y = parent_y + (parent_h // 2 - modal_h // 2)
        
        self.geometry(f"{modal_w}x{modal_h}+{x}+{y}")
        self.grab_set()
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_ui(self):
        """UI elemanlarını oluşturur"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        ctk.CTkLabel(
            main_frame,
            text="⚙️ Gelişmiş Ayarlar",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold")
        ).pack(pady=(0, 20))
        
        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(main_frame, height=550)
        scroll_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Ses Seviyeleri
        self._create_section(scroll_frame, "Ses Seviyeleri (dB)")
        self._create_slider(scroll_frame, "Fon Başlangıç", "start_fon_db", -5.0, 0.0, -1.94)
        self._create_slider(scroll_frame, "Fon Ducking", "ducked_fon_db", -15.0, -5.0, -10.46)
        self._create_slider(scroll_frame, "Fon Orta", "mid_fon_db", -5.0, 0.0, -3.10)
        self._create_slider(scroll_frame, "Ses Seviyesi", "voice_db", -3.0, 3.0, -0.91)
        
        # Timing Ayarları
        self._create_section(scroll_frame, "Zamanlama (ms)")
        self._create_slider(scroll_frame, "Intro Süresi", "intro_duration", 1000, 5000, 3000, step=100)
        self._create_slider(scroll_frame, "Outro Yükseliş", "outro_rise", 1000, 4000, 2000, step=100)
        self._create_slider(scroll_frame, "Outro Düşüş", "outro_fall", 2000, 5000, 3000, step=100)
        
        # Spot Analizi Ayarları
        self._create_section(scroll_frame, "Spot Analizi")
        self._create_slider_with_format(scroll_frame, "Boşluk Süresi", "max_gap_ms", 500, 3000, 1400, step=50, format_func=lambda v: f"{v/1000:.2f}s")
        
        # Butonlar
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(
            btn_frame,
            text="Varsayılana Dön",
            command=self._reset_defaults,
            width=140,
            height=35,
            corner_radius=10,
            fg_color="#6C757D",
            hover_color="#5A6268"
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="İptal",
            command=self._on_close,
            width=100,
            height=35,
            corner_radius=10,
            fg_color="#6C757D",
            hover_color="#5A6268"
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="✓ Kaydet",
            command=self._save_settings,
            width=120,
            height=35,
            corner_radius=10,
            fg_color="#28A745",
            hover_color="#218838",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold")
        ).pack(side="right")
    
    def _create_section(self, parent, title: str):
        """Bölüm başlığı oluşturur"""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", pady=(15, 10))
        
        ctk.CTkLabel(
            section,
            text=title,
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF")
        ).pack(anchor="w")
        
        ctk.CTkFrame(
            section,
            height=2,
            fg_color=("#E0E0E0", "#555")
        ).pack(fill="x", pady=(5, 0))
    
    def _create_slider(self, parent, label: str, key: str, min_val: float, max_val: float, default: float, step: float = 0.1):
        """Slider oluşturur"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=8)
        
        # Label
        label_frame = ctk.CTkFrame(row, fg_color="transparent")
        label_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            label_frame,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            anchor="w"
        ).pack(anchor="w")
        
        # Value label
        value_var = ctk.StringVar()
        value_label = ctk.CTkLabel(
            row,
            textvariable=value_var,
            width=60,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color="#007BFF"
        )
        value_label.pack(side="right", padx=(10, 0))
        
        # Slider
        slider_var = ctk.DoubleVar(value=self.current_settings.get(key, default))
        slider = ctk.CTkSlider(
            row,
            from_=min_val,
            to=max_val,
            variable=slider_var,
            number_of_steps=int((max_val - min_val) / step),
            command=lambda v: value_var.set(f"{v:.2f}")
        )
        slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # İlk değeri göster
        value_var.set(f"{slider_var.get():.2f}")
        
        self.settings_vars[key] = slider_var
    
    def _create_slider_with_format(self, parent, label: str, key: str, min_val: float, max_val: float, default: float, step: float = 0.1, format_func: Optional[Callable[[float], str]] = None):
        """Slider oluşturur (özel format fonksiyonu ile)"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=8)
        
        # Label
        label_frame = ctk.CTkFrame(row, fg_color="transparent")
        label_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            label_frame,
            text=label,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            anchor="w"
        ).pack(anchor="w")
        
        # Value label
        value_var = ctk.StringVar()
        value_label = ctk.CTkLabel(
            row,
            textvariable=value_var,
            width=60,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color="#007BFF"
        )
        value_label.pack(side="right", padx=(10, 0))
        
        # Slider
        slider_var = ctk.DoubleVar(value=self.current_settings.get(key, default))
        
        # Format fonksiyonu varsa kullan, yoksa varsayılan format
        if format_func:
            update_cmd = lambda v: value_var.set(format_func(v))
        else:
            update_cmd = lambda v: value_var.set(f"{v:.2f}")
        
        slider = ctk.CTkSlider(
            row,
            from_=min_val,
            to=max_val,
            variable=slider_var,
            number_of_steps=int((max_val - min_val) / step),
            command=update_cmd
        )
        slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # İlk değeri göster
        if format_func:
            value_var.set(format_func(slider_var.get()))
        else:
            value_var.set(f"{slider_var.get():.2f}")
        
        self.settings_vars[key] = slider_var
    
    def _reset_defaults(self):
        """Varsayılan değerlere dön"""
        defaults = {
            "start_fon_db": -1.94,
            "ducked_fon_db": -10.46,
            "mid_fon_db": -3.10,
            "voice_db": -0.91,
            "intro_duration": 3000,
            "outro_rise": 2000,
            "outro_fall": 3000,
            "max_gap_ms": 1400
        }
        
        for key, value in defaults.items():
            if key in self.settings_vars:
                self.settings_vars[key].set(value)
    
    def _save_settings(self):
        """Ayarları kaydet"""
        settings = {}
        for key, var in self.settings_vars.items():
            settings[key] = var.get()
        
        if self.on_save:
            self.on_save(settings)
        
        self._on_close()
    
    def _on_close(self):
        """Pencereyi kapat"""
        try:
            self.grab_release()
            self.destroy()
        except Exception:
            pass

