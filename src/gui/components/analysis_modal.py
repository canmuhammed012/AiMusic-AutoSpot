"""Ham ses analizi modal penceresi"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional
import logging

from ...constants import FONT_FAMILY

logger = logging.getLogger(__name__)

class AnalysisModal(ctk.CTkToplevel):
    """Ham ses analizi için basit modal pencere"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        
        self._setup_window()
        self._setup_ui()
    
    def _setup_window(self):
        """Pencere ayarlarını yapar"""
        self.title("Analiz Ediliyor")
        modal_w, modal_h = 400, 150
        
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
        self.transient(parent)
        
        # Kapatma butonunu devre dışı bırak
        self.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def _setup_ui(self):
        """UI elemanlarını oluşturur"""
        main_frame = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#2D2E30"),
            corner_radius=15,
            border_width=2,
            border_color=("#E0E0E0", "#444")
        )
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Spinner (dönen çark)
        self.spinner_label = ctk.CTkLabel(
            content_frame,
            text="⏳",
            font=ctk.CTkFont(family=FONT_FAMILY, size=40)
        )
        self.spinner_label.pack(pady=(0, 15))
        
        # Mesaj
        self.message_label = ctk.CTkLabel(
            content_frame,
            text="Ham sesler analiz ediliyor...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=("#333", "#EEE")
        )
        self.message_label.pack()
        
        # Animasyon başlat
        self._start_animation()
    
    def _start_animation(self):
        """Spinner animasyonu"""
        def animate():
            if self.winfo_exists():
                current_text = self.spinner_label.cget("text")
                # Basit dönen emoji animasyonu
                spinners = ["⏳", "⏰", "⏳", "⏰"]
                current_index = spinners.index(current_text) if current_text in spinners else 0
                next_index = (current_index + 1) % len(spinners)
                self.spinner_label.configure(text=spinners[next_index])
                self.after(500, animate)
        
        animate()
    
    def close(self):
        """Modal'ı kapat"""
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

