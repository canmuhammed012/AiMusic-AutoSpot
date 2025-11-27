"""Güncelleme bildirim modal penceresi"""

import customtkinter as ctk
import webbrowser
import subprocess
import os
import sys
from typing import Optional, Dict, Any, Callable
import logging

from ...constants import FONT_FAMILY, UIConfig, APP_NAME

logger = logging.getLogger(__name__)

class UpdateModal(ctk.CTkToplevel):
    """Güncelleme bildirim penceresi"""
    
    def __init__(
        self,
        parent,
        update_info: Dict[str, Any],
        current_version: str,
        on_install_now: Optional[Callable] = None,
        on_remind_later: Optional[Callable] = None,
        **kwargs
    ):
        """
        UpdateModal oluşturur.
        
        Args:
            parent: Parent window
            update_info: Güncelleme bilgisi dict'i
            current_version: Mevcut versiyon
            on_install_now: "Şimdi Al" callback'i
            on_remind_later: "Daha Sonra Hatırlat" callback'i
        """
        super().__init__(parent, **kwargs)
        
        self.update_info = update_info
        self.current_version = current_version
        self.download_url = update_info.get("download_url", "")
        self.release_url = update_info.get("release_url", "")
        self.new_version = update_info.get("version", "Bilinmiyor")
        self.on_install_now = on_install_now
        self.on_remind_later = on_remind_later
        
        self._setup_window()
        self._setup_ui()
    
    def _setup_window(self):
        """Pencere ayarlarını yapar"""
        self.title("Yeni Güncelleme Mevcut")
        modal_w, modal_h = 600, 500
        
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
        self.protocol("WM_DELETE_WINDOW", self._on_remind_later)
    
    def _setup_ui(self):
        """UI elemanlarını oluşturur"""
        main_frame = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#2D2E30"),
            corner_radius=20,
            border_width=2,
            border_color=("#E0E0E0", "#444")
        )
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=25)
        
        # Başlık - Büyük ve dikkat çekici
        title_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame,
            text=f"🎉 {APP_NAME} V{self.new_version} Yayınlandı!",
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
            text_color="#28A745"
        ).pack()
        
        # Sürüm notları başlığı
        notes_title = ctk.CTkLabel(
            content_frame,
            text="✨ Yeni Özellikler ve İyileştirmeler:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            anchor="w"
        )
        notes_title.pack(anchor="w", pady=(10, 10))
        
        # Sürüm notları - formatlanmış liste
        notes_frame = ctk.CTkScrollableFrame(content_frame, height=220)
        notes_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        release_notes = self.update_info.get("release_notes", "")
        
        # Sürüm notlarını parse et ve formatla
        formatted_notes = self._format_release_notes(release_notes)
        
        notes_text = ctk.CTkTextbox(
            notes_frame,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            wrap="word",
            fg_color=("#F8F9FA", "#1E1E1E"),
            border_width=1,
            border_color=("#E0E0E0", "#444"),
            corner_radius=10
        )
        notes_text.pack(fill="both", expand=True)
        notes_text.insert("1.0", formatted_notes)
        notes_text.configure(state="disabled")
        
        # Butonlar
        btn_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        # Güncellemeyi Şimdi Al butonu
        if self.download_url:
            install_btn = ctk.CTkButton(
                btn_frame,
                text="🚀 Güncellemeyi Şimdi Al",
                command=self._install_now,
                width=200,
                height=45,
                corner_radius=12,
                font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
                fg_color="#28A745",
                hover_color="#218838"
            )
            install_btn.pack(side="left", padx=(0, 10))
        
        # Daha Sonra Hatırlat butonu
        remind_btn = ctk.CTkButton(
            btn_frame,
            text="⏰ Daha Sonra Hatırlat",
            command=self._on_remind_later,
            width=200,
            height=45,
            corner_radius=12,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            fg_color="#6C757D",
            hover_color="#5A6268"
        )
        remind_btn.pack(side="right")
    
    def _format_release_notes(self, notes: str) -> str:
        """Sürüm notlarını formatlar ve emojiler ekler"""
        if not notes:
            return "• Geliştirilmiş performans\n• Hata düzeltmeleri\n• Genel iyileştirmeler"
        
        # Markdown formatını temizle
        notes = notes.replace("##", "").replace("###", "").replace("#", "").strip()
        
        # Satırları parse et
        lines = notes.split('\n')
        formatted_lines = []
        
        # Emoji mapping
        emoji_map = {
            "senkronizasyon": "🔄",
            "ses analizi": "🎵",
            "spot analiz": "🎯",
            "arayüz": "🎨",
            "bug": "🐛",
            "fix": "🔧",
            "geliştirme": "⚡",
            "iyileştirme": "✨",
            "performans": "🚀",
            "hata": "❌",
            "düzeltme": "✅"
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Bullet point kontrolü
            if line.startswith('-') or line.startswith('*') or line.startswith('•'):
                line = line.lstrip('-*•').strip()
            
            # Emoji ekle
            emoji = "•"
            line_lower = line.lower()
            for key, emoji_char in emoji_map.items():
                if key in line_lower:
                    emoji = emoji_char
                    break
            
            formatted_lines.append(f"{emoji} {line}")
        
        # Eğer formatlanmış satır yoksa, varsayılan formatla
        if not formatted_lines:
            formatted_lines = [
                "🔄 Geliştirilmiş Senkronizasyon",
                "🎵 Ses Analizi Geliştirmeleri",
                "🎯 Spot Analiz Geliştirmeleri",
                "🎨 Arayüz Güncellemeleri",
                "🐛 Bug Fix"
            ]
        
        return '\n'.join(formatted_lines)
    
    def _install_now(self):
        """Güncellemeyi şimdi yükle - programı kapat ve setup'ı çalıştır"""
        if self.download_url and self.on_install_now:
            self.on_install_now(self.download_url)
        elif self.download_url:
            # Fallback: tarayıcıda aç
            try:
                webbrowser.open(self.download_url)
                logger.info(f"İndirme linki açıldı: {self.download_url}")
            except Exception as e:
                logger.error(f"İndirme linki açılamadı: {e}")
            self._on_remind_later()
    
    def _on_remind_later(self):
        """Daha sonra hatırlat - flag'i kaydet"""
        if self.on_remind_later:
            self.on_remind_later(self.new_version, self.download_url)
        self._close()
    
    def _close(self):
        """Pencereyi kapat"""
        try:
            self.grab_release()
            self.destroy()
        except Exception:
            pass
