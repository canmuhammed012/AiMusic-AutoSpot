"""Adım kartı bileşeni - Profesyonel modern tasarım"""

import customtkinter as ctk
from typing import Optional, Callable
from PIL import Image
import logging

from ...constants import FONT_FAMILY, UIConfig
from ...utils.file_utils import get_resource_path

logger = logging.getLogger(__name__)

class StepCard(ctk.CTkFrame):
    """Modern, profesyonel adım kartı bileşeni"""
    
    def __init__(
        self,
        parent,
        title: str,
        description: str,
        btn_text: str,
        command: Callable,
        icon: Optional[ctk.CTkImage] = None,
        extra_button: Optional[dict] = None,
        **kwargs
    ):
        """
        StepCard oluşturur.
        
        Args:
            parent: Parent widget
            title: Kart başlığı
            description: Açıklama metni
            btn_text: Ana buton metni
            command: Ana buton komutu
            icon: İkon (CTkImage)
            extra_button: Ekstra buton bilgileri {"text": str, "command": callable}
        """
        super().__init__(
            parent,
            fg_color=("#FFFFFF", "#2D2E30"),
            corner_radius=18,
            border_width=2,
            border_color=("#E3F2FD", "#424242"),
            **kwargs
        )
        
        self.title = title
        self.description = description
        self.icon = icon
        self._hover_state = False
        
        self._setup_ui(btn_text, command, extra_button)
        self._setup_animations()
    
    def _setup_ui(self, btn_text: str, command: Callable, extra_button: Optional[dict]):
        """UI elemanlarını oluşturur"""
        self.grid_columnconfigure(1, weight=1)
        
        # İkon (daha büyük)
        if self.icon:
            icon_label = ctk.CTkLabel(
                self,
                image=self.icon,
                text=""
            )
            icon_label.grid(row=0, column=0, rowspan=3, sticky="n", padx=25, pady=20)
        
        # Başlık (daha büyük ve bold)
        self.title_label = ctk.CTkLabel(
            self,
            text=self.title,
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            anchor="w",
            text_color=("#1A1A1A", "#FFFFFF")
        )
        self.title_label.grid(row=0, column=1, sticky="sw", pady=(15, 0), padx=(0, 15))
        
        # Açıklama (daha okunabilir)
        self.desc_label = ctk.CTkLabel(
            self,
            text=self.description,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color="gray60",
            anchor="w",
            justify="left",
            wraplength=400
        )
        self.desc_label.grid(row=1, column=1, sticky="nw", padx=(0, 15))
        
        # Yol gösterici (daha modern)
        path_container = ctk.CTkFrame(self, fg_color="transparent", height=28)
        path_container.grid(row=2, column=1, sticky="ew", pady=(12, 8))
        path_container.pack_propagate(False)
        
        self.path_label = ctk.CTkLabel(
            path_container,
            text="Henüz bir dosya seçilmedi...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, slant="italic"),
            text_color="gray50",
            anchor="w"
        )
        self.path_label.pack(side="left", anchor="w", padx=(0, 10))
        
        # Analiz sonucu etiketi (opsiyonel)
        self.analysis_label = None
        if "Ham Ses" in self.title:
            self.analysis_label = ctk.CTkLabel(
                self,
                text="",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
                text_color="#6C757D"
            )
            self.analysis_label.grid(row=2, column=2, sticky="e", pady=(12, 8), padx=(0, 25))
        
        # Butonlar (daha modern)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=0, column=2, rowspan=2, sticky="e", padx=25)
        
        # Ekstra buton (varsa)
        if extra_button:
            extra_btn = ctk.CTkButton(
                btn_frame,
                text=extra_button["text"],
                command=extra_button["command"],
                width=140,
                height=38,
                corner_radius=10,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
                fg_color="#17A2B8",
                hover_color="#138496",
                border_width=0
            )
            extra_btn.pack(side="left", padx=(0, 8))
        
        # Ana buton (daha büyük ve modern)
        self.main_button = ctk.CTkButton(
            btn_frame,
            text=btn_text,
            command=command,
            width=120,
            height=38,
            corner_radius=10,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            fg_color="#007BFF",
            hover_color="#0056B3",
            border_width=0
        )
        self.main_button.pack(side="left")
    
    def _setup_animations(self):
        """Animasyon efektlerini ayarlar"""
        # Hover efekti için event binding
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # Child widget'lara da bind et
        for widget in self.winfo_children():
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """Mouse giriş animasyonu"""
        if not self._hover_state:
            self._hover_state = True
            self._animate_hover(True)
    
    def _on_leave(self, event):
        """Mouse çıkış animasyonu"""
        if self._hover_state:
            self._hover_state = False
            self._animate_hover(False)
    
    def _animate_hover(self, is_hover: bool):
        """Hover animasyonu"""
        try:
            if is_hover:
                # Hafif yükseltme efekti
                self.configure(
                    border_width=3,
                    border_color=("#007BFF", "#4A9EFF"),
                    fg_color=("#F8F9FA", "#353535")
                )
            else:
                # Normal duruma dön
                self.configure(
                    border_width=2,
                    border_color=("#E3F2FD", "#424242"),
                    fg_color=("#FFFFFF", "#2D2E30")
                )
        except Exception as e:
            logger.debug(f"Animasyon hatası: {e}")
    
    def update_path(self, path_text: str, color: str = None):
        """
        Yol etiketini günceller.
        
        Args:
            path_text: Görüntülenecek metin
            color: Metin rengi (None ise varsayılan)
        """
        if color:
            self.path_label.configure(text=path_text, text_color=color)
        else:
            self.path_label.configure(text=path_text, text_color=("#1A1A1A", "#FFFFFF"))
    
    def update_analysis(self, text: str, color: str = "gray"):
        """
        Analiz sonucu etiketini günceller.
        
        Args:
            text: Görüntülenecek metin
            color: Metin rengi
        """
        if self.analysis_label:
            self.analysis_label.configure(text=text, text_color=color)
    
    def set_loading(self, loading: bool):
        """
        Yükleme durumunu ayarlar.
        
        Args:
            loading: Yükleme durumu
        """
        if loading:
            self.main_button.configure(
                state="disabled",
                text="⏳ Yükleniyor...",
                fg_color="#6C757D"
            )
        else:
            self.main_button.configure(
                state="normal",
                text="Dosya Seç",
                fg_color="#007BFF"
            )
