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
        status_frame.pack(fill="x", pady=(0, 10))
        status_frame.grid_columnconfigure(0, weight=1)
        
        # "Montaja Başlamak İçin Dosyaları Seçin" yazısı (ortalanmış, her zaman görünür)
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Montaja Başlamak İçin Dosyaları Seçin",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color="gray60",
            height=30
        )
        self.status_label.grid(row=0, column=0, sticky="")
        
        # İlerleme çubuğu (dosya seçim aşaması için)
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(pady=(0, 8))  # fill="x" kaldırıldı, genişleme yok
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar container (4 kademe için)
        bar_container = ctk.CTkFrame(progress_frame, fg_color="transparent")
        bar_container.grid(row=0, column=0, sticky="", pady=(0, 8))
        
        # 4 kademe göstergesi (progress bar üstünde)
        steps_frame = ctk.CTkFrame(bar_container, fg_color="transparent")
        steps_frame.grid(row=0, column=0, sticky="", pady=(0, 5))
        steps_frame.grid_columnconfigure(0, weight=1)
        steps_frame.grid_columnconfigure(1, weight=1)
        steps_frame.grid_columnconfigure(2, weight=1)
        steps_frame.grid_columnconfigure(3, weight=1)
        
        self.step_labels = []
        for i in range(4):
            step_label = ctk.CTkLabel(
                steps_frame,
                text=str(i + 1),
                font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
                text_color=("#666", "#999"),
                width=30,
                height=25
            )
            # Her adımı eşit aralıklarla yerleştir
            step_label.grid(row=0, column=i, sticky="")
            self.step_labels.append(step_label)
        
        # Ana progress bar (sabit genişlik)
        self.selection_progress_bar = ctk.CTkProgressBar(bar_container, mode="determinate", width=280)
        self.selection_progress_bar.grid(row=1, column=0, sticky="", ipady=5)
        self.selection_progress_bar.set(0)
        
        # Adım mesajı (progress bar altında) - Sabit yükseklik
        message_container = ctk.CTkFrame(progress_frame, fg_color="transparent")
        message_container.grid(row=1, column=0, sticky="")
        message_container.configure(height=50)  # Sabit yükseklik (opsiyonel mesaj için yer)
        message_container.grid_propagate(False)  # Grid için yüksekliği sabit tut
        
        self.step_message_label = ctk.CTkLabel(
            message_container,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=("#333", "#EEE"),
            height=25,
            wraplength=280  # Metin genişliğini sınırla (progress bar genişliğiyle uyumlu)
        )
        self.step_message_label.grid(row=0, column=0, sticky="")
        
        # Adım 3 için ek mesaj (opsiyonel bilgi) - Her zaman görünür, boş text ile yer kaplar
        self.step_optional_label = ctk.CTkLabel(
            message_container,
            text=" ",  # Boşluk karakteri ile yer kaplar
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),  # Daha büyük ve bold
            text_color=("gray50", "gray70"),
            height=20,
            wraplength=280  # Metin genişliğini sınırla
        )
        self.step_optional_label.grid(row=1, column=0, sticky="", pady=(2, 0))
        
        # Montaj ilerleme çubuğu (montaj sırasında kullanılacak)
        montage_progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        montage_progress_frame.pack(fill="x", pady=(5, 0))
        montage_progress_frame.grid_columnconfigure(0, weight=1)
        montage_progress_frame.grid_columnconfigure(1, weight=0)
        montage_progress_frame.pack_forget()  # Başlangıçta gizli
        
        self.progress_bar = ctk.CTkProgressBar(montage_progress_frame, mode="determinate")
        self.progress_bar.grid(row=0, column=0, sticky="ew", ipady=2)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            montage_progress_frame,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=("#333", "#EEE")
        )
        self.progress_label.grid(row=0, column=1, padx=(5, 0), sticky="e")
        
        # Frame referanslarını sakla
        self.progress_frame = progress_frame
        self.montage_progress_frame = montage_progress_frame
        
        # Aksiyon butonları
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame = action_frame  # Action frame referansını sakla
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
        """
        Durum etiketini günceller (artık kullanılmıyor, status_label sabit kalıyor)
        Bu fonksiyon geriye dönük uyumluluk için boş bırakıldı.
        """
        # Status label artık sabit "Montaja Başlamak İçin Dosyaları Seçin" olarak kalıyor
        # Durum mesajları artık step_message_label'da gösteriliyor
        pass
    
    def update_selection_progress(self, step: int, total_steps: int = 4):
        """
        Dosya seçim aşaması progress bar'ını günceller.
        
        Args:
            step: Mevcut adım (0-4, 0 = hiçbir şey seçili değil)
            total_steps: Toplam adım sayısı (varsayılan 4)
        """
        progress = (step / total_steps) * 100 if step > 0 else 0
        self.selection_progress_bar.set(progress / 100.0)
        
        # Adım mesajları (bir sonraki adımın mesajını göster)
        # step=0 → Adım 1 mesajı, step=1 → Adım 2 mesajı, vb.
        step_messages = {
            1: "Adım 1: Ham Sesinizi Yükleyiniz!",
            2: "Adım 2: Lütfen Fon Seçiniz ya da Yükleyiniz.",
            3: "Adım 3: Lütfen Bitiş Sesinizi Seçiniz ya da Yükleyiniz.",
            4: "Adım 4: Montajı Başlatabilirsiniz!"
        }
        
        # Status label her zaman görünür (text değişmez, sabit kalır)
        self.status_label.grid()
        
        # Bir sonraki adımın mesajını göster (step+1)
        # step=0 → Adım 1 mesajı, step=1 → Adım 2 mesajı, vb.
        next_step = step + 1
        if next_step <= 4:
            current_message = step_messages.get(next_step, "")
        else:
            # step=4 ise (montaj başladı) özel mesaj
            current_message = "Montaj başlatılıyor..."
        
        self.step_message_label.configure(text=current_message)
        
        # Adım 3 için opsiyonel bilgi mesajı (parantez içinde, bold ve büyük punto)
        if next_step == 3:
            self.step_optional_label.configure(
                text="(Dilerseniz yalnızca Ham Ses ve Fon Müzik ile montajı başlatabilirsiniz.)",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold")  # Bold ve büyük punto
            )
        else:
            # Görünmez yap ama yer kaplamaya devam et (boşluk karakteri)
            self.step_optional_label.configure(text=" ")
        
        # Adım numaralarını vurgula
        for i, label in enumerate(self.step_labels):
            if i < step:
                # Tamamlanan adımlar
                label.configure(
                    text_color="#28A745",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold")
                )
            elif i == step - 1:
                # Mevcut adım
                label.configure(
                    text_color="#007BFF",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold")
                )
            else:
                # Gelecek adımlar
                label.configure(
                    text_color=("#666", "#999"),
                    font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold")
                )
    
    def update_progress(self, value: int, message: str = ""):
        """
        Montaj ilerleme çubuğunu günceller.
        
        Args:
            value: İlerleme değeri (0-100)
            message: Durum mesajı
        """
        # Dosya seçim progress bar'ını gizle, montaj progress bar'ını göster
        if value > 0:
            self.progress_frame.pack_forget()
            # Progress bar'ı action frame'den önce (üstünde) göstermek için
            # Action frame'i geçici olarak kaldırıp, progress bar'ı ekleyip, sonra action frame'i tekrar ekle
            action_pack_info = self.action_frame.pack_info()
            self.action_frame.pack_forget()
            self.montage_progress_frame.pack(fill="x", pady=(5, 0))
            # Action frame'i tekrar ekle (progress bar'ın altına)
            self.action_frame.pack(**action_pack_info)
        
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
            # Montaj progress bar'ını gizle, dosya seçim progress bar'ını göster
            self.montage_progress_frame.pack_forget()
            self.progress_frame.pack(fill="x", pady=(5, 0))
            
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

