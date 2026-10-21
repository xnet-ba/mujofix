"""Fluent 2 / Windows 11 tema: Segoe UI, zaobljene kontrole, Mica pozadina.

Bez novih zavisnosti: QSS za izgled, `ctypes` + DWM za Mica (Win11).
Van Windowsa (Linux CI, offscreen testovi) sve graceful degradira:
`apply_mica` vrati False, tema ostane solidna boja pozadine.

Pravilo: nikad ne tvrdi da je Mica aktivna ako DWM poziv nije uspio.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mujofix.platform import windows  # noqa: E402

FONT_STACK = ["Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI",
              "Noto Sans", "DejaVu Sans", "Sans Serif"]
MONO_STACK = ["Cascadia Mono", "Consolas", "Cascadia Code", "DejaVu Sans Mono",
              "Monospace"]

# Fluent 2 tokeni (svijetla / tamna)
_LIGHT = {
    "base": "#f3f3f3",
    "layer": "#ffffff",
    "layer_alt": "#fafafa",
    "border": "#d1d1d1",
    "control_border": "#8a8a8a",
    "text": "#1b1b1b",
    "text_secondary": "#5c5c5c",
    "text_disabled": "#9a9a9a",
    "accent": "#0f6cbd",
    "accent_hover": "#115ea3",
    "accent_press": "#0c3b5e",
    "on_accent": "#ffffff",
    "sel": "#e8f1fb",
}
_DARK = {
    "base": "#202020",
    "layer": "#2b2b2b",
    "layer_alt": "#272727",
    "border": "#3b3b3b",
    "control_border": "#8a8a8a",
    "text": "#ffffff",
    "text_secondary": "#d6d6d6",
    "text_disabled": "#7a7a7a",
    "accent": "#479ef5",
    "accent_hover": "#62abf5",
    "accent_press": "#2886de",
    "on_accent": "#000000",
    "sel": "#2b3a4a",
}


def is_dark() -> bool:
    """Tema sistema. `MUJOFIX_THEME=dark|light` je rucni override (testovi)."""
    override = os.environ.get("MUJOFIX_THEME", "").strip().lower()
    if override in ("dark", "light"):
        return override == "dark"
    if not windows.is_windows():
        return False
    try:
        import winreg

        key = (r"Software\Microsoft\Windows\CurrentVersion"
               r"\Themes\Personalize")
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
            value, _ = winreg.QueryValueEx(handle, "AppsUseLightTheme")
        return int(value) == 0
    except Exception:
        return False


def accent_color(dark: bool) -> str:
    """Windows akcent ako je dostupan, inace Fluent 2 default."""
    if windows.is_windows():
        try:
            import winreg

            key = r"Software\Microsoft\Windows\DWM"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
                value, _ = winreg.QueryValueEx(handle, "AccentColor")
            # AccentColor je ABGR dword
            value = int(value)
            r = value & 0xFF
            g = (value >> 8) & 0xFF
            b = (value >> 16) & 0xFF
            if (r, g, b) != (0, 0, 0):
                return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            pass
    return _DARK["accent"] if dark else _LIGHT["accent"]


def tokens(dark: bool) -> dict:
    table = dict(_DARK if dark else _LIGHT)
    table["accent"] = accent_color(dark)
    return table


def qss(dark: bool | None = None, mica: bool = False) -> str:
    """QSS za cijelu aplikaciju. `mica=True`: prozor je providan (Mica se vidi)."""
    dark = is_dark() if dark is None else dark
    t = tokens(dark)
    root_bg = "transparent" if mica else t["base"]
    return f"""
* {{
    font-family: "{'", "'.join(FONT_STACK)}";
    font-size: 14px;
    color: {t["text"]};
}}
QWidget#root {{ background: {root_bg}; }}
QWidget {{ outline: none; }}

QLabel#title {{ font-size: 22px; font-weight: 600; }}
QLabel#subtitle {{ font-size: 15px; color: {t["text_secondary"]}; }}
QLabel#h1 {{ font-size: 16px; font-weight: 600; }}
QLabel#report {{ font-size: 14px; font-weight: 600; color: {t["accent"]}; }}

QPushButton {{
    background: {t["layer"]};
    border: 1px solid {t["border"]};
    border-radius: 4px;
    padding: 6px 14px;
    min-height: 18px;
}}
QPushButton:hover {{ background: {t["layer_alt"]}; }}
QPushButton:pressed {{ background: {t["border"]}; }}
QPushButton:disabled {{ color: {t["text_disabled"]};
                        border-color: {t["border"]}; }}
QPushButton:focus {{ border: 2px solid {t["accent"]}; }}
QPushButton#primary {{
    background: {t["accent"]};
    color: {t["on_accent"]};
    border: 1px solid transparent;
    font-size: 15px;
    padding: 9px 16px;
    border-radius: 6px;
}}
QPushButton#primary:hover {{ background: {t["accent_hover"]}; }}
QPushButton#primary:pressed {{ background: {t["accent_press"]}; }}
QPushButton#primary:disabled {{ background: {t["border"]};
                                color: {t["text_disabled"]}; }}

QListWidget {{
    background: {t["layer"]};
    border: 1px solid {t["border"]};
    border-radius: 8px;
    padding: 4px;
}}
QListWidget::item {{ padding: 6px 8px; border-radius: 4px; }}
QListWidget::item:hover {{ background: {t["layer_alt"]}; }}
QListWidget::item:selected {{ background: {t["sel"]}; color: {t["text"]}; }}

QPlainTextEdit#log {{
    background: {t["layer"]};
    border: 1px solid {t["border"]};
    border-radius: 8px;
    font-family: "{'", "'.join(MONO_STACK)}";
    font-size: 12.5px;
    padding: 6px;
}}
QPlainTextEdit#example {{ background: {t["layer_alt"]};
    border: 1px solid {t["border"]}; border-radius: 6px;
    font-family: "{'", "'.join(MONO_STACK)}"; font-size: 12.5px; }}

QProgressBar {{
    background: {t["border"]};
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{ background: {t["accent"]}; border-radius: 3px; }}

QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px;
                        border: 1px solid {t["control_border"]};
                        background: {t["layer"]}; }}
QCheckBox::indicator:checked {{ background: {t["accent"]};
                                border: 1px solid {t["accent"]}; }}
QCheckBox::indicator:hover {{ border: 1px solid {t["accent"]}; }}
QListWidget::indicator {{ width: 16px; height: 16px; border-radius: 3px;
                          border: 1px solid {t["control_border"]};
                          background: {t["layer"]}; }}
QListWidget::indicator:checked {{ background: {t["accent"]};
                                   border: 1px solid {t["accent"]}; }}
QToolTip {{ background: {t["layer"]}; color: {t["text"]};
            border: 1px solid {t["border"]}; padding: 4px 6px; }}

QDialog {{ background: {t["base"]}; }}
QMenuBar {{ background: transparent; }}
QMenu {{ background: {t["layer"]}; border: 1px solid {t["border"]};
         border-radius: 6px; padding: 4px; }}
QMenu::item {{ padding: 6px 18px; border-radius: 4px; }}
QMenu::item:selected {{ background: {t["sel"]}; }}

QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {t["border"]}; border-radius: 4px;
                               min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background: {t["text_disabled"]}; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {t["border"]}; border-radius: 4px;
                                 min-width: 28px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
"""


def apply(app, dark: bool | None = None, mica: bool = False) -> bool:
    """Postavi font + QSS na aplikaciju. Vrati da li je aktivna tamna tema."""
    from PySide6.QtGui import QFont

    dark = is_dark() if dark is None else dark
    font = QFont()
    font.setFamilies(FONT_STACK)
    font.setPointSizeF(10.0)
    app.setFont(font)
    app.setStyleSheet(qss(dark, mica))
    return dark


# --- Mica (Windows 11 backdrop) --------------------------------------------
_DWMWA_USE_IMMERSIVE_DARK_MODE = 20
_DWMWA_WINDOW_CORNER_PREFERENCE = 33
_DWMWA_SYSTEMBACKDROP_TYPE = 38
_DWMSBT_MAINWINDOW = 2  # Mica
_DWMWCP_ROUND = 2


def apply_mica(window) -> bool:
    """Ukljuci Mica za `window`. True SAMO ako je DWM poziv uspio.

    Ne-Windows: False. Svaka greska (stariji build, onemogucen DWM) -> False,
    bez izuzetka — tema tada ostaje solidna boja.
    """
    if not windows.is_windows():
        return False
    try:
        import ctypes

        hwnd = int(window.winId())
        dwm = ctypes.windll.dwmapi

        dark = ctypes.c_int(1 if is_dark() else 0)
        dwm.DwmSetWindowAttribute(hwnd, _DWMWA_USE_IMMERSIVE_DARK_MODE,
                                  ctypes.byref(dark), ctypes.sizeof(dark))
        backdrop = ctypes.c_int(_DWMSBT_MAINWINDOW)
        result = dwm.DwmSetWindowAttribute(
            hwnd, _DWMWA_SYSTEMBACKDROP_TYPE,
            ctypes.byref(backdrop), ctypes.sizeof(backdrop))
        if result != 0:
            return False
        corners = ctypes.c_int(_DWMWCP_ROUND)
        dwm.DwmSetWindowAttribute(hwnd, _DWMWA_WINDOW_CORNER_PREFERENCE,
                                  ctypes.byref(corners), ctypes.sizeof(corners))

        class MARGINS(ctypes.Structure):
            _fields_ = [("cxLeftWidth", ctypes.c_int),
                        ("cxRightWidth", ctypes.c_int),
                        ("cyTopHeight", ctypes.c_int),
                        ("cyBottomHeight", ctypes.c_int)]

        dwm.DwmExtendFrameIntoClientArea(
            hwnd, ctypes.byref(MARGINS(-1, -1, -1, -1)))
        return True
    except Exception:
        return False


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))


def app_icon():
    """QIcon aplikacije iz `assets/mujofix.ico`; prazan QIcon ako nema fajla."""
    from PySide6.QtGui import QIcon

    for base in (getattr(sys, "_MEIPASS", None), _repo_root()):
        if not base:
            continue
        path = os.path.join(base, "assets", "mujofix.ico")
        if os.path.isfile(path):
            return QIcon(path)
    return QIcon()


def _is_win11() -> bool:
    ver = windows.version()
    return bool(ver and ver[2] >= 22000)  # Mica trazi Win11 (build 22000+)


def setup(app, window) -> bool:
    """Primijeni Fluent 2 temu i, ako moze, Mica. Vrati je li Mica aktivna.

    Redoslijed je vazan: prvo solidna tema (radi svuda), pa Mica samo ako je
    DWM poziv uspio. Ako Mica padne (Win10, DWM off), translucent se
    ponistava — prozor nikad ne ostane providan bez pozadine.
    """
    dark = apply(app)
    icon = app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
        window.setWindowIcon(icon)
    if not (windows.is_windows() and _is_win11()):
        return False
    from PySide6.QtCore import Qt

    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    if apply_mica(window):
        apply(app, dark=dark, mica=True)
        return True
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    return False
