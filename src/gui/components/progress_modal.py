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
        self.spinner_angle = 0  # Çark döndürme açısı
        self.current_spot_info = ""  # Mevcut spot bilgisi
        self.hourglass_flipped = False  # Kum saati ters durumu
        self.montage_stage_active = False  # "Montaj Tamamlanıyor" aşaması aktif mi?
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
        
        # En üstte dönen çark
        self.top_spinner = ctk.CTkLabel(
            top_section,
            text="⚙",
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
        
        # İkon (çark veya tik)
        icon_label = ctk.CTkLabel(
            row,
            text="⚙",
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
        """Çark animasyonu - üst çark ve aktif aşamalar için"""
        if self.is_completed:
            return
        
        # "Montaj Tamamlanıyor" aşaması aktifse normal animasyonu tamamen durdur
        # Sadece kum saati animasyonu çalışacak
        if self.montage_stage_active:
            # Diğer tüm aşamaların ikonlarını kontrol et ve emoji görünmesin
            for i, row in enumerate(self.stage_widgets):
                if i < 2:  # İlk iki aşama
                    if row.is_completed:
                        row.icon_label.configure(text="✓", text_color="#28A745")
                    else:
                        row.icon_label.configure(text="", text_color="#28A745")
            return  # Kum saati animasyonu _flip_hourglass tarafından yönetiliyor
        
        # Normal animasyon (diğer aşamalar için)
        # Üst çark animasyonu (Unicode döndürme karakterleri)
        spinner_chars = ["⚙", "⏳", "⏰", "🔄"]
        self.spinner_angle = (self.spinner_angle + 1) % len(spinner_chars)
        self.top_spinner.configure(text=spinner_chars[self.spinner_angle])
        
        # Aktif aşamalar için çark animasyonu (henüz tamamlanmamış olanlar)
        for i, row in enumerate(self.stage_widgets):
            if not row.is_completed:
                # "Montaj Tamamlanıyor" aşaması değilse normal animasyon
                if i != 2:
                    # Her aşama için ayrı animasyon açısı
                    if not hasattr(row, 'spinner_angle'):
                        row.spinner_angle = 0
                    row.spinner_angle = (row.spinner_angle + 1) % len(spinner_chars)
                    row.icon_label.configure(text=spinner_chars[row.spinner_angle])
        
        # 100ms sonra tekrar çağır ve job ID'yi sakla
        self.animation_job = self.after(100, self._animate_spinner)
    
    def _update_hourglass(self):
        """Kum saati emojisini güncelle - sadece kum saati göster"""
        if not self.montage_stage_active or self.is_completed:
            return
        
        # Kum saati emojileri: ⏳ (normal) ve ⏲ (akışlı kum - ters görünümlü)
        # Baş aşağı dönme efekti için bu iki emoji arasında geçiş yapıyoruz
        if self.hourglass_flipped:
            hourglass_emoji = "⏲"  # Akışlı kum saati (ters görünümlü)
        else:
            hourglass_emoji = "⏳"  # Normal kum saati
        
        # Üst spinner'ı sadece kum saati yap (diğer emojiler görünmesin)
        self.top_spinner.configure(text=hourglass_emoji)
        
        # "Montaj Tamamlanıyor" aşamasının ikonunu sadece kum saati yap
        if len(self.stage_widgets) > 2:
            montage_row = self.stage_widgets[2]  # Index 2 = "Montaj Tamamlanıyor"
            if not montage_row.is_completed:
                montage_row.icon_label.configure(text=hourglass_emoji)
        
        # Diğer tüm aşamaların ikonlarını kontrol et - emoji görünmemeli
        for i, other_row in enumerate(self.stage_widgets):
            if i < 2:  # İlk iki aşama
                if other_row.is_completed:
                    # Tamamlanmış aşamalar için tik işareti
                    other_row.icon_label.configure(text="✓", text_color="#28A745")
                else:
                    # Tamamlanmamış aşamalar için boş (hiçbir emoji görünmesin)
                    other_row.icon_label.configure(text="", text_color="#28A745")
    
    def _flip_hourglass(self):
        """Kum saatini tersine çevir (2 saniyede bir)"""
        if self.montage_stage_active and not self.is_completed:
            self.hourglass_flipped = not self.hourglass_flipped
            # Kum saati emojisini güncelle
            self._update_hourglass()
            # 2 saniye sonra tekrar tersine çevir
            self.after(2000, self._flip_hourglass)
    
    def update_stage(self, stage_index: int):
        """Aşamayı tamamlandı olarak işaretle"""
        if 0 <= stage_index < len(self.stage_widgets):
            row = self.stage_widgets[stage_index]
            if not row.is_completed:
                # "Montaj Tamamlanıyor" aşaması (index 2) için özel işlem
                if stage_index == 2:
                    # Bu aşamada sadece kum saati animasyonu başlat
                    self.montage_stage_active = True
                    self.hourglass_flipped = False
                    
                    # Bekleyen animasyon işlerini iptal et
                    if self.animation_job:
                        self.after_cancel(self.animation_job)
                        self.animation_job = None
                    
                    # Diğer aşamaların animasyonlarını durdur (sadece kum saati görünsün)
                    # Diğer aşamaların (0 ve 1) ikonlarını sabit tut - HİÇBİR EMOJİ GÖRÜNMESİN
                    for i, other_row in enumerate(self.stage_widgets):
                        if i < 2:
                            # Diğer aşamaların ikonlarını tamamen gizle veya sabit tut
                            if other_row.is_completed:
                                # Tamamlanmış aşamalar için tik işareti göster
                                other_row.icon_label.configure(text="✓", text_color="#28A745")
                            else:
                                # Tamamlanmamış aşamalar için ikonu tamamen gizle
                                # Veya boş string yap - hiçbir emoji görünmesin
                                other_row.icon_label.configure(text="", text_color="#28A745")
                    
                    # Spot bilgisi label'ını gizle
                    self.spot_info_label.pack_forget()
                    
                    # Üst spinner'ı hemen kum saati yap (diğer emojiler görünmesin)
                    self.top_spinner.configure(text="⏳")
                    
                    # "Montaj Tamamlanıyor" aşamasının ikonunu kum saati yap
                    row.icon_label.configure(text="⏳")
                    
                    # İlk kum saati güncellemesi (hemen başlat)
                    self._update_hourglass()
                    # 2 saniye sonra tersine çevir
                    self.after(2000, self._flip_hourglass)
                else:
                    # Diğer aşamalar için normal işlem
                    # Önce çarkı göster, sonra tik'e geç
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
        
        # Üst çarkı durdur ve kutlama emoji göster
        self.top_spinner.configure(text="🎉", text_color="#28A745")
        
        # Sonuç frame'ini göster
        self.result_frame.grid()
        self.result_emoji.configure(text="✅")
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

