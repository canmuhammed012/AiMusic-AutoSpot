"""Kontrol paneli bileşeni"""

import customtkinter as ctk
from typing import Optional, Callable
import logging

from ...constants import FONT_FAMILY, UIConfig

logger = logging.getLogger(__name__)

class ControlPanel(ctk.CTkFrame):
    """Ayarlar ve kontrol paneli"""
    
    def __init__(
        self,
        parent,
        on_theme_change: Optional[Callable] = None,
        on_format_change: Optional[Callable] = None,
        on_start: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        on_advanced: Optional[Callable] = None,
        on_check_updates: Optional[Callable] = None,
        **kwargs
    ):
        """
        ControlPanel oluşturur.
        
        Args:
            parent: Parent widget
            on_theme_change: Tema değişim callback'i
            on_format_change: Format değişim callback'i
            on_start: Başlat butonu callback'i
            on_cancel: İptal butonu callback'i
            on_advanced: Gelişmiş ayarlar callback'i
        """
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.on_theme_change = on_theme_change
        self.on_format_change = on_format_change
        self.on_start = on_start
        self.on_cancel = on_cancel
        self.on_advanced = on_advanced
        self.on_check_updates = on_check_updates
        
        # Değişkenleri başlat
        self.theme_var = ctk.BooleanVar()
        self.format_var = ctk.StringVar(value="wav")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI elemanlarını oluşturur"""
        # Ayarlar kartı
        settings_card = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#2D2E30"),
            corner_radius=UIConfig.CARD_CORNER_RADIUS,
            border_width=1,
            border_color=("#E0E0E0", "#444")
        )
        settings_card.pack(fill="x", pady=(8, 10))
        
        # Başlık
        ctk.CTkLabel(
            settings_card,
            text="Ayarlar",
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 12))
        
        # Kompakt ayarlar (yan yana)
        settings_row = ctk.CTkFrame(settings_card, fg_color="transparent")
        settings_row.pack(fill="x", padx=20, pady=(0, 15))
        
        # Sol taraf: Görünüm
        left_frame = ctk.CTkFrame(settings_row, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            left_frame,
            text="Görünüm",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 5))
        
        self.theme_switch = ctk.CTkSwitch(
            left_frame,
            text="Koyu Mod",
            variable=self.theme_var,
            command=self._on_theme_toggle,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11)
        )
        self.theme_switch.pack(anchor="w")
        
        # Sağ taraf: Format
        right_frame = ctk.CTkFrame(settings_row, fg_color="transparent")
        right_frame.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(
            right_frame,
            text="Format",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 5))
        
        self.format_var = ctk.StringVar(value="wav")
        self.format_menu = ctk.CTkOptionMenu(
            right_frame,
            values=["wav", "mp3"],
            variable=self.format_var,
            command=self._on_format_change,
            width=120,
            height=28,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            dropdown_font=ctk.CTkFont(family=FONT_FAMILY, size=11)
        )
        self.format_menu.pack(anchor="w")
        
        # Gelişmiş ayarlar butonu (ortalanmış, alt satırda)
        advanced_row = ctk.CTkFrame(settings_card, fg_color="transparent")
        advanced_row.pack(fill="x", padx=20, pady=(0, 18))
        
        self.advanced_btn = ctk.CTkButton(
            advanced_row,
            text="⚙️ Gelişmiş Ayarlar",
            command=self._on_advanced_clicked,
            width=180,
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color="#6C757D",
            hover_color="#5A6268",
            border_width=0
        )
        self.advanced_btn.pack(anchor="center")
        
        # Güncellemeleri kontrol et butonu
        update_row = ctk.CTkFrame(settings_card, fg_color="transparent")
        update_row.pack(fill="x", padx=20, pady=(10, 18))
        
        self.update_btn = ctk.CTkButton(
            update_row,
            text="🔄 Güncellemeleri Kontrol Et",
            command=self._on_check_updates_clicked,
            width=180,
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color="#007BFF",
            hover_color="#0056B3",
            border_width=0
        )
        self.update_btn.pack(anchor="center")
        
        # Durum ve ilerleme
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 5))
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Başlamak için dosyaları seçin...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14),
            text_color="gray60",
            wraplength=250,
            justify="left",
            height=40,
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w")
        
        # İlerleme çubuğu
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(5, 0))
        progress_frame.grid_columnconfigure(0, weight=1)
        progress_frame.grid_columnconfigure(1, weight=0)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, mode="determinate")
        self.progress_bar.grid(row=0, column=0, sticky="ew", ipady=2)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=("#333", "#EEE")
        )
        self.progress_label.grid(row=0, column=1, padx=(5, 0), sticky="e")
        
        # Aksiyon butonları
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", pady=(5, 0))
        
        self.start_button = ctk.CTkButton(
            action_frame,
            text="🚀 Montajı Başlat",
            font=ctk.CTkFont(family=FONT_FAMILY, size=17, weight="bold"),
            height=60,
            corner_radius=14,
            fg_color="#28A745",
            hover_color="#218838",
            border_width=0,
            command=self._on_start_clicked
        )
        self.start_button.pack(fill="x", pady=(0, 10))
        
        self.cancel_button = ctk.CTkButton(
            action_frame,
            text="✕ İptal Et",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            height=45,
            corner_radius=12,
            fg_color="#DC3545",
            hover_color="#C82333",
            text_color="#FFFFFF",
            border_width=0,
            command=self._on_cancel_clicked,
            state="disabled"
        )
        self.cancel_button.pack(fill="x")
    
    def _create_settings_row(
        self,
        parent,
        title: str,
        description: str,
        widget_type: str,
        callback: Optional[Callable] = None
    ):
        """Ayarlar satırı oluşturur"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=8)
        
        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            text_frame,
            text=title,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 0))
        
        ctk.CTkLabel(
            text_frame,
            text=description,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color="gray60"
        ).pack(anchor="w", pady=(0, 0))
        
        if widget_type == "switch":
            if not hasattr(self, 'theme_var'):
                self.theme_var = ctk.BooleanVar()
            switch = ctk.CTkSwitch(
                row,
                text="",
                variable=self.theme_var,
                command=callback
            )
            switch.pack(side="right")
        elif widget_type == "optionmenu":
            if not hasattr(self, 'format_var'):
                self.format_var = ctk.StringVar(value="wav")
            optionmenu = ctk.CTkOptionMenu(
                row,
                variable=self.format_var,
                values=["wav", "mp3"],
                width=80,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                dropdown_font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                corner_radius=UIConfig.BUTTON_CORNER_RADIUS,
                command=callback
            )
            optionmenu.pack(side="right")
    
    def _on_theme_toggle(self):
        """Tema değişim handler'ı"""
        if self.on_theme_change:
            self.on_theme_change(self.theme_var.get())
    
    def _on_advanced_clicked(self):
        """Gelişmiş ayarlar butonu handler'ı"""
        if self.on_advanced:
            self.on_advanced()
    
    def _on_check_updates_clicked(self):
        """Güncellemeleri kontrol et butonu handler'ı"""
        if self.on_check_updates:
            self.on_check_updates()
    
    def _on_format_change(self, value: str):
        """Format değişim handler'ı"""
        if self.on_format_change:
            self.on_format_change(value)
    
    def _on_start_clicked(self):
        """Başlat butonu handler'ı"""
        if self.on_start:
            self.on_start()
    
    def _on_cancel_clicked(self):
        """İptal butonu handler'ı"""
        if self.on_cancel:
            self.on_cancel()
    
    def update_status(self, text: str, color: str = "gray60"):
        """Durum etiketini günceller"""
        self.status_label.configure(text=text, text_color=color)
    
    def update_progress(self, value: int, message: str = ""):
        """
        İlerleme çubuğunu günceller.
        
        Args:
            value: İlerleme değeri (0-100)
            message: Durum mesajı
        """
        self.progress_bar.set(value / 100.0)
        self.progress_label.configure(text=f"%{int(value)}" if value > 0 else "")
        if message:
            self.update_status(message)
    
    def set_processing(self, processing: bool):
        """
        İşlem durumunu ayarlar.
        
        Args:
            processing: İşlem devam ediyor mu?
        """
        state = "disabled" if processing else "normal"
        self.start_button.configure(state=state)
        self.cancel_button.configure(state="normal" if processing else "disabled")
        
        if not processing:
            self.progress_bar.set(0)
            self.progress_label.configure(text="")
    
    def get_format(self) -> str:
        """Seçili formatı döndürür"""
        return self.format_var.get()
    
    def get_theme(self) -> bool:
        """Tema durumunu döndürür (True=koyu, False=açık)"""
        return self.theme_var.get()
    
    def set_theme(self, is_dark: bool):
        """Tema durumunu ayarlar"""
        self.theme_var.set(is_dark)

