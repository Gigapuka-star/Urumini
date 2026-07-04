import os
import json
import threading
import tempfile
import time
import ctypes
import io
import struct
from tkinter import filedialog, messagebox
import customtkinter as ctk
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    genai = None
    types = None
    HAS_GEMINI = False

# Імпортуємо Pillow
try:
    from PIL import Image, ImageGrab
    HAS_PIL = True
except ImportError:
    messagebox.showwarning("Бібліотека Pillow не знайдена", "Встановіть Pillow (pip install Pillow)!")
    HAS_PIL = False

from paint_window import MiniPaintWindow

CONFIG_FILE = "gemini_config.json"

THEMES = {
    "Rose Gold": {"bg": "#1A1214", "chat_bg": "#2C1A1D", "user_bubble": "#B76E79", "bot_bubble": "#44282C", "error_bubble": "#8C2A3A", "text": "#FFF0F2", "accent": "#E0A1A9", "top_bar": "#150E10", "border": "#5E3A40"},
    "Neon Space": {"bg": "#0B0C10", "chat_bg": "#13111C", "user_bubble": "#4A00E0", "bot_bubble": "#2A2540", "error_bubble": "#800020", "text": "#FFFFFF", "accent": "#6B21FF", "top_bar": "#0F0E17", "border": "#3B3561"},
    "Cyberpunk 2077": {"bg": "#03001e", "chat_bg": "#120024", "user_bubble": "#ff007f", "bot_bubble": "#240046", "error_bubble": "#ff0000", "text": "#00f0ff", "accent": "#ff007f", "top_bar": "#0a0018", "border": "#730099"},
    "Matrix (Hacker)": {"bg": "#000000", "chat_bg": "#050B05", "user_bubble": "#00FF33", "bot_bubble": "#102410", "error_bubble": "#8B0000", "text": "#00FF33", "accent": "#00FF33", "top_bar": "#020502", "border": "#00FF33"},
    "Ocean Breeze": {"bg": "#0F2027", "chat_bg": "#203A43", "user_bubble": "#2C5364", "bot_bubble": "#243B55", "error_bubble": "#9E3C3C", "text": "#ECEFF1", "accent": "#00E5FF", "top_bar": "#0B161A", "border": "#37474F"},
    "Classic Dark": {"bg": "#18191A", "chat_bg": "#242526", "user_bubble": "#007AFF", "bot_bubble": "#3A3B3C", "error_bubble": "#A42828", "text": "#E4E6EB", "accent": "#2D88FF", "top_bar": "#18191A", "border": "#3E4042"},
    "Dracula": {"bg": "#282a36", "chat_bg": "#1E1F29", "user_bubble": "#bd93f9", "bot_bubble": "#44475a", "error_bubble": "#ff5555", "text": "#f8f8f2", "accent": "#ff79c6", "top_bar": "#21222C", "border": "#6272a4"},
    "Gruvbox": {"bg": "#282828", "chat_bg": "#1d2021", "user_bubble": "#d3869b", "bot_bubble": "#3c3836", "error_bubble": "#cc241d", "text": "#ebdbb2", "accent": "#fabd2f", "top_bar": "#282828", "border": "#504945"},
    "Monokai": {"bg": "#272822", "chat_bg": "#1e1f1c", "user_bubble": "#fd971f", "bot_bubble": "#3e3d32", "error_bubble": "#f92672", "text": "#f8f8f2", "accent": "#a6e22e", "top_bar": "#272822", "border": "#75715e"},
    "Solarized Dark": {"bg": "#002b36", "chat_bg": "#001e26", "user_bubble": "#268bd2", "bot_bubble": "#073642", "error_bubble": "#dc322f", "text": "#839496", "accent": "#2aa198", "top_bar": "#002b36", "border": "#586e75"}
}

THEME_ALIASES = {
    "Рожеве Золото": "Rose Gold",
    "Космічний Неон": "Neon Space",
    "Кіберпанк 2077": "Cyberpunk 2077",
    "Матриця (Hacker)": "Matrix (Hacker)",
    "Океанський Бриз": "Ocean Breeze",
    "Класичний Темний": "Classic Dark",
}

LOCALES = {
    "en": {
        "settings_title": "⚙️ Settings",
        "settings_header": "CONTROL PANEL",
        "free_mode_label": "🌐 Guest mode (no key)",
        "experiments": "🧪 EXPERIMENTS:",
        "typewriter_label": "⌨️ Typewriter effect",
        "typewriter_speed": "⌨️ Typing speed: {}",
        "typewriter_delay": "⏱ Delay (ms): {}",
        "sound_label": "🔔 Sound notification",
        "jedi_label": "🕵️ Incognito (erase old messages)",
        "model_label": "🧠 AI Model:",
        "theme_label": "🎨 Visual Theme:",
        "font_label": "🔤 Fonts:",
        "font_size": "📏 Font size: {}px",
        "clear_dialog": "🗑️ Clear dialog",
        "language_label": "🌍 Language:",
        "language": "Language",
        "english": "English",
        "ukrainian": "Ukrainian",
        "russian": "Russian",
        "placeholder_message": "Message...",
        "attachment_file": "📎 File: {}",
        "attachment_screenshot": "📎 Screenshot from clipboard",
        "guest_mode_on": "🌐 GUEST MODE ENABLED (API simulation).",
        "guest_mode_missing_module": "🔌 google-genai module not found — guest mode enabled.",
        "connection_error": "🚨 CONNECTION ERROR: {}",
        "no_connection": "🚨 CONNECTION FAILED: No connection. Check your setup.",
        "mock_response": "🤖 GUEST MODE: This is a mock response. To generate a real answer, switch off guest mode.",
        "copy_ok": "✅ Last text/code copied to clipboard.",
        "copy_error": "⚠️ Copy error: {}",
        "copy_empty": "⚠️ There is nothing to copy.",
        "attach_title": "Choose a file",
        "attach_all_files": "All files",
        "window_title": "AI Client",
        "error_api_key": "🚨 CRITICAL ERROR: No connection is available. Guest mode is active.",
        "clear_chat": "Clear dialog",
        "theme": "Theme"
    },
    "uk": {
        "settings_title": "⚙️ Налаштування",
        "settings_header": "ПАНЕЛЬ КЕРУВАННЯ",
        "free_mode_label": "🌐 Гостьовий режим (без ключа)",
        "experiments": "🧪 ЕКСПЕРИМЕНТИ:",
        "typewriter_label": "⌨️ Ефект друку",
        "typewriter_speed": "⌨️ Швидкість набору: {}",
        "typewriter_delay": "⏱ Затримка (ms): {}",
        "sound_label": "🔔 Звукове сповіщення",
        "jedi_label": "🕵️ Інкогніто (стирати старі)",
        "model_label": "🧠 Модель ШІ:",
        "theme_label": "🎨 Візуальна тема:",
        "font_label": "🔤 Шрифти:",
        "font_size": "📏 Розмір шрифту: {}px",
        "clear_dialog": "🗑️ Очистити діалог",
        "language_label": "🌍 Мова:",
        "language": "Мова",
        "english": "Англійська",
        "ukrainian": "Українська",
        "russian": "Російська",
        "placeholder_message": "Повідомлення...",
        "attachment_file": "📎 Файл: {}",
        "attachment_screenshot": "📎 Скріншот із буфера",
        "guest_mode_on": "🌐 ГОСТЬОВИЙ РЕЖИМ УВІМКНЕНО (імітація API).",
        "guest_mode_missing_module": "🔌 Модуль google-genai не знайдено — увімкнено гостьовий режим.",
        "connection_error": "🚨 ПОМИЛКА ПІДКЛЮЧЕННЯ: {}",
        "no_connection": "🚨 ВІДМОВА: Немає підключення. Перевірте налаштування.",
        "mock_response": "🤖 ГОСТЬОВИЙ РЕЖИМ: Це імітація відповіді. Щоб отримати справжню відповідь, вимкніть гостьовий режим.",
        "copy_ok": "✅ Останній текст/код скопійовано у буфер обміну.",
        "copy_error": "⚠️ Помилка копіювання: {}",
        "copy_empty": "⚠️ Немає чого копіювати.",
        "attach_title": "Оберіть файл",
        "attach_all_files": "Усі файли",
        "window_title": "AI Client",
        "error_api_key": "🚨 КРИТИЧНА ПОМИЛКА: Немає підключення. Гостьовий режим активний.",
        "clear_chat": "Очистити діалог",
        "theme": "Тема"
    },
    "ru": {
        "settings_title": "⚙️ Настройки",
        "settings_header": "ПАНЕЛЬ УПРАВЛЕНИЯ",
        "free_mode_label": "🌐 Гостевой режим (без ключа)",
        "experiments": "🧪 ЭКСПЕРИМЕНТЫ:",
        "typewriter_label": "⌨️ Эффект печати",
        "typewriter_speed": "⌨️ Скорость набора: {}",
        "typewriter_delay": "⏱ Задержка (ms): {}",
        "sound_label": "🔔 Звуковое уведомление",
        "jedi_label": "🕵️ Инкогнито (стирание старых)",
        "model_label": "🧠 Модель ИИ:",
        "theme_label": "🎨 Визуальная тема:",
        "font_label": "🔤 Шрифты:",
        "font_size": "📏 Размер шрифта: {}px",
        "clear_dialog": "🗑️ Очистить диалог",
        "language_label": "🌍 Язык:",
        "language": "Язык",
        "english": "Английский",
        "ukrainian": "Украинский",
        "russian": "Русский",
        "placeholder_message": "Сообщение...",
        "attachment_file": "📎 Файл: {}",
        "attachment_screenshot": "📎 Скриншот из буфера",
        "guest_mode_on": "🌐 ГОСТЕВОЙ РЕЖИМ ВКЛЮЧЕН (имитация API).",
        "guest_mode_missing_module": "🔌 Модуль google-genai не найден — включён гостевой режим.",
        "connection_error": "🚨 ОШИБКА ПОДКЛЮЧЕНИЯ: {}",
        "no_connection": "🚨 ОТКАЗ: Нет подключения. Проверьте настройки.",
        "mock_response": "🤖 ГОСТЕВОЙ РЕЖИМ: Это имитация ответа. Чтобы получить настоящий ответ, выключите гостевой режим.",
        "copy_ok": "✅ Последний текст/код скопирован в буфер обмена.",
        "copy_error": "⚠️ Ошибка копирования: {}",
        "copy_empty": "⚠️ Нечего копировать.",
        "attach_title": "Выберите файл",
        "attach_all_files": "Все файлы",
        "window_title": "AI Client",
        "error_api_key": "🚨 КРИТИЧНАЯ ОШИБКА: Нет подключения. Гостевой режим активен.",
        "clear_chat": "Очистить диалог",
        "theme": "Тема"
    }
}

# =====================================================================
# ВІКНО НАЛАШТУВАНЬ
# =====================================================================
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master_app, current_theme_config):
        super().__init__(master_app)
        self.master_app = master_app
        self.locale = self.master_app.current_locale
        self.t = LOCALES[self.locale]
        
        self.title(self.t["settings_title"])
        self.geometry("420x680")
        self.minsize(380, 560)
        self.resizable(True, True)
        self.attributes('-topmost', True)
        
        self.container = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.container.pack(fill="both", expand=True)
        
        self.header_lbl = ctk.CTkLabel(self.container, text=self.t["settings_header"], font=("Segoe UI", 16, "bold"))
        self.header_lbl.pack(pady=(20, 10))

        self.free_mode_switch = ctk.CTkSwitch(
            self.container, text=self.t["free_mode_label"], font=("Segoe UI", 13, "bold"), command=self.toggle_free_mode
        )
        self.free_mode_switch.pack(padx=20, pady=(5, 10), anchor="w")
        if self.master_app.free_mode: self.free_mode_switch.select()

        self.divider_exp = ctk.CTkFrame(self.container, height=2, fg_color="#444444")
        self.divider_exp.pack(fill="x", padx=20, pady=5)
        
        self.exp_lbl = ctk.CTkLabel(self.container, text=self.t["experiments"], font=("Segoe UI", 13, "bold"), text_color="#FFD700")
        self.exp_lbl.pack(padx=20, pady=(5, 5), anchor="w")

        self.typewriter_switch = ctk.CTkSwitch(self.container, text=self.t["typewriter_label"], command=self.toggle_typewriter)
        self.typewriter_switch.pack(padx=20, pady=(5, 5), anchor="w")
        if self.master_app.typewriter_mode: self.typewriter_switch.select()

        # Typewriter tuning controls
        self.chunk_lbl = ctk.CTkLabel(self.container, text=self.t["typewriter_speed"].format(self.master_app.typewriter_chunk_size), font=("Segoe UI", 12))
        self.chunk_lbl.pack(padx=20, pady=(6, 0), anchor="w")
        self.chunk_slider = ctk.CTkSlider(self.container, from_=1, to=32, number_of_steps=31, command=self._on_chunk_slider)
        self.chunk_slider.set(self.master_app.typewriter_chunk_size)
        self.chunk_slider.pack(fill="x", padx=20, pady=(3, 8))

        self.delay_lbl = ctk.CTkLabel(self.container, text=self.t["typewriter_delay"].format(self.master_app.typewriter_delay_ms), font=("Segoe UI", 12))
        self.delay_lbl.pack(padx=20, pady=(6, 0), anchor="w")
        self.delay_slider = ctk.CTkSlider(self.container, from_=0, to=50, number_of_steps=50, command=self._on_delay_slider)
        self.delay_slider.set(self.master_app.typewriter_delay_ms)
        self.delay_slider.pack(fill="x", padx=20, pady=(3, 8))

        self.sound_switch = ctk.CTkSwitch(self.container, text=self.t["sound_label"], command=self.toggle_sound)
        self.sound_switch.pack(padx=20, pady=(5, 5), anchor="w")
        if self.master_app.sound_mode: self.sound_switch.select()

        self.jedi_switch = ctk.CTkSwitch(self.container, text=self.t["jedi_label"], command=self.toggle_jedi)
        self.jedi_switch.pack(padx=20, pady=(5, 10), anchor="w")
        if self.master_app.jedi_mode: self.jedi_switch.select()

        self.divider1 = ctk.CTkFrame(self.container, height=2, fg_color="#444444")
        self.divider1.pack(fill="x", padx=20, pady=5)
        
        self.model_lbl = ctk.CTkLabel(self.container, text=self.t["model_label"], font=("Segoe UI", 13, "bold"))
        self.model_lbl.pack(padx=20, pady=(5, 0), anchor="w")
        self.model_dropdown = ctk.CTkOptionMenu(self.container, values=["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-2.5-pro"], command=self.master_app.change_ai_model)
        self.model_dropdown.pack(fill="x", padx=20, pady=(5, 10))
        self.model_dropdown.set(self.master_app.selected_model_name)
        
        self.theme_lbl = ctk.CTkLabel(self.container, text=self.t["theme_label"], font=("Segoe UI", 13, "bold"))
        self.theme_lbl.pack(padx=20, pady=(5, 0), anchor="w")
        self.theme_dropdown = ctk.CTkOptionMenu(self.container, values=list(THEMES.keys()), command=self.master_app.change_theme_event)
        self.theme_dropdown.pack(fill="x", padx=20, pady=(5, 10))
        self.theme_dropdown.set(self.master_app.current_theme_name)
        
        self.font_lbl = ctk.CTkLabel(self.container, text=self.t["font_label"], font=("Segoe UI", 13, "bold"))
        self.font_lbl.pack(padx=20, pady=(5, 0), anchor="w")
        self.font_dropdown = ctk.CTkOptionMenu(self.container, values=["Comic Sans MS", "Segoe UI", "Roboto", "Consolas"], command=self.master_app.change_font_family_event)
        self.font_dropdown.pack(fill="x", padx=20, pady=(5, 10))
        self.font_dropdown.set(self.master_app.current_font_family)
        
        self.size_lbl = ctk.CTkLabel(self.container, text=self.t["font_size"].format(self.master_app.current_font_size), font=("Segoe UI", 13, "bold"))
        self.size_lbl.pack(padx=20, pady=(5, 0), anchor="w")
        self.size_slider = ctk.CTkSlider(self.container, from_=11, to=24, number_of_steps=13, command=self._on_slider_change)
        self.size_slider.pack(fill="x", padx=20, pady=(5, 15))
        self.size_slider.set(self.master_app.current_font_size)
        
        self.language_lbl = ctk.CTkLabel(self.container, text=self.t["language_label"], font=("Segoe UI", 13, "bold"))
        self.language_lbl.pack(padx=20, pady=(5, 0), anchor="w")
        self.language_dropdown = ctk.CTkOptionMenu(self.container, values=[self.t["english"], self.t["ukrainian"], self.t["russian"]], command=self.change_language)
        self.language_dropdown.pack(fill="x", padx=20, pady=(5, 10))
        self.language_dropdown.set(self.t["english"] if self.locale == "en" else (self.t["ukrainian"] if self.locale == "uk" else self.t["russian"]))

        self.btn_clear = ctk.CTkButton(self.container, text=self.t["clear_dialog"], fg_color="#A30000", hover_color="#D30000", command=self.master_app.clear_chat_history)
        self.btn_clear.pack(fill="x", padx=20, pady=5)

        self.apply_colors(current_theme_config)

    def toggle_free_mode(self):
        self.master_app.free_mode = self.free_mode_switch.get() == 1
        self.master_app.save_config_state()
        self.master_app.init_gemini_client()

    def toggle_typewriter(self):
        self.master_app.typewriter_mode = self.typewriter_switch.get() == 1
        self.master_app.save_config_state()

    # Settings hooks for typewriter tuning
    def save_typewriter_chunk(self, value):
        try:
            self.master_app.typewriter_chunk_size = int(value)
            self.master_app.save_config_state()
        except: pass

    def save_typewriter_delay(self, value):
        try:
            self.master_app.typewriter_delay_ms = int(value)
            self.master_app.save_config_state()
        except: pass

    def toggle_sound(self):
        self.master_app.sound_mode = self.sound_switch.get() == 1
        self.master_app.save_config_state()

    def toggle_jedi(self):
        self.master_app.jedi_mode = self.jedi_switch.get() == 1
        self.master_app.save_config_state()

    def change_language(self, selected_value):
        if selected_value == self.t["english"]:
            self.master_app.current_locale = "en"
        elif selected_value == self.t["ukrainian"]:
            self.master_app.current_locale = "uk"
        else:
            self.master_app.current_locale = "ru"
        self.master_app.save_config_state()
        self.master_app.apply_locale()
        self.master_app.open_settings_window()

    def _on_chunk_slider(self, value):
        try:
            v = int(value)
            self.chunk_lbl.configure(text=f"⌨️ Швидкість набору: {v}")
            self.master_app.typewriter_chunk_size = v
            self.master_app.save_config_state()
        except: pass

    def _on_delay_slider(self, value):
        try:
            v = int(value)
            self.delay_lbl.configure(text=f"⏱ Затримка (ms): {v}")
            self.master_app.typewriter_delay_ms = v
            self.master_app.save_config_state()
        except: pass

    def _on_slider_change(self, value):
        self.size_lbl.configure(text=f"📏 Розмір: {int(value)}px")
        self.master_app.change_font_size_event(value)
        
    def apply_colors(self, cfg):
        self.container.configure(fg_color=cfg["top_bar"])
        self.header_lbl.configure(text_color=cfg["accent"])
        for lbl in [self.model_lbl, self.theme_lbl, self.font_lbl, self.size_lbl, self.language_lbl]: lbl.configure(text_color=cfg["text"])
        for switch in [self.free_mode_switch, self.typewriter_switch, self.sound_switch, self.jedi_switch]:
            switch.configure(progress_color=cfg["user_bubble"], button_color=cfg["accent"])
        for ctrl in [self.model_dropdown, self.theme_dropdown, self.font_dropdown, self.language_dropdown]:
            ctrl.configure(button_color=cfg["user_bubble"], button_hover_color=cfg["accent"], fg_color=cfg["bg"], text_color=cfg["text"])
        self.size_slider.configure(progress_color=cfg["user_bubble"], button_color=cfg["accent"])


# =====================================================================
# ВІДЖЕТ ПОВІДОМЛЕННЯ (ТЕПЕР БЕЗ СКРОЛУ І З АНІМАЦІЄЮ)
# =====================================================================
class MessageWidget(ctk.CTkFrame):
    def __init__(self, parent, text, is_user, is_error, theme_config, font_family, font_size, app_width):
        super().__init__(parent, fg_color="transparent")
        self.is_user = is_user
        self.is_error = is_error

        bubble_color = theme_config["error_bubble"] if is_error else (theme_config["user_bubble"] if is_user else theme_config["bot_bubble"])
        self.pack(fill="x", padx=10, pady=5)

        # Використовуємо CTkLabel замість CTkTextbox. Він розширюється автоматично!
        self.label = ctk.CTkLabel(
            self, text=text, fg_color=bubble_color, text_color=theme_config["text"],
            font=(font_family, font_size), corner_radius=0, justify="left",
            wraplength=int(app_width * 0.7) # Динамічна ширина тексту
        )
        
        # АНІМАЦІЯ СЛАЙД-ІН
        self.target_padx = (60, 5) if is_user else (5, 60)
        self.anim_offset = 50
        
        start_padx = (self.target_padx[0] + self.anim_offset, self.target_padx[1]) if is_user else (self.target_padx[0], self.target_padx[1] + self.anim_offset)
        
        self.label.pack(side="right" if is_user else "left", padx=start_padx, pady=2, ipadx=15, ipady=10)
        self.animate_slide()

    def animate_slide(self):
        if self.anim_offset > 0:
            self.anim_offset -= 10 # Швидкість анімації
            current_padx = (self.target_padx[0] + self.anim_offset, self.target_padx[1]) if self.is_user else (self.target_padx[0], self.target_padx[1] + self.anim_offset)
            target = getattr(self, 'label', None) or getattr(self, 'text_widget', None)
            if target:
                try:
                    target.pack_configure(padx=current_padx)
                except Exception:
                    pass
            self.after(15, self.animate_slide)

    def _on_copy_request(self, event=None):
        try:
            text = self.label.cget("text")
            if not text:
                return
            # try to use parent root clipboard
            root = self.winfo_toplevel()
            try:
                root.clipboard_clear()
                root.clipboard_append(text)
                root.insert_system_note("✅ Повідомлення скопійовано у буфер обміну.")
            except Exception:
                pass
        except Exception:
            pass

    def update_style(self, theme_config, font_family, font_size, app_width):
        bubble_color = theme_config["error_bubble"] if self.is_error else (theme_config["user_bubble"] if self.is_user else theme_config["bot_bubble"])
        try:
            self.text_widget.configure(bg=bubble_color, fg=theme_config["text"], font=(font_family, font_size))
        except Exception:
            pass


class AdvancedChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("900x750")
        self.title("AI Client")
        self.minsize(600, 500)
        
        self.current_theme_name = "Dracula" 
        self.current_font_family = "Comic Sans MS"
        self.current_font_size = 14
        self.selected_model_name = "gemini-3.1-flash-lite"
        self.current_locale = "en"
        self.t = LOCALES[self.current_locale]
        
        self.chat_history = []
        self.messages_widgets_list = []
        self.settings_window_instance = None
        self.paint_window_instance = None
        self.chat_session = None
        self.attached_file_path = None

        self.API_KEY = ""
        self.key_history = []
        self.free_mode = False
        self.typewriter_mode = False
        self.sound_mode = False
        self.jedi_mode = False
        # Typewriter tuning and control
        self.typewriter_chunk_size = 8
        self.typewriter_delay_ms = 1
        self.typewriter_paused = False
        self._typewriter_after_id = None
        self._typewriter_state = None

        self.load_config_state()
        self.t = LOCALES[self.current_locale]
        self.setup_ui_layout()
        self.apply_theme_colors()
        self.init_gemini_client()

        # Працюємо з буфером надійно: обробка Paste + Ctrl+V на головному вікні та в CTkEntry
        self.bind("<<Paste>>", self.paste_from_clipboard)
        self.bind("<Control-v>", self.paste_from_clipboard)
        self.bind("<Control-V>", self.paste_from_clipboard)
        self.bind("<Shift-Insert>", self.paste_from_clipboard)
        self.entry_field.bind("<<Paste>>", self.paste_from_clipboard)
        self.entry_field.bind("<Control-v>", self.paste_from_clipboard)
        self.entry_field.bind("<Control-V>", self.paste_from_clipboard)
        self.entry_field.bind("<Shift-Insert>", self.paste_from_clipboard)
        self.bind_all("<<Paste>>", self.paste_from_clipboard)
        self.bind_all("<Control-v>", self.paste_from_clipboard)
        self.bind_all("<Control-V>", self.paste_from_clipboard)
        self.bind_all("<Shift-Insert>", self.paste_from_clipboard)
        self.bind_class("Frame", "<<Paste>>", self.paste_from_clipboard)
        self.bind_class("Frame", "<Control-v>", self.paste_from_clipboard)
        self.bind_class("Frame", "<Control-V>", self.paste_from_clipboard)
        self.bind_class("Frame", "<Shift-Insert>", self.paste_from_clipboard)
        self.bind_class("CTkEntry", "<<Paste>>", self.paste_from_clipboard)
        self.bind_class("CTkEntry", "<Control-v>", self.paste_from_clipboard)
        self.bind_class("CTkEntry", "<Control-V>", self.paste_from_clipboard)
        self.bind_class("CTkEntry", "<Shift-Insert>", self.paste_from_clipboard)
        self.bind("<Configure>", self.on_resize) # Щоб текст підлаштовувався при розтягуванні вікна

    def load_config_state(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.API_KEY = data.get("api_key", self.API_KEY)
                    self.key_history = data.get("key_history", self.key_history)
                    self.current_locale = data.get("language", self.current_locale)
                    self.free_mode = data.get("free_mode", False)
                    self.typewriter_mode = data.get("typewriter", False)
                    self.sound_mode = data.get("sound", False)
                    self.jedi_mode = data.get("jedi", False)
                    self.typewriter_chunk_size = data.get("typewriter_chunk", self.typewriter_chunk_size)
                    self.typewriter_delay_ms = data.get("typewriter_delay", self.typewriter_delay_ms)
                    if data.get("last_theme") in THEMES: self.current_theme_name = data.get("last_theme")
            except Exception: pass 

    def save_config_state(self):
        data = {
            "api_key": self.API_KEY, "key_history": self.key_history, "free_mode": self.free_mode,
            "last_theme": self.current_theme_name, "language": self.current_locale, "typewriter": self.typewriter_mode,
            "sound": self.sound_mode, "jedi": self.jedi_mode,
            "typewriter_chunk": self.typewriter_chunk_size, "typewriter_delay": self.typewriter_delay_ms
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception: pass

    def save_api_key_to_config(self, new_key):
        self.API_KEY = new_key
        if new_key not in self.key_history: self.key_history.append(new_key)
        self.save_config_state()

    def apply_locale(self):
        self.t = LOCALES[self.current_locale]
        self.title(self.t["window_title"])
        if hasattr(self, "entry_field") and self.entry_field.winfo_exists():
            self.entry_field.configure(placeholder_text=self.t["placeholder_message"])
        if self.settings_window_instance and self.settings_window_instance.winfo_exists():
            self.settings_window_instance.destroy()
            self.settings_window_instance = None
        self.open_settings_window()

    def setup_ui_layout(self):
        # ВЕРХНЮ ПАНЕЛЬ ВИДАЛЕНО ПОВНІСТЮ
        self.chat_view = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.chat_view.pack(fill="both", expand=True)

        self.input_dock = ctk.CTkFrame(self, corner_radius=0)
        self.input_dock.pack(fill="x", side="bottom")

        self.attachment_frame = ctk.CTkFrame(self.input_dock, fg_color="transparent", height=30)
        self.attachment_label = ctk.CTkLabel(self.attachment_frame, text="", text_color="#A0A0A0", font=("Segoe UI", 12))
        self.attachment_label.pack(side="left", padx=(20, 10), pady=(5, 0))
        self.btn_remove_attachment = ctk.CTkButton(
            self.attachment_frame, text="❌", width=40, height=40, fg_color="transparent", hover_color="#8C2A3A", text_color="#FF4C4C", command=self.remove_attachment, corner_radius=20
        )
        self.btn_remove_attachment.pack(side="left", pady=(4, 0), padx=(6,0))

        self.controls_frame = ctk.CTkFrame(self.input_dock, fg_color="transparent")
        self.controls_frame.pack(fill="x", expand=True)

        # Кнопка налаштувань переїхала вниз
        # control buttons: uniform smaller size and reduced height
        BTN_W, BTN_H, BTN_CR = 40, 40, 18
        self.btn_settings = ctk.CTkButton(self.controls_frame, text="⚙️", width=BTN_W, height=BTN_H, corner_radius=BTN_CR, font=("Segoe UI", 14), command=self.open_settings_window)
        self.btn_settings.pack(side="left", padx=(6, 4), pady=8)

        self.btn_attach = ctk.CTkButton(self.controls_frame, text="📎", font=("Segoe UI", 14), width=BTN_W, height=BTN_H, corner_radius=BTN_CR, command=self.attach_file)
        self.btn_attach.pack(side="left", padx=4, pady=8)
        
        self.btn_draw = ctk.CTkButton(self.controls_frame, text="🎨", font=("Segoe UI", 14), width=BTN_W, height=BTN_H, corner_radius=BTN_CR, command=self.open_paint_window)
        self.btn_draw.pack(side="left", padx=(4, 6), pady=8)

        # (pause button removed; send button handles stop/reveal)

        self.entry_field = ctk.CTkEntry(
            self.controls_frame, placeholder_text=self.t["placeholder_message"], 
            height=50, border_width=1, font=(self.current_font_family, 14), corner_radius=25
        )
        self.entry_field.pack(side="left", fill="x", expand=True, padx=(10, 10), pady=20)
        self.entry_field.bind("<Return>", lambda event: self.process_and_send())

        # send button same small height as other controls
        self.send_action_btn = ctk.CTkButton(self.controls_frame, text="➤", font=("Segoe UI", 18), width=48, height=40, corner_radius=20, command=self.process_and_send)
        self.send_action_btn.pack(side="right", padx=(4, 6), pady=8)

        # paste test button, same size as controls
        self.btn_paste_test = ctk.CTkButton(self.controls_frame, text="📋", width=40, height=40, corner_radius=18, command=self.paste_from_clipboard)
        self.btn_paste_test.pack(side="right", padx=(0, 6), pady=8)

        # Key bindings for pause/resume and emergency reveal
        self.bind("<Escape>", lambda e: self.reveal_full_typewriter())
        self.bind("<Control-period>", lambda e: self.toggle_typewriter_pause())

    def on_resize(self, event):
        # Оновлення ширини бульбашок при зміні розміру вікна
        for widget in self.messages_widgets_list:
            widget.label.configure(wraplength=int(self.winfo_width() * 0.7))

    def paste_from_clipboard(self, event=None):
        try:
            print("DEBUG: Спрацювало paste_from_clipboard")
            print(f"DEBUG: paste event -> type={getattr(event, 'type', None)} widget={getattr(event, 'widget', None)} keysym={getattr(event, 'keysym', None)}")
            img = None
            if HAS_PIL:
                try:
                    img = ImageGrab.grabclipboard()
                    print(f"DEBUG: ImageGrab отримав -> {img}")
                except Exception as e:
                    print(f"DEBUG: Помилка Pillow -> {e}")
                    img = None
                if img is None and os.name == "nt":
                    img = self._grab_windows_clipboard_image()
                    print(f"DEBUG: _grab_windows_clipboard_image отримав -> {img}")
            else:
                img = None

            if HAS_PIL and img is not None and isinstance(img, Image.Image):
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, f"gemini_screen_{int(time.time())}.png")
                try:
                    img.save(temp_path, "PNG")
                    self.attached_file_path = temp_path
                    self.attachment_label.configure(text="📎 Скріншот із буфера")
                    self.attachment_frame.pack(side="top", fill="x", before=self.controls_frame)
                    return "break"
                except Exception as e:
                    print(f"DEBUG: Збереження зображення не вдалось -> {e}")

            if isinstance(img, list) and len(img) > 0:
                if os.path.exists(img[0]):
                    self.attached_file_path = img[0]
                    self.attachment_label.configure(text=f"📎 Файл: {os.path.basename(img[0])}")
                    self.attachment_frame.pack(side="top", fill="x", before=self.controls_frame)
                    return "break"

            try:
                clip_text = self.clipboard_get()
                if isinstance(clip_text, str):
                    clip_text = clip_text.strip().strip('"')
                    if clip_text.startswith("file://"):
                        clip_text = clip_text.replace("file://", "")
                        clip_text = clip_text.replace("/", "\\") if os.name == "nt" else clip_text
                    if os.path.exists(clip_text):
                        self.attached_file_path = clip_text
                        self.attachment_label.configure(text=f"📎 Файл: {os.path.basename(clip_text)}")
                        self.attachment_frame.pack(side="top", fill="x", before=self.controls_frame)
                        return "break"
                    if clip_text:
                        self.entry_field.delete(0, "end")
                        self.entry_field.insert(0, clip_text)
                        return "break"
            except Exception as e:
                print(f"DEBUG: clipboard_get помилка -> {e}")

            print("DEBUG: У буфері немає придатних для вставки даних.")
        except Exception as e:
            print(f"DEBUG: paste_from_clipboard помилка -> {e}")
        return "break"

    def _grab_windows_clipboard_image(self):
        try:
            CF_DIB = 8
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            if not user32.OpenClipboard(None):
                return None
            try:
                if not user32.IsClipboardFormatAvailable(CF_DIB):
                    return None
                h_clip = user32.GetClipboardData(CF_DIB)
                if not h_clip:
                    return None
                ptr = kernel32.GlobalLock(h_clip)
                if not ptr:
                    return None
                size = kernel32.GlobalSize(h_clip)
                if not size:
                    kernel32.GlobalUnlock(h_clip)
                    return None
                buffer = ctypes.create_string_buffer(size)
                ctypes.memmove(buffer, ptr, size)
                kernel32.GlobalUnlock(h_clip)
                bmp_header = b"BM" + struct.pack("<I", size + 14) + b"\x00\x00\x00\x00" + b"\x0E\x00\x00\x00"
                return Image.open(io.BytesIO(bmp_header + buffer.raw))
            finally:
                user32.CloseClipboard()
        except Exception:
            return None

    def open_paint_window(self):
        if self.paint_window_instance is None or not self.paint_window_instance.winfo_exists():
            self.paint_window_instance = MiniPaintWindow(self)
        else: self.paint_window_instance.focus()

    def attach_file(self):
        file_path = filedialog.askopenfilename(title=self.t["attach_title"], filetypes=[(self.t["attach_all_files"], "*.*")])
        if file_path:
            self.attached_file_path = file_path
            self.attachment_label.configure(text=f"📎 {os.path.basename(file_path)}")
            self.attachment_frame.pack(side="top", fill="x", before=self.controls_frame)

    def remove_attachment(self):
        self.attached_file_path = None
        self.attachment_frame.pack_forget()

    def init_gemini_client(self):
        if not HAS_GEMINI:
            self.free_mode = True
            self.chat_session = None
            self.insert_system_note(self.t["guest_mode_missing_module"])
            return

        if self.free_mode:
            self.insert_system_note(self.t["guest_mode_on"])
            return

        if not self.API_KEY or self.API_KEY.strip() == "":
            self.display_message(self.t["error_api_key"], is_user=False, is_error=True)
            self.chat_session = None
            return

        try:
            self.client = genai.Client(api_key=self.API_KEY)
            self.chat_session = self.client.chats.create(model=self.selected_model_name)
            self.insert_system_note(f"✅ Підключено до {self.selected_model_name}")
        except Exception as e:
            self.display_message(f"🚨 ПОМИЛКА ПІДКЛЮЧЕННЯ: {e}", is_user=False, is_error=True)
            self.chat_session = None

    def open_settings_window(self):
        if self.settings_window_instance is None or not self.settings_window_instance.winfo_exists():
            self.settings_window_instance = SettingsWindow(self, THEMES[self.current_theme_name])
        else: self.settings_window_instance.focus()

    def apply_theme_colors(self):
        cfg = THEMES[self.current_theme_name]
        self.configure(fg_color=cfg["bg"])
        self.chat_view.configure(fg_color=cfg["chat_bg"])
        self.input_dock.configure(fg_color=cfg["bg"])
        
        self.btn_settings.configure(fg_color=cfg["bot_bubble"], hover_color=cfg["border"], text_color=cfg["text"])
        self.btn_attach.configure(fg_color=cfg["bot_bubble"], hover_color=cfg["border"], text_color=cfg["text"])
        self.btn_draw.configure(fg_color=cfg["bot_bubble"], hover_color=cfg["border"], text_color=cfg["text"])
        
        self.entry_field.configure(fg_color=cfg["top_bar"], border_color=cfg["border"], text_color=cfg["text"], font=(self.current_font_family, self.current_font_size))
        self.send_action_btn.configure(fg_color=cfg["user_bubble"], hover_color=cfg["accent"])

        if self.settings_window_instance and self.settings_window_instance.winfo_exists():
            self.settings_window_instance.apply_colors(cfg)

        for widget in self.messages_widgets_list:
            widget.update_style(cfg, self.current_font_family, self.current_font_size, self.winfo_width())

    def change_theme_event(self, selected_theme):
        self.current_theme_name = selected_theme
        self.save_config_state()
        self.apply_theme_colors()

    def change_font_family_event(self, selected_font):
        self.current_font_family = selected_font
        self.apply_theme_colors()

    def change_font_size_event(self, slider_value):
        self.current_font_size = int(slider_value)
        self.apply_theme_colors()

    def change_ai_model(self, selected_model):
        self.selected_model_name = selected_model
        self.init_gemini_client()

    def insert_system_note(self, text):
        lbl = ctk.CTkLabel(self.chat_view, text=text, font=(self.current_font_family, 12, "italic"), text_color="#888888")
        lbl.pack(fill="x", pady=5)
        self.scroll_to_bottom()

    def display_message(self, text, is_user, is_error=False, auto_scroll=True):
        if self.jedi_mode and is_user and len(self.messages_widgets_list) > 2:
            self.clear_chat_history(keep_session=True)
            
        cfg = THEMES[self.current_theme_name]
        msg_bubble = MessageWidget(self.chat_view, text, is_user, is_error, cfg, self.current_font_family, self.current_font_size, self.winfo_width())
        self.messages_widgets_list.append(msg_bubble)
        self.chat_history.append({"role": "user" if is_user else ("error" if is_error else "model"), "text": text})
        if auto_scroll:
            self.scroll_to_bottom()
        return msg_bubble

    def scroll_to_bottom(self):
        self.chat_view.update_idletasks()
        self.chat_view._parent_canvas.yview_moveto(1.0)

    def process_and_send(self):
        query_text = self.entry_field.get()
        file_path = self.attached_file_path
        # If typewriter is currently rendering a response, pressing send reveals full text
        if self._typewriter_state:
            self.reveal_full_typewriter()
            return
        if not query_text.strip() and not file_path: return

        display_text = f"📎 [{os.path.basename(file_path)}]\n{query_text}" if file_path else query_text
        self.display_message(display_text, is_user=True)
        self.entry_field.delete(0, "end")
        self.remove_attachment()

        if self.free_mode:
            self.entry_field.configure(state="disabled")
            def mock_response():
                time.sleep(1.2)
                self.after(0, self._on_gemini_response, self.t["mock_response"], False)
            threading.Thread(target=mock_response, daemon=True).start()
            return

        if not self.chat_session:
            self.display_message(self.t["no_connection"], is_user=False, is_error=True)
            return

        self.entry_field.configure(state="disabled")
        threading.Thread(target=self._request_gemini, args=(query_text, file_path), daemon=True).start()

    def copy_last_response(self):
        # Copy latest model reply or last available message to clipboard
        for item in reversed(self.chat_history):
            if item["role"] == "model" or item["role"] == "error":
                text_to_copy = item["text"].strip()
                break
        else:
            text_to_copy = self.chat_history[-1]["text"].strip() if self.chat_history else ""

        if not text_to_copy:
            self.insert_system_note(self.t["copy_empty"])
            return

        try:
            self.clipboard_clear()
            self.clipboard_append(text_to_copy)
            self.insert_system_note(self.t["copy_ok"])
        except Exception as e:
            self.insert_system_note(self.t["copy_error"].format(e))

    def _request_gemini(self, query_text, file_path=None):
        try:
            contents = []
            if file_path:
                # Always upload files (including images) via the client API.
                # Some SDKs/servers expect an uploaded file object rather than a PIL Image.
                try:
                    uploaded = self.client.files.upload(file=file_path)
                    contents.append(uploaded)
                except Exception:
                    # Fallback: if upload fails (e.g., client not initialized), pass the local path
                    contents.append(file_path)
            if query_text.strip(): contents.append(query_text)
            if not contents: return

            response = self.chat_session.send_message(contents)
            result_text = response.text
            is_error = False
        except Exception as err:
            result_text = f"🚨 ПОМИЛКА: {str(err)}"
            is_error = True

        self.after(0, self._on_gemini_response, result_text, is_error)

    def _on_gemini_response(self, result_text, is_error):
        if self.sound_mode:
            try:
                import winsound
                winsound.MessageBeep()
            except: pass
        if self.typewriter_mode and not is_error:
            # Prepare a stateful typewriter that can be paused/resumed or revealed
            msg_bubble = self.display_message("", is_user=False, is_error=is_error, auto_scroll=False)
            text_len = len(result_text)

            # Cancel any previous typewriter jobs
            if self._typewriter_after_id:
                try: self.after_cancel(self._typewriter_after_id)
                except: pass
                self._typewriter_after_id = None

            # Initialize state
            self._typewriter_state = {
                "msg_bubble": msg_bubble,
                "result_text": result_text,
                "index": 0
            }
            self.typewriter_paused = False

            # Step function uses instance settings and avoids frequent scrolling to prevent shaking
            def _step():
                state = self._typewriter_state
                if not state: return
                if self.typewriter_paused:
                    self._typewriter_after_id = None
                    return
                idx = state["index"]
                chunk = self.typewriter_chunk_size
                next_idx = min(idx + chunk, text_len)
                try:
                    state["msg_bubble"].label.configure(text=state["result_text"][:next_idx])
                except: pass
                state["index"] = next_idx
                if next_idx < text_len:
                    # schedule next step without scrolling (reduces jitter)
                    self._typewriter_after_id = self.after(self.typewriter_delay_ms, _step)
                else:
                    # finished
                    self._typewriter_state = None
                    self._typewriter_after_id = None
                    self._restore_inputs()

            # Immediate show for very short responses
            if text_len <= self.typewriter_chunk_size:
                msg_bubble.label.configure(text=result_text)
                self._restore_inputs()
            else:
                # start typing
                self._typewriter_after_id = self.after(0, _step)
        else:
            self.display_message(result_text, is_user=False, is_error=is_error)
            self._restore_inputs()

    def _restore_inputs(self):
        self.entry_field.configure(state="normal")
        self.entry_field.focus()

    def toggle_typewriter_pause(self):
        # Toggle pause/resume for ongoing typewriter
        if not self._typewriter_state:
            return
        if not self.typewriter_paused:
            # Pause: cancel scheduled callback
            self.typewriter_paused = True
            if self._typewriter_after_id:
                try: self.after_cancel(self._typewriter_after_id)
                except: pass
                self._typewriter_after_id = None
        else:
            # Resume
            self.typewriter_paused = False
            if self._typewriter_state:
                # schedule next step immediately
                self._typewriter_after_id = self.after(0, lambda: self.after(0, self._resume_typewriter))

    def _resume_typewriter(self):
        # helper to call the step defined in _on_gemini_response by scheduling a fresh step
        if not self._typewriter_state:
            return
        # create a small wrapper to reuse the same stepping logic
        def _step_wrapper():
            # Re-run the same step logic by calling _on_gemini_response continuation
            state = self._typewriter_state
            if not state: return
            idx = state.get("index", 0)
            chunk = self.typewriter_chunk_size
            text_len = len(state.get("result_text", ""))
            next_idx = min(idx + chunk, text_len)
            try:
                state["msg_bubble"].label.configure(text=state["result_text"][:next_idx])
            except: pass
            state["index"] = next_idx
            if next_idx < text_len and not self.typewriter_paused:
                self._typewriter_after_id = self.after(self.typewriter_delay_ms, _step_wrapper)
            else:
                if next_idx >= text_len:
                    self._typewriter_state = None
                    self._typewriter_after_id = None
                    self._restore_inputs()

        # start the wrapper loop
        self._typewriter_after_id = self.after(0, _step_wrapper)

    def reveal_full_typewriter(self):
        # Emergency reveal: show full response immediately and cancel typing
        if not self._typewriter_state:
            return
        state = self._typewriter_state
        try:
            if self._typewriter_after_id:
                try: self.after_cancel(self._typewriter_after_id)
                except: pass
                self._typewriter_after_id = None
            state["msg_bubble"].label.configure(text=state.get("result_text", ""))
        except: pass
        self._typewriter_state = None
        self.typewriter_paused = False
        # UI pause button removed
        self._restore_inputs()

    def clear_chat_history(self, keep_session=False):
        for widget in self.messages_widgets_list: widget.destroy()
        self.messages_widgets_list.clear()
        self.chat_history.clear()
        if not keep_session: self.init_gemini_client()

if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception: pass

    ctk.set_appearance_mode("dark")
    app = AdvancedChatApp()
    app.mainloop()