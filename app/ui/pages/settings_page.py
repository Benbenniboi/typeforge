from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QComboBox, QSlider, QCheckBox,
                               QScrollArea, QFrame, QMessageBox, QSizePolicy,
                               QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

from app.database import Database
from app.config import DB_PATH, APP_NAME, VERSION


class SectionHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            "color: #e94560; font-size: 12px; font-weight: bold; "
            "padding: 16px 0 6px 0; text-transform: uppercase; letter-spacing: 1px;"
        )


class SettingRow(QWidget):
    def __init__(self, label: str, control: QWidget, description: str = "", parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(12)

        info_col = QVBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #e0e0e0; font-size: 13px;")
        info_col.addWidget(lbl)
        if description:
            desc = QLabel(description)
            desc.setStyleSheet("color: #555570; font-size: 11px;")
            info_col.addWidget(desc)
        lay.addLayout(info_col)
        lay.addStretch()
        lay.addWidget(control)


class SettingsPage(QWidget):
    settings_changed = pyqtSignal(dict)
    theme_changed = pyqtSignal(str)

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(40, 24, 40, 40)
        lay.setSpacing(4)

        title = QLabel("Settings")
        title.setObjectName("title_label")
        lay.addWidget(title)

        # ── Appearance ────────────────────────────────────────────────────────
        lay.addWidget(SectionHeader("Appearance"))

        self._theme_combo = QComboBox()
        for t in ("dark", "light", "high_contrast", "solarized", "nord", "gruvbox", "catppuccin"):
            self._theme_combo.addItem(t.replace("_", " ").title(), t)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        lay.addWidget(SettingRow("Theme", self._theme_combo))

        self._font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self._font_size_slider.setRange(14, 28)
        self._font_size_slider.setFixedWidth(200)
        self._font_size_label = QLabel("18px")
        self._font_size_label.setFixedWidth(40)
        self._font_size_label.setStyleSheet("color: #888899;")
        font_row = QHBoxLayout()
        font_row.addWidget(self._font_size_slider)
        font_row.addWidget(self._font_size_label)
        font_widget = QWidget()
        font_widget.setLayout(font_row)
        self._font_size_slider.valueChanged.connect(
            lambda v: (self._font_size_label.setText(f"{v}px"), self._save_setting("font_size", str(v)), self._emit_settings())
        )
        lay.addWidget(SettingRow("Font Size", font_widget, "Size of the typing text"))

        self._caret_combo = QComboBox()
        for c in ("line", "block", "underline"):
            self._caret_combo.addItem(c.capitalize(), c)
        self._caret_combo.currentIndexChanged.connect(
            lambda: (self._save_setting("caret_style", self._caret_combo.currentData()), self._emit_settings())
        )
        lay.addWidget(SettingRow("Caret Style", self._caret_combo))

        # ── Behavior ──────────────────────────────────────────────────────────
        lay.addWidget(SectionHeader("Behavior"))

        self._stop_on_error_cb = QCheckBox()
        self._stop_on_error_cb.toggled.connect(
            lambda v: self._save_setting("stop_on_error", "true" if v else "false")
        )
        lay.addWidget(SettingRow("Stop on Error", self._stop_on_error_cb,
                                  "Lesson mode: prevent advancing until correct key is pressed"))

        self._hint_delay_slider = QSlider(Qt.Orientation.Horizontal)
        self._hint_delay_slider.setRange(1, 5)
        self._hint_delay_slider.setFixedWidth(200)
        self._hint_delay_label = QLabel("3s")
        self._hint_delay_label.setFixedWidth(30)
        self._hint_delay_label.setStyleSheet("color: #888899;")
        hint_row = QHBoxLayout()
        hint_row.addWidget(self._hint_delay_slider)
        hint_row.addWidget(self._hint_delay_label)
        hint_widget = QWidget()
        hint_widget.setLayout(hint_row)
        self._hint_delay_slider.valueChanged.connect(
            lambda v: (self._hint_delay_label.setText(f"{v}s"), self._save_setting("hint_delay", str(v)))
        )
        lay.addWidget(SettingRow("Hint Delay", hint_widget, "Seconds before finger hint appears in lesson mode"))

        self._show_wpm_cb = QCheckBox()
        self._show_wpm_cb.toggled.connect(
            lambda v: (self._save_setting("show_live_wpm", "true" if v else "false"), self._emit_settings())
        )
        lay.addWidget(SettingRow("Show Live WPM", self._show_wpm_cb))

        # ── Sound ─────────────────────────────────────────────────────────────
        lay.addWidget(SectionHeader("Sound"))

        self._sound_cb = QCheckBox()
        self._sound_cb.toggled.connect(
            lambda v: self._save_setting("sound_enabled", "true" if v else "false")
        )
        lay.addWidget(SettingRow("Key Sounds", self._sound_cb))

        self._sound_style_combo = QComboBox()
        for s in ("none", "soft", "mechanical"):
            self._sound_style_combo.addItem(s.capitalize(), s)
        self._sound_style_combo.currentIndexChanged.connect(
            lambda: self._save_setting("sound_style", self._sound_style_combo.currentData())
        )
        lay.addWidget(SettingRow("Sound Style", self._sound_style_combo))

        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setFixedWidth(200)
        self._vol_label = QLabel("50%")
        self._vol_label.setFixedWidth(40)
        self._vol_label.setStyleSheet("color: #888899;")
        vol_row = QHBoxLayout()
        vol_row.addWidget(self._volume_slider)
        vol_row.addWidget(self._vol_label)
        vol_widget = QWidget()
        vol_widget.setLayout(vol_row)
        self._volume_slider.valueChanged.connect(
            lambda v: (self._vol_label.setText(f"{v}%"), self._save_setting("sound_volume", str(v)))
        )
        lay.addWidget(SettingRow("Volume", vol_widget))

        # ── Data ──────────────────────────────────────────────────────────────
        lay.addWidget(SectionHeader("Data"))

        self._db_path_label = QLabel(str(DB_PATH))
        self._db_path_label.setStyleSheet("color: #4a4a6a; font-size: 11px;")
        self._db_path_label.setWordWrap(True)
        lay.addWidget(self._db_path_label)

        self._db_size_label = QLabel("")
        self._db_size_label.setStyleSheet("color: #4a4a6a; font-size: 11px;")
        lay.addWidget(self._db_size_label)

        clear_history_btn = QPushButton("Clear All Test History")
        clear_history_btn.setStyleSheet("color: #e94560; background: #2a1a1a;")
        clear_history_btn.clicked.connect(self._clear_history)
        lay.addWidget(SettingRow("Test History", clear_history_btn, "Permanently deletes all test results"))

        clear_lessons_btn = QPushButton("Clear Lesson Progress")
        clear_lessons_btn.setStyleSheet("color: #e94560; background: #2a1a1a;")
        clear_lessons_btn.clicked.connect(self._clear_lessons)
        lay.addWidget(SettingRow("Lesson Progress", clear_lessons_btn, "Resets all lesson unlocks and stars"))

        # ── About ─────────────────────────────────────────────────────────────
        lay.addWidget(SectionHeader("About"))

        about_text = QLabel(
            f"{APP_NAME} v{VERSION} — MIT License\n"
            "Free and open source software.\nNo ads, no telemetry, no accounts required."
        )
        about_text.setStyleSheet("color: #666688; font-size: 13px; line-height: 1.6;")
        about_text.setWordWrap(True)
        lay.addWidget(about_text)

        gh_btn = QPushButton("View on GitHub")
        gh_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://github.com/typeforge/typeforge")
        ))
        lay.addWidget(gh_btn)

        lay.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def _load_settings(self):
        s = self._db.get_all_settings()

        theme = s.get("theme", "dark")
        for i in range(self._theme_combo.count()):
            if self._theme_combo.itemData(i) == theme:
                self._theme_combo.setCurrentIndex(i)
                break

        self._font_size_slider.setValue(int(s.get("font_size", 18)))
        self._font_size_label.setText(f"{int(s.get('font_size', 18))}px")

        caret = s.get("caret_style", "line")
        for i in range(self._caret_combo.count()):
            if self._caret_combo.itemData(i) == caret:
                self._caret_combo.setCurrentIndex(i)
                break

        self._stop_on_error_cb.setChecked(s.get("stop_on_error") == "true")
        self._hint_delay_slider.setValue(int(s.get("hint_delay", 3)))
        self._hint_delay_label.setText(f"{int(s.get('hint_delay', 3))}s")
        self._show_wpm_cb.setChecked(s.get("show_live_wpm", "true") == "true")
        self._sound_cb.setChecked(s.get("sound_enabled") == "true")

        sound_style = s.get("sound_style", "soft")
        for i in range(self._sound_style_combo.count()):
            if self._sound_style_combo.itemData(i) == sound_style:
                self._sound_style_combo.setCurrentIndex(i)
                break

        self._volume_slider.setValue(int(s.get("sound_volume", 50)))
        self._vol_label.setText(f"{int(s.get('sound_volume', 50))}%")

        size_bytes = self._db.get_db_size()
        size_kb = size_bytes / 1024
        self._db_size_label.setText(f"Database size: {size_kb:.1f} KB")

    def _save_setting(self, key: str, value: str):
        self._db.set_setting(key, value)

    def _on_theme_changed(self):
        theme = self._theme_combo.currentData()
        self._save_setting("theme", theme)
        self.theme_changed.emit(theme)

    def _emit_settings(self):
        self.settings_changed.emit(self._db.get_all_settings())

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "Clear History",
            "This will permanently delete all test history. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._db.clear_test_history()

    def _clear_lessons(self):
        reply = QMessageBox.question(
            self, "Clear Lesson Progress",
            "This will reset all lesson progress and unlock status. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._db.clear_lesson_progress()
