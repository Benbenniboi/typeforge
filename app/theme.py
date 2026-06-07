from __future__ import annotations
from PyQt6.QtWidgets import QApplication

# ── Palette definitions ───────────────────────────────────────────────────────

THEMES = {
    "dark": {
        "background":  "#0b0b0f",
        "surface":     "#0f0f16",
        "surface2":    "#141420",
        "sidebar":     "#080810",
        "text":        "#d0d0d8",
        "muted":       "#2e2e42",
        "muted2":      "#505068",
        "accent":      "#4d9de0",
        "accent_dim":  "#1e3a58",
        "correct":     "#c8d6e8",
        "error":       "#c84b55",
        "error_bg":    "#1f0e10",
        "caret":       "#4d9de0",
        "border":      "#13131e",
    },
    "light": {
        "background":  "#f0f0f5",
        "surface":     "#ffffff",
        "surface2":    "#e4e4ee",
        "sidebar":     "#e8e8f0",
        "text":        "#1a1a2e",
        "muted":       "#c0c0d0",
        "muted2":      "#8080a0",
        "accent":      "#2979c8",
        "accent_dim":  "#d0e4f8",
        "correct":     "#1a3a6a",
        "error":       "#c0303a",
        "error_bg":    "#fce8ea",
        "caret":       "#2979c8",
        "border":      "#d8d8e8",
    },
    "high_contrast": {
        "background":  "#000000",
        "surface":     "#0a0a0a",
        "surface2":    "#141414",
        "sidebar":     "#000000",
        "text":        "#ffffff",
        "muted":       "#333333",
        "muted2":      "#666666",
        "accent":      "#00aaff",
        "accent_dim":  "#002244",
        "correct":     "#00ff88",
        "error":       "#ff2244",
        "error_bg":    "#220008",
        "caret":       "#00aaff",
        "border":      "#222222",
    },
    "solarized": {
        "background":  "#002b36",
        "surface":     "#073642",
        "surface2":    "#073642",
        "sidebar":     "#001e26",
        "text":        "#839496",
        "muted":       "#073642",
        "muted2":      "#586e75",
        "accent":      "#268bd2",
        "accent_dim":  "#0a2a42",
        "correct":     "#859900",
        "error":       "#dc322f",
        "error_bg":    "#2a0f0e",
        "caret":       "#268bd2",
        "border":      "#073642",
    },
    "nord": {
        "background":  "#2e3440",
        "surface":     "#3b4252",
        "surface2":    "#434c5e",
        "sidebar":     "#242933",
        "text":        "#eceff4",
        "muted":       "#3b4252",
        "muted2":      "#4c566a",
        "accent":      "#88c0d0",
        "accent_dim":  "#1e3040",
        "correct":     "#a3be8c",
        "error":       "#bf616a",
        "error_bg":    "#2a1518",
        "caret":       "#88c0d0",
        "border":      "#3b4252",
    },
    "gruvbox": {
        "background":  "#1d2021",
        "surface":     "#282828",
        "surface2":    "#3c3836",
        "sidebar":     "#161819",
        "text":        "#ebdbb2",
        "muted":       "#3c3836",
        "muted2":      "#665c54",
        "accent":      "#83a598",
        "accent_dim":  "#1a2828",
        "correct":     "#b8bb26",
        "error":       "#fb4934",
        "error_bg":    "#2d1010",
        "caret":       "#83a598",
        "border":      "#3c3836",
    },
    "catppuccin": {
        "background":  "#1e1e2e",
        "surface":     "#181825",
        "surface2":    "#313244",
        "sidebar":     "#181825",
        "text":        "#cdd6f4",
        "muted":       "#313244",
        "muted2":      "#45475a",
        "accent":      "#89b4fa",
        "accent_dim":  "#1e2848",
        "correct":     "#a6e3a1",
        "error":       "#f38ba8",
        "error_bg":    "#2a1020",
        "caret":       "#89b4fa",
        "border":      "#313244",
    },
}


def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES["dark"])


def apply_theme(app: QApplication, theme_name: str):
    t = get_theme(theme_name)
    qss = f"""
    /* ── Base ── */
    QMainWindow, QWidget {{
        background-color: {t['background']};
        color: {t['text']};
        font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
        font-size: 13px;
    }}

    /* ── Sidebar ── */
    QWidget#sidebar {{
        background-color: {t['sidebar']};
        border-right: 1px solid {t['border']};
    }}

    /* ── Nav buttons ── */
    QPushButton#nav_button {{
        background-color: transparent;
        color: {t['muted2']};
        border: none;
        text-align: left;
        padding: 9px 14px;
        font-size: 12px;
        font-family: 'JetBrains Mono', monospace;
        border-radius: 4px;
        letter-spacing: 0.5px;
    }}
    QPushButton#nav_button:hover {{
        background-color: {t['surface2']};
        color: {t['text']};
    }}
    QPushButton#nav_button:checked {{
        background-color: transparent;
        color: {t['accent']};
    }}

    /* ── Generic buttons ── */
    QPushButton {{
        background-color: transparent;
        color: {t['muted2']};
        border: 1px solid {t['border']};
        padding: 7px 16px;
        border-radius: 4px;
        font-size: 12px;
        font-family: 'JetBrains Mono', monospace;
    }}
    QPushButton:hover {{
        border-color: {t['muted2']};
        color: {t['text']};
        background-color: {t['surface2']};
    }}
    QPushButton:pressed {{
        border-color: {t['accent']};
        color: {t['accent']};
    }}

    QPushButton#accent_button {{
        background-color: {t['accent_dim']};
        color: {t['accent']};
        border: 1px solid {t['accent']};
        font-weight: bold;
        padding: 9px 24px;
        font-size: 13px;
        letter-spacing: 0.5px;
    }}
    QPushButton#accent_button:hover {{
        background-color: {t['accent']};
        color: {t['background']};
    }}

    /* ── Combobox ── */
    QComboBox {{
        background-color: transparent;
        color: {t['muted2']};
        border: 1px solid {t['border']};
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 12px;
        font-family: 'JetBrains Mono', monospace;
    }}
    QComboBox:hover {{
        border-color: {t['muted2']};
        color: {t['text']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {t['surface']};
        color: {t['text']};
        selection-background-color: {t['surface2']};
        border: 1px solid {t['border']};
        outline: none;
    }}

    /* ── Sliders ── */
    QSlider::groove:horizontal {{
        background: {t['surface2']};
        height: 2px;
        border-radius: 1px;
    }}
    QSlider::handle:horizontal {{
        background: {t['accent']};
        width: 12px;
        height: 12px;
        margin: -5px 0;
        border-radius: 6px;
    }}
    QSlider::sub-page:horizontal {{
        background: {t['accent']};
        border-radius: 1px;
    }}

    /* ── Scroll ── */
    QScrollArea {{
        background-color: {t['background']};
        border: none;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: {t['muted']};
        border-radius: 3px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {t['muted2']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    /* ── Labels ── */
    QLabel {{
        background-color: transparent;
    }}
    QLabel#title_label {{
        font-size: 20px;
        font-weight: bold;
        color: {t['text']};
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.5px;
    }}
    QLabel#muted_label {{
        color: {t['muted2']};
        font-size: 11px;
    }}

    /* ── Checkboxes ── */
    QCheckBox {{
        color: {t['muted2']};
        spacing: 8px;
        font-size: 12px;
    }}
    QCheckBox:hover {{
        color: {t['text']};
    }}
    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border-radius: 2px;
        border: 1px solid {t['muted2']};
        background: transparent;
    }}
    QCheckBox::indicator:checked {{
        background-color: {t['accent']};
        border-color: {t['accent']};
    }}

    /* ── Dividers ── */
    QFrame#divider {{
        background-color: {t['border']};
        max-height: 1px;
    }}

    /* ── Dialogs ── */
    QDialog {{
        background-color: {t['surface']};
        border: 1px solid {t['border']};
    }}

    /* ── Tables ── */
    QTableWidget {{
        background-color: transparent;
        color: {t['text']};
        gridline-color: {t['border']};
        border: none;
        font-size: 12px;
        font-family: 'JetBrains Mono', monospace;
    }}
    QTableWidget::item:selected {{
        background-color: {t['surface2']};
        color: {t['text']};
    }}
    QTableWidget::item:hover {{
        background-color: {t['surface']};
    }}
    QHeaderView::section {{
        background-color: transparent;
        color: {t['muted2']};
        padding: 8px 12px;
        border: none;
        border-bottom: 1px solid {t['border']};
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-family: 'JetBrains Mono', monospace;
    }}

    /* ── Text inputs ── */
    QLineEdit, QTextEdit {{
        background-color: {t['surface']};
        color: {t['text']};
        border: 1px solid {t['border']};
        padding: 7px 10px;
        border-radius: 4px;
        font-size: 13px;
        font-family: 'JetBrains Mono', monospace;
    }}
    QLineEdit:focus, QTextEdit:focus {{
        border-color: {t['accent']};
        outline: none;
    }}

    /* ── Message box ── */
    QMessageBox {{
        background-color: {t['surface']};
    }}
    QMessageBox QLabel {{
        color: {t['text']};
    }}

    /* ── Splitter ── */
    QSplitter::handle {{
        background-color: {t['border']};
    }}

    /* ── Stacked widget / pages ── */
    QStackedWidget {{
        background-color: {t['background']};
    }}

    /* ── Tooltip ── */
    QToolTip {{
        background-color: {t['surface2']};
        color: {t['text']};
        border: 1px solid {t['border']};
        padding: 4px 8px;
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
    }}
    """
    app.setStyleSheet(qss)
