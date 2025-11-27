"""Montaj ilerleme modal penceresi"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable
import threading
import time
import logging

from ...constants import FONT_FAMILY, UIConfig

logger = logging.getLogger(__name__)

class ProgressModal(ctk.CTkToplevel):
    """Montaj ilerleme gösterimi için modal pencere"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.current_stage = 0
        self.stages = [
            "Ham Ses Analiz Ediliyor",
            "Fon Sesi Entegre Ediliyor",
            "Montaj Tamamlanıyor"
        ]
        self.stage_widgets = []
        self.is_completed = False
        self.spinner_angle = 0  # Kum saati döndürme açısı
        self.current_spot_info = ""  # Mevcut spot bilgisi
        self.animation_job = None  # Animasyon işi için referans
        
        self._setup_window()
        self._setup_ui()
        self._start_animation()
    
    def _setup_window(self):
        """Pencere ayarlarını yapar"""
        self.title("Montaj İşlemi")
        self.overrideredirect(True)  # Başlık çubuğunu kaldır
        
        modal_w, modal_h = 500, 500
        
        # Parent pencerenin konumunu ve boyutunu al
        parent = self.master
        parent.update_idletasks()
        
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        
        # Parent pencerenin merkezine göre konumlandır
        x = parent_x + (parent_w // 2 - modal_w // 2)
        y = parent_y + (parent_h // 2 - modal_h // 2)
        
        # Ekran dışına çıkmaması için kontrol et
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        
        if x < 0:
            x = 50
        if y < 0:
            y = 50
        if x + modal_w > screen_w:
            x = screen_w - modal_w - 50
        if y + modal_h > screen_h:
            y = screen_h - modal_h - 50
        
        self.geometry(f"{modal_w}x{modal_h}+{x}+{y}")
        self.grab_set()
        self.resizable(False, False)
        
        # Arka plan blur efekti için parent'ı koyulaştır
        self._blur_background()
    
    def _blur_background(self):
        """Arka planı blur efekti ile koyulaştır"""
        try:
            # Parent penceresine overlay ekle (yarı saydam siyah)
            # CustomTkinter'da opacity doğrudan desteklenmediği için koyu gri kullanıyoruz
            self.overlay = ctk.CTkFrame(
                self.parent,
                fg_color=("#333333", "#1A1A1A")  # Koyu gri (yarı saydam efekti)
            )
            self.overlay.place(x=0, y=0, relwidth=1, relheight=1)
            self.overlay.lift()
            # Opacity efekti için tkinter canvas kullanılabilir ama şimdilik koyu overlay yeterli
        except Exception as e:
            logger.debug(f"Blur efekti uygulanamadı: {e}")
    
    def _setup_ui(self):
        """UI elemanlarını oluşturur"""
        # Ana container
        main_frame = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#2D2E30"),
            corner_radius=20,
            border_width=2,
            border_color=("#E0E0E0", "#444")
        )
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # İçerik frame (scrollable olabilir)
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=20)
        content_frame.grid_rowconfigure(1, weight=1)  # Aşamalar genişleyebilir
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Üst kısım (çark ve aşamalar)
        top_section = ctk.CTkFrame(content_frame, fg_color="transparent")
        top_section.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        # En üstte dönen kum saati
        self.top_spinner = ctk.CTkLabel(
            top_section,
            text="⏳",
            font=ctk.CTkFont(family=FONT_FAMILY, size=48),
            text_color="#007BFF"
        )
        self.top_spinner.pack(pady=(0, 15))
        
        # Aşamalar
        self.stages_frame = ctk.CTkFrame(top_section, fg_color="transparent")
        self.stages_frame.pack(fill="x", pady=(0, 10))
        
        for i, stage_text in enumerate(self.stages):
            stage_row = self._create_stage_row(stage_text, i)
            self.stage_widgets.append(stage_row)
            stage_row.pack(fill="x", pady=6)
        
        # Spot bilgisi label'ı (aşamaların altında)
        self.spot_info_label = ctk.CTkLabel(
            top_section,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color="#007BFF",
            wraplength=400,
            justify="center"
        )
        self.spot_info_label.pack(pady=(10, 0))
        
        # Orta kısım (sonuç mesajı - başlangıçta gizli)
        self.result_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        self.result_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        
        self.result_emoji = ctk.CTkLabel(
            self.result_frame,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=36)
        )
        self.result_emoji.pack(pady=(5, 5))
        
        self.result_label = ctk.CTkLabel(
            self.result_frame,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color="gray60",
            wraplength=400,
            justify="center"
        )
        self.result_label.pack(pady=(0, 5))
        
        # Alt kısım (buton - sabit altta)
        bottom_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        bottom_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        # İptal butonu (işlem devam ederken görünür)
        self.cancel_button = ctk.CTkButton(
            bottom_frame,
            text="✕ İptal Et",
            command=self._on_cancel_clicked,
            width=220,
            height=45,
            corner_radius=12,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            fg_color="#DC3545",
            hover_color="#C82333",
            text_color="#FFFFFF",
            border_width=0
        )
        self.cancel_button.pack(pady=(0, 5))
        
        # Tamamla butonu (başlangıçta gizli)
        self.complete_button = ctk.CTkButton(
            bottom_frame,
            text="✓ Tamamla",
            command=self._on_complete_clicked,
            width=220,
            height=45,
            corner_radius=12,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            fg_color="#28A745",
            hover_color="#218838",
            text_color="#FFFFFF",
            border_width=0
        )
        self.complete_button.pack()
        
        # Başlangıçta gizli
        self.result_frame.grid_remove()
        self.complete_button.pack_forget()
    
    def _create_stage_row(self, text: str, index: int):
        """Aşama satırı oluşturur"""
        row = ctk.CTkFrame(self.stages_frame, fg_color="transparent")
        
        # İkon (kum saati veya tik)
        icon_label = ctk.CTkLabel(
            row,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20),
            text_color="#007BFF",
            width=30
        )
        icon_label.pack(side="left", padx=(0, 12))
        
        # Metin
        text_label = ctk.CTkLabel(
            row,
            text=text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            anchor="w"
        )
        text_label.pack(side="left", fill="x", expand=True)
        
        # Widget referanslarını sakla
        row.icon_label = icon_label
        row.text_label = text_label
        row.is_completed = False
        row.spinner_angle = 0  # Her aşama için ayrı animasyon açısı
        
        return row
    
    def _start_animation(self):
        """Dönen çark animasyonunu başlat"""
        self._animate_spinner()
    
    def _animate_spinner(self):
        """Kum saati animasyonu - sürekli dönen kum saati"""
        if self.is_completed:
            return
        
        # Kum saati döndürme animasyonu (sürekli dönsün)
        # Dönen kum saati karakterleri: ⏳ → ⏲ → ⏳ (tersine çevirme efekti)
        hourglass_chars = ["⏳", "⏲"]
        self.spinner_angle = (self.spinner_angle + 1) % len(hourglass_chars)
        current_hourglass = hourglass_chars[self.spinner_angle]
        
        # Üst spinner'ı sürekli döndür
        self.top_spinner.configure(text=current_hourglass)
        
        # Aktif aşamalar için kum saati göster (henüz tamamlanmamış olanlar)
        for i, row in enumerate(self.stage_widgets):
            if not row.is_completed:
                # Aktif aşama için kum saati göster
                row.icon_label.configure(text=current_hourglass, text_color="#007BFF")
            else:
                # Tamamlanmış aşamalar için tik işareti
                row.icon_label.configure(text="✓", text_color="#28A745")
        
        # 150ms sonra tekrar çağır (sürekli dönsün, duraksamadan - daha hızlı)
        self.animation_job = self.after(150, self._animate_spinner)
    
    def _update_hourglass(self):
        """Kum saati emojisini güncelle - sadece kum saati göster (artık kullanılmıyor, _animate_spinner kullanılıyor)"""
        # Bu fonksiyon artık kullanılmıyor, _animate_spinner sürekli animasyonu yönetiyor
        pass
    
    def _flip_hourglass(self):
        """Kum saatini tersine çevir (artık kullanılmıyor, _animate_spinner sürekli animasyonu yönetiyor)"""
        # Bu fonksiyon artık kullanılmıyor, _animate_spinner sürekli animasyonu yönetiyor
        pass
    
    def update_stage(self, stage_index: int):
        """Aşamayı tamamlandı olarak işaretle"""
        if 0 <= stage_index < len(self.stage_widgets):
            row = self.stage_widgets[stage_index]
            if not row.is_completed:
                # Tüm aşamalar için aynı işlem: tamamlandı olarak işaretle
                def set_completed():
                    row.icon_label.configure(text="✓", text_color="#28A745")
                    row.is_completed = True
                    self.current_stage = stage_index + 1
                
                # Kısa bir gecikme ile tik göster (animasyon efekti)
                self.after(300, set_completed)
    
    def update_spot_info(self, spot_info: str):
        """Spot bilgisini güncelle (örn: "Spot 2/5 işleniyor...")"""
        self.current_spot_info = spot_info
        if spot_info:
            self.spot_info_label.configure(text=spot_info)
            self.spot_info_label.pack(pady=(10, 0))
        else:
            self.spot_info_label.pack_forget()
    
    def show_completion(self, message: str):
        """Tamamlanma mesajını göster"""
        self.is_completed = True
        
        # Animasyonu durdur
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        
        # Üst spinner'ı durdur (kum saati kalabilir veya boş bırakılabilir)
        self.top_spinner.configure(text="✓", text_color="#28A745")
        
        # Sonuç frame'ini göster
        self.result_frame.grid()
        self.result_emoji.configure(text="✓")  # Sadece tik işareti, emoji yok
        self.result_label.configure(text=message, text_color="#28A745")
        
        # İptal butonunu gizle, tamamla butonunu göster
        self.cancel_button.pack_forget()
        self.complete_button.pack(pady=(10, 0))
    
    def _on_cancel_clicked(self):
        """İptal butonuna tıklandığında"""
        # Parent window'daki iptal metodunu çağır
        if hasattr(self.parent, '_cancel_montaj'):
            self.parent._cancel_montaj()
        
        # İptal butonunu devre dışı bırak ve metni değiştir
        self.cancel_button.configure(
            state="disabled",
            text="İptal ediliyor...",
            text_color="#FFFFFF"
        )
    
    def _on_complete_clicked(self):
        """Tamamla butonuna tıklandığında"""
        self.destroy()
    
    def destroy(self):
        """Pencereyi kapat ve blur'u temizle"""
        try:
            if hasattr(self, 'overlay'):
                self.overlay.destroy()
        except Exception:
            pass
        
        try:
            self.grab_release()
        except Exception:
            pass
        
        super().destroy()

