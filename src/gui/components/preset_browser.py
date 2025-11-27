"""Preset fon müziği tarayıcı penceresi - Profesyonel versiyon"""

import os
import shutil
import subprocess
import sys
import customtkinter as ctk
from tkinter import messagebox
from typing import List, Optional, Callable
import logging
import threading
import time

# Windows için pencere yönetimi (opsiyonel)
try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from ...constants import FONT_FAMILY, PRESET_CATEGORIES, ENDING_CATEGORIES, UIConfig
from ...utils.file_utils import get_resource_path

logger = logging.getLogger(__name__)

class PresetBrowser(ctk.CTkToplevel):
    """Preset fon müziği seçim penceresi - Modern tasarım"""
    
    def __init__(
        self,
        parent,
        on_selection: Callable[[List[str]], None],
        total_spots: Optional[int] = None,
        categories: Optional[dict] = None,
        title: Optional[str] = None,
        default_category: Optional[str] = None,
        **kwargs
    ):
        """
        PresetBrowser oluşturur.
        
        Args:
            parent: Parent window
            on_selection: Seçim callback'i (seçilen dosya yolları listesi)
            total_spots: Toplam spot sayısı (tek spot kısıtı için)
            categories: Kategori sözlüğü (None ise PRESET_CATEGORIES kullanılır)
            title: Pencere başlığı (None ise varsayılan kullanılır)
            default_category: Varsayılan seçili kategori (None ise ilk kategori kullanılır)
        """
        super().__init__(parent, **kwargs)
        
        self.on_selection = on_selection
        self.total_spots = total_spots
        self.categories = categories if categories is not None else PRESET_CATEGORIES
        self.window_title = title if title is not None else "Fon Müziği Kataloğu"
        self.default_category = default_category
        self.selected_presets = set()
        self._preview_proc = None
        self._preview_btn = None
        self._is_closing = False
        self._preview_path = None
        
        self._setup_window()
        self._setup_ui()
    
    def _setup_window(self):
        """Pencere ayarlarını yapar"""
        self.title(self.window_title)
        modal_w, modal_h = 700, 600
        
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
        
        # Kapatma handler'ı (X butonu ile kapanınca iptal gibi davran)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _setup_ui(self):
        """UI elemanlarını oluşturur"""
        # Ana container - grid kullanarak butonlar için alan ayır
        main_frame = ctk.CTkFrame(self, fg_color=("#F8F9FA", "#1E1E1E"))
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_rowconfigure(0, weight=0)  # Başlık - sabit
        main_frame.grid_rowconfigure(1, weight=0)  # Kategoriler - sabit
        main_frame.grid_rowconfigure(2, weight=1)   # Liste - genişleyebilir
        main_frame.grid_rowconfigure(3, weight=0)  # Butonlar - sabit
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Başlık (daha büyük ve modern)
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"🎵 {self.window_title}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF")
        )
        title_label.pack(anchor="center")
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Kategori seçin ve müzikleri dinleyin",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color="gray60"
        )
        subtitle_label.pack(anchor="center", pady=(5, 0))
        
        # Kategori butonları (her satıra 4 adet)
        # Varsayılan kategori: default_category varsa onu kullan, yoksa ilk kategoriyi kullan
        categories_list = list(self.categories.keys())
        default_cat = self.default_category if self.default_category and self.default_category in categories_list else (categories_list[0] if categories_list else "AI Music")
        self.cat_var = ctk.StringVar(value=default_cat)
        cats_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        cats_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        cats_frame.grid_columnconfigure(0, weight=1)
        cats_frame.grid_columnconfigure(1, weight=1)
        cats_frame.grid_columnconfigure(2, weight=1)
        cats_frame.grid_columnconfigure(3, weight=1)
        
        self.cat_buttons = {}
        categories = list(self.categories.keys())
        
        # Kategori butonları için sabit boyutlar
        btn_width = 150
        btn_font_size = 12
        
        # Her satıra 4 kategori yerleştir
        for i, name in enumerate(categories):
            row = i // 4  # Satır numarası (0, 1, 2, ...)
            col = i % 4   # Sütun numarası (0, 1, 2, 3)
            
            btn = ctk.CTkButton(
                cats_frame,
                text=name,
                width=btn_width,
                height=38,
                corner_radius=10,
                font=ctk.CTkFont(family=FONT_FAMILY, size=btn_font_size, weight="bold"),
                border_width=2,
                command=lambda n=name: self._on_category_change(n)
            )
            btn.grid(row=row, column=col, padx=8, pady=5, sticky="ew")
            self.cat_buttons[name] = btn
        
        self._update_category_styles()
        
        # Liste container
        self.list_container = ctk.CTkScrollableFrame(
            main_frame,
            fg_color=("#FFFFFF", "#2D2D2D"),
            corner_radius=12
        )
        self.list_container.grid(row=2, column=0, sticky="nsew", pady=(0, 15))
        
        # Butonlar (daha belirgin ve görünür) - her zaman görünür olmalı
        btn_frame = ctk.CTkFrame(
            main_frame,
            fg_color=("#F8F9FA", "#2D2D2D"),
            corner_radius=10,
            border_width=1,
            border_color=("#DEE2E6", "#444"),
            height=80  # Sabit yükseklik
        )
        btn_frame.grid(row=3, column=0, sticky="ew", pady=(0, 0))
        btn_frame.grid_propagate(False)  # Yüksekliği koru
        
        # İçerik frame - grid kullanarak daha iyi kontrol
        btn_content = ctk.CTkFrame(btn_frame, fg_color="transparent")
        btn_content.pack(fill="both", expand=True, padx=20, pady=15)
        btn_content.grid_columnconfigure(0, weight=1)
        btn_content.grid_columnconfigure(1, weight=1)
        
        cancel_btn = ctk.CTkButton(
            btn_content,
            text="✕ İptal Et",
            command=self._on_cancel,
            height=48,
            corner_radius=10,
            fg_color="#DC3545",
            hover_color="#C82333",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            border_width=0
        )
        cancel_btn.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        apply_btn = ctk.CTkButton(
            btn_content,
            text="✓ Seçimleri Onayla",
            command=self._apply_selection,
            height=48,
            corner_radius=10,
            fg_color="#28A745",
            hover_color="#218838",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            border_width=0
        )
        apply_btn.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        # İlk kategoriyi yükle
        self._refresh_list()
    
    def _on_category_change(self, category: str):
        """Kategori değişim handler'ı"""
        if self._is_closing:
            return
        self.cat_var.set(category)
        self._update_category_styles()
        self._stop_preview()
        self._refresh_list()
    
    def _update_category_styles(self):
        """Kategori buton stillerini günceller"""
        selected = self.cat_var.get()
        for name, btn in self.cat_buttons.items():
            if name == selected:
                btn.configure(
                    fg_color="#007BFF",
                    hover_color="#0056B3",
                    border_color="#0056B3",
                    border_width=2
                )
            else:
                btn.configure(
                    fg_color=("#E9ECEF", "#3D3D3D"),
                    hover_color=("#DEE2E6", "#4D4D4D"),
                    border_color=("#CED4DA", "#5D5D5D"),
                    border_width=2
                )
    
    def _refresh_list(self):
        """Preset listesini yeniler"""
        if self._is_closing:
            return
        
        # Mevcut widget'ları temizle
        try:
            for widget in list(self.list_container.winfo_children()):
                try:
                    widget.pack_forget()
                    widget.destroy()
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Widget temizleme hatası: {e}")
        
        category = self.cat_var.get()
        relative_path = self.categories[category]
        folder = get_resource_path(relative_path)
        folder = os.path.normpath(folder)
        
        logger.info(f"Preset kategori: {category}, Klasör: {folder}")
        
        if not os.path.exists(folder) or not os.path.isdir(folder):
            error_label = ctk.CTkLabel(
                self.list_container,
                text=f"❌ Klasör bulunamadı:\n{folder}",
                text_color="#E74C3C",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                justify="left"
            )
            error_label.pack(pady=30, padx=20)
            return
        
        # Dosyaları bul ve doğal sıralama ile sırala
        try:
            all_files = os.listdir(folder)
            items = []
            for f in all_files:
                file_path = os.path.join(folder, f)
                if os.path.isfile(file_path) and f.lower().endswith((".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg")):
                    items.append(file_path)
            
            # Doğal sıralama (natural sort) - sayısal değerleri dikkate alarak
            def natural_sort_key(path):
                """Doğal sıralama için key fonksiyonu"""
                filename = os.path.basename(path).lower()
                # Sayıları ve metinleri ayır
                import re
                parts = []
                for part in re.split(r'(\d+)', filename):
                    if part.isdigit():
                        parts.append((0, int(part)))  # Sayılar için (0, sayı)
                    else:
                        parts.append((1, part.lower()))  # Metinler için (1, metin)
                return parts
            
            items.sort(key=natural_sort_key)
            
            logger.info(f"Bulunan {len(items)} ses dosyası (doğal sıralama ile)")
            
            if not items:
                error_label = ctk.CTkLabel(
                    self.list_container,
                    text="📭 Bu kategoride ses dosyası bulunamadı.",
                    text_color="#6C757D",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=13)
                )
                error_label.pack(pady=30, padx=20)
                return
            
            # Her dosya için satır oluştur
            for path in items:
                self._create_preset_row(path)
                
        except Exception as e:
            logger.error(f"Liste yenileme hatası: {e}", exc_info=True)
            error_label = ctk.CTkLabel(
                self.list_container,
                text=f"❌ Hata: {str(e)}",
                text_color="#E74C3C",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12)
            )
            error_label.pack(pady=30, padx=20)
    
    def _create_preset_row(self, path: str):
        """Preset satırı oluşturur - Modern tasarım"""
        if self._is_closing:
            return
        
        name = os.path.basename(path)
        is_selected = path in self.selected_presets
        
        # Kompakt satır kartı
        row = ctk.CTkFrame(
            self.list_container,
            fg_color=("#F8F9FA", "#3D3D3D") if not is_selected else ("#E7F3FF", "#1E3A5F"),
            corner_radius=8,
            border_width=2 if is_selected else 1,
            border_color="#007BFF" if is_selected else ("#DEE2E6", "#5D5D5D")
        )
        row.pack(fill="x", pady=3, padx=5)
        # Path'i row'a sakla (seçim toggle'da kullanmak için)
        row._preset_path = path
        
        # Kompakt içerik container
        content_frame = ctk.CTkFrame(row, fg_color="transparent")
        content_frame.pack(fill="x", padx=8, pady=6)
        
        # Sol taraf: Seçim + Oynat + İsim
        left_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True)
        
        # Seçim işareti (kompakt)
        check_text = "✓" if is_selected else "○"
        check_label = ctk.CTkLabel(
            left_frame,
            text=check_text,
            width=20,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            text_color="#28A745" if is_selected else "#6C757D"
        )
        check_label.pack(side="left", padx=(0, 8))
        
        # Oynat butonu (kompakt) - sistem mavisi ve sabit genişlik
        def make_preview_command(file_path):
            def preview_cmd():
                for widget in row.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkFrame):
                                for btn in child.winfo_children():
                                    if isinstance(btn, ctk.CTkButton) and btn.cget("text") in ("▶", "⏸"):
                                        self._toggle_preview(file_path, btn)
                                        return
            return preview_cmd
        
        # Play/Pause ikonları - aynı genişlikte
        is_playing = self._preview_path == path
        play_icon = "⏸" if is_playing else "▶"
        
        play_btn = ctk.CTkButton(
            left_frame,
            text=play_icon,
            width=38,  # Sabit genişlik (pause ikonu için yeterli)
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color="#007BFF" if not is_playing else "#DC3545",  # Sistem mavisi / Kırmızı (pause)
            hover_color="#0056B3" if not is_playing else "#C82333",
            text_color="#FFFFFF",
            command=make_preview_command(path)
        )
        play_btn.pack(side="left", padx=(0, 10))
        
        # Dosya adı (kompakt)
        name_label = ctk.CTkLabel(
            left_frame,
            text=name,
            anchor="w",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=("#1A1A1A", "#FFFFFF")
        )
        name_label.pack(side="left", fill="x", expand=True)
        
        # Sağ taraf: Seç butonu (kompakt)
        select_btn = ctk.CTkButton(
            content_frame,
            text="✓" if is_selected else "Seç",
            width=70,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color="#28A745" if is_selected else "#6C757D",
            hover_color="#218838" if is_selected else "#5A6268",
            command=lambda p=path: self._toggle_select(p, select_btn, check_label, row)
        )
        select_btn.pack(side="right")
    
    def _toggle_preview(self, path: str, btn: ctk.CTkButton):
        """Önizleme toggle"""
        if self._is_closing:
            return
        if self._preview_proc and self._preview_proc.poll() is None and self._preview_path == path:
            self._stop_preview()
        else:
            self._start_preview(path, btn)
    
    def _start_preview(self, path: str, btn: ctk.CTkButton):
        """Önizlemeyi başlat - Ses çıkışı ile"""
        if self._is_closing:
            return
        try:
            self._stop_preview()
            
            # ffplay'i bul
            ffplay_path = shutil.which("ffplay")
            
            if not ffplay_path:
                from ...utils.file_utils import get_resource_path
                project_ffplay = get_resource_path("ffmpeg/bin/ffplay.exe")
                if os.path.exists(project_ffplay):
                    ffplay_path = project_ffplay
            
            if not ffplay_path:
                import tempfile
                temp_ffplay = os.path.join(tempfile.gettempdir(), "ses_montaj_ffmpeg", "ffplay.exe")
                if os.path.exists(temp_ffplay):
                    ffplay_path = temp_ffplay
            
            if not ffplay_path or not os.path.exists(ffplay_path):
                messagebox.showwarning(
                    "Önizleme Hatası",
                    "FFplay bulunamadı. Ses önizlemesi yapılamıyor."
                )
                return
            
            logger.info(f"FFplay ile önizleme başlatılıyor: {ffplay_path}")
            
            # Pencere açılmadan ses çıkışı için -nodisp kullan
            # Windows'ta CREATE_NO_WINDOW flag'i ile tamamen gizli çalıştır
            startupinfo = None
            creationflags = 0
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW
            
            self._preview_proc = subprocess.Popen(
                [
                    ffplay_path,
                    "-nodisp",  # Pencere gösterme
                    "-autoexit",  # Otomatik kapan
                    "-loglevel", "quiet",  # Log yok
                    "-volume", "80",  # Ses seviyesi
                    path
                ],
                startupinfo=startupinfo,
                creationflags=creationflags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self._preview_btn = btn
            self._preview_path = path
            btn.configure(text="⏸", fg_color="#DC3545", hover_color="#C82333")
            
            # Process bitişini kontrol et
            threading.Thread(target=self._monitor_preview, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Önizleme hatası: {e}", exc_info=True)
            messagebox.showwarning(
                "Önizleme Hatası",
                f"Önizleme başlatılamadı:\n\n{str(e)}"
            )
    
    def _monitor_preview(self):
        """Önizleme process'ini izle"""
        try:
            if self._preview_proc:
                self._preview_proc.wait()
                # Process bittiğinde butonu güncelle
                if not self._is_closing and self._preview_btn:
                    self.after(0, lambda: self._preview_btn.configure(
                        text="▶",
                        fg_color="#007BFF",
                        hover_color="#0056B3"
                    ) if self._preview_btn else None)
                    self._preview_btn = None
                    self._preview_path = None
        except Exception:
            pass
    
    def _stop_preview(self):
        """Önizlemeyi durdur"""
        try:
            if self._preview_proc and self._preview_proc.poll() is None:
                self._preview_proc.terminate()
                time.sleep(0.1)
                if self._preview_proc.poll() is None:
                    self._preview_proc.kill()
            self._preview_proc = None
            if self._preview_btn:
                self._preview_btn.configure(text="▶", fg_color="#007BFF", hover_color="#0056B3")
            self._preview_btn = None
            self._preview_path = None
        except Exception as e:
            logger.debug(f"Preview durdurma hatası: {e}")
    
    def _toggle_select(self, path: str, btn: ctk.CTkButton, check_label: ctk.CTkLabel, row: ctk.CTkFrame):
        """Seçim toggle"""
        if self._is_closing:
            return
        
        # Tek spot kontrolü: Eğer tek spot varsa ve başka bir şey seçiliyse, önceki seçimi kaldır
        if self.total_spots == 1:
            if path in self.selected_presets:
                # Seçimi kaldır
                self.selected_presets.remove(path)
                btn.configure(text="Seç", fg_color="#6C757D", hover_color="#5A6268")
                check_label.configure(text="○", text_color="#6C757D")
                row.configure(
                    fg_color=("#F8F9FA", "#3D3D3D"),
                    border_color=("#DEE2E6", "#5D5D5D"),
                    border_width=1
                )
            else:
                # Önceki seçimi kaldır (tek spot için sadece 1 seçim olabilir)
                if self.selected_presets:
                    # Önceki seçimi bul ve UI'da güncelle
                    old_path = list(self.selected_presets)[0]
                    # Tüm satırları kontrol et ve önceki seçimi kaldır
                    for widget in self.list_container.winfo_children():
                        if isinstance(widget, ctk.CTkFrame):
                            # Bu satırın path'ini kontrol et (row'un userdata'sına path saklayabiliriz)
                            try:
                                widget_path = getattr(widget, '_preset_path', None)
                                if widget_path == old_path:
                                    # Önceki seçimi UI'da kaldır
                                    for child in widget.winfo_children():
                                        if isinstance(child, ctk.CTkFrame):
                                            for grandchild in child.winfo_children():
                                                if isinstance(grandchild, ctk.CTkButton):
                                                    btn_text = grandchild.cget("text")
                                                    if btn_text == "✓":
                                                        grandchild.configure(text="Seç", fg_color="#6C757D", hover_color="#5A6268")
                                                elif isinstance(grandchild, ctk.CTkLabel):
                                                    label_text = grandchild.cget("text")
                                                    if label_text == "✓":
                                                        grandchild.configure(text="○", text_color="#6C757D")
                                    widget.configure(
                                        fg_color=("#F8F9FA", "#3D3D3D"),
                                        border_color=("#DEE2E6", "#5D5D5D"),
                                        border_width=1
                                    )
                                    break
                            except Exception:
                                pass
                    self.selected_presets.clear()
                
                # Yeni seçimi ekle
                self.selected_presets.add(path)
                btn.configure(text="✓", fg_color="#28A745", hover_color="#218838")
                check_label.configure(text="✓", text_color="#28A745")
                row.configure(
                    fg_color=("#E7F3FF", "#1E3A5F"),
                    border_color="#007BFF",
                    border_width=2
                )
                # Path'i row'a sakla (sonraki seçimlerde kullanmak için)
                row._preset_path = path
        else:
            # Çoklu spot: Normal toggle
            if path in self.selected_presets:
                self.selected_presets.remove(path)
                btn.configure(text="Seç", fg_color="#6C757D", hover_color="#5A6268")
                check_label.configure(text="○", text_color="#6C757D")
                row.configure(
                    fg_color=("#F8F9FA", "#3D3D3D"),
                    border_color=("#DEE2E6", "#5D5D5D"),
                    border_width=1
                )
            else:
                self.selected_presets.add(path)
                btn.configure(text="✓", fg_color="#28A745", hover_color="#218838")
                check_label.configure(text="✓", text_color="#28A745")
                row.configure(
                    fg_color=("#E7F3FF", "#1E3A5F"),
                    border_color="#007BFF",
                    border_width=2
                )
            # Path'i row'a sakla
            row._preset_path = path
    
    def _on_cancel(self):
        """İptal - seçimleri uygulamadan kapat"""
        if self._is_closing:
            return
        
        self._is_closing = True
        self._stop_preview()
        self.selected_presets.clear()  # Seçimleri temizle
        
        try:
            self.grab_release()
        except Exception:
            pass
        
        try:
            self.destroy()
        except Exception as e:
            logger.debug(f"Destroy hatası (görmezden geliniyor): {e}")
            try:
                self.quit()
            except Exception:
                pass
    
    def _apply_selection(self):
        """Seçimleri uygula ve pencereyi kapat"""
        if self._is_closing:
            return
        
        chosen = list(self.selected_presets)
        
        if not chosen:
            messagebox.showinfo(
                "Bilgi",
                "Lütfen en az bir fon müziği seçin."
            )
            return
        
        # Tek spot kısıtı kontrolü
        if self.total_spots == 1:
            if len(chosen) > 1:
                messagebox.showwarning(
                    "Seçim Kısıtı",
                    "Analiz tek spot buldu. Yalnızca 1 fon seçebilirsiniz."
                )
                chosen = chosen[:1]
        else:
            # Çoklu spot için seçim sayısını kontrol et
            if len(chosen) > self.total_spots:
                messagebox.showwarning(
                    "Seçim Kısıtı",
                    f"Analiz {self.total_spots} spot buldu. En fazla {self.total_spots} fon seçebilirsiniz."
                )
                chosen = chosen[:self.total_spots]
        
        self._stop_preview()
        if self.on_selection:
            self.on_selection(chosen)
        
        # Pencereyi kapat
        self._is_closing = True
        try:
            self.grab_release()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception as e:
            logger.debug(f"Destroy hatası (görmezden geliniyor): {e}")
            try:
                self.quit()
            except Exception:
                pass
    
    def _on_close(self):
        """Pencereyi güvenli şekilde kapat (sadece X butonu ile)"""
        if self._is_closing:
            return
        
        self._is_closing = True
        self._stop_preview()
        
        # X butonu ile kapanırsa seçimleri uygulama (sadece butonlarla çalışmalı)
        # Bu fonksiyon artık sadece pencere kapatma işlemini yapar
        
        try:
            self.grab_release()
        except Exception:
            pass
        
        try:
            self.destroy()
        except Exception as e:
            logger.debug(f"Destroy hatası (görmezden geliniyor): {e}")
            try:
                self.quit()
            except Exception:
                pass
