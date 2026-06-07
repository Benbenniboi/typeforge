from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QComboBox, QCheckBox, QStackedWidget,
                               QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent

from app.ui.widgets.typing_area import TypingArea
from app.ui.widgets.wpm_graph import WpmGraph
from app.ui.widgets.results_panel import ResultsPanel
from app.core.text_generator import TextGenerator
from app.core.engine import TestResult
from app.database import Database


class TestPage(QWidget):
    test_finished = pyqtSignal(object)

    WORD_COUNTS = [10, 25, 50, 100]
    DURATIONS = [15, 30, 60, 120]

    def __init__(self, db: Database, text_gen: TextGenerator, parent=None):
        super().__init__(parent)
        self._db = db
        self._text_gen = text_gen
        self._mode = "words"
        self._word_count = 25
        self._duration = 60
        self._word_list = "english_200"
        self._punctuation = False
        self._numbers = False
        self._countdown = 0
        self._time_elapsed = 0.0

        self._setup_ui()
        self._connect_signals()
        self._load_settings()
        self._new_test()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        # ── Typing view ──────────────────────────────────────────────────────
        typing_widget = QWidget()
        typing_layout = QVBoxLayout(typing_widget)
        typing_layout.setContentsMargins(40, 20, 40, 20)
        typing_layout.setSpacing(12)

        # Top control bar
        ctrl_bar = QHBoxLayout()
        ctrl_bar.setSpacing(8)

        self._mode_btns: dict[str, QPushButton] = {}
        for mode in ("words", "time", "quote", "code"):
            btn = QPushButton(mode.capitalize())
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setProperty("mode_btn", True)
            btn.setStyleSheet("""
                QPushButton { background: transparent; border: none; color: #363650;
                              padding: 4px 12px; border-radius: 0px; font-size: 12px;
                              font-family: 'JetBrains Mono', monospace; letter-spacing: 0.5px; }
                QPushButton:hover { color: #8090b0; }
                QPushButton:checked { color: #4d9de0; border-bottom: 2px solid #4d9de0; }
            """)
            btn.clicked.connect(lambda checked, m=mode: self._set_mode(m))
            self._mode_btns[mode] = btn
            ctrl_bar.addWidget(btn)

        ctrl_bar.addWidget(self._make_sep())

        self._sub_stack = QStackedWidget()
        self._sub_stack.setFixedHeight(32)

        # Words sub-options
        words_sub = QWidget()
        words_sub_lay = QHBoxLayout(words_sub)
        words_sub_lay.setContentsMargins(0, 0, 0, 0)
        words_sub_lay.setSpacing(4)
        self._word_count_btns: dict[int, QPushButton] = {}
        for wc in self.WORD_COUNTS:
            btn = QPushButton(str(wc))
            btn.setCheckable(True)
            btn.setFixedSize(36, 28)
            btn.setStyleSheet("""
                QPushButton { background: transparent; border: none; color: #363650;
                              border-radius: 4px; font-size: 12px;
                              font-family: 'JetBrains Mono', monospace; }
                QPushButton:hover { color: #8090b0; }
                QPushButton:checked { color: #4d9de0; }
            """)
            btn.clicked.connect(lambda checked, w=wc: self._set_word_count(w))
            self._word_count_btns[wc] = btn
            words_sub_lay.addWidget(btn)
        self._sub_stack.addWidget(words_sub)

        # Time sub-options
        time_sub = QWidget()
        time_sub_lay = QHBoxLayout(time_sub)
        time_sub_lay.setContentsMargins(0, 0, 0, 0)
        time_sub_lay.setSpacing(4)
        self._duration_btns: dict[int, QPushButton] = {}
        for d in self.DURATIONS:
            btn = QPushButton(str(d))
            btn.setCheckable(True)
            btn.setFixedSize(36, 28)
            btn.setStyleSheet("""
                QPushButton { background: transparent; border: none; color: #363650;
                              border-radius: 4px; font-size: 12px;
                              font-family: 'JetBrains Mono', monospace; }
                QPushButton:hover { color: #8090b0; }
                QPushButton:checked { color: #4d9de0; }
            """)
            btn.clicked.connect(lambda checked, d_=d: self._set_duration(d_))
            self._duration_btns[d] = btn
            time_sub_lay.addWidget(btn)
        self._sub_stack.addWidget(time_sub)

        # Quote/Code: empty sub
        self._sub_stack.addWidget(QWidget())
        self._sub_stack.addWidget(QWidget())

        ctrl_bar.addWidget(self._sub_stack)
        ctrl_bar.addStretch()

        self._punct_cb = QCheckBox("punctuation")
        self._punct_cb.setStyleSheet("color: #363650; font-size: 12px; font-family: 'JetBrains Mono', monospace;")
        self._numbers_cb = QCheckBox("numbers")
        self._numbers_cb.setStyleSheet("color: #363650; font-size: 12px; font-family: 'JetBrains Mono', monospace;")
        ctrl_bar.addWidget(self._punct_cb)
        ctrl_bar.addWidget(self._numbers_cb)

        self._word_list_combo = QComboBox()
        self._word_list_combo.setFixedHeight(28)
        self._word_list_combo.setStyleSheet("font-size: 12px;")
        for wl in ("english_200", "english_1000", "code_python", "code_javascript"):
            self._word_list_combo.addItem(wl)
        ctrl_bar.addWidget(self._word_list_combo)

        typing_layout.addLayout(ctrl_bar)

        # Timer / countdown label
        self._timer_label = QLabel("")
        self._timer_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._timer_label.setStyleSheet("color: #4d9de0; font-size: 32px; font-weight: bold; font-family: 'JetBrains Mono', monospace;")
        self._timer_label.setVisible(False)
        typing_layout.addWidget(self._timer_label)

        # Typing area
        self._typing_area = TypingArea()
        self._typing_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        typing_layout.addWidget(self._typing_area, 1)

        # Live graph (hidden until first keypress)
        self._live_graph = WpmGraph()
        self._live_graph.setMinimumHeight(100)
        self._live_graph.setMaximumHeight(120)
        self._live_graph.setVisible(False)
        typing_layout.addWidget(self._live_graph)

        # Restart hint
        hint = QLabel("tab  —  restart")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #1c1c28; font-size: 11px; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px;")
        typing_layout.addWidget(hint)

        self._stack.addWidget(typing_widget)

        # ── Results view ─────────────────────────────────────────────────────
        self._results_panel = ResultsPanel()
        self._stack.addWidget(self._results_panel)

        # ── Timers ───────────────────────────────────────────────────────────
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._tick_countdown)

    def _make_sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet("background: #13131e;")
        return sep

    def _connect_signals(self):
        self._typing_area.first_keypress.connect(self._on_first_keypress)
        self._typing_area.test_complete.connect(self._on_test_complete)
        self._typing_area.wpm_updated.connect(self._on_wpm_updated)
        self._typing_area.key_pressed.connect(self._on_key_pressed)
        self._results_panel.restart_requested.connect(self._new_test)
        self._results_panel.next_test_requested.connect(self._new_test)
        self._punct_cb.toggled.connect(self._on_options_changed)
        self._numbers_cb.toggled.connect(self._on_options_changed)
        self._word_list_combo.currentTextChanged.connect(self._on_options_changed)

    def _load_settings(self):
        mode = self._db.get_setting("last_mode") or "words"
        self._set_mode(mode, new_test=False)

        wc = int(self._db.get_setting("last_word_count") or 25)
        self._set_word_count(wc, new_test=False)

        d = int(self._db.get_setting("last_duration") or 60)
        self._set_duration(d, new_test=False)

        wl = self._db.get_setting("last_word_list") or "english_200"
        idx = self._word_list_combo.findText(wl)
        if idx >= 0:
            self._word_list_combo.setCurrentIndex(idx)
            self._word_list = wl

        self._punctuation = self._db.get_setting("punctuation") == "true"
        self._punct_cb.setChecked(self._punctuation)
        self._numbers = self._db.get_setting("numbers_mode") == "true"
        self._numbers_cb.setChecked(self._numbers)

    def _set_mode(self, mode: str, new_test: bool = True):
        self._mode = mode
        for m, btn in self._mode_btns.items():
            btn.setChecked(m == mode)

        mode_idx = {"words": 0, "time": 1, "quote": 2, "code": 3}
        self._sub_stack.setCurrentIndex(mode_idx.get(mode, 0))
        self._word_list_combo.setVisible(mode in ("words", "time"))
        self._punct_cb.setVisible(mode in ("words", "time"))
        self._numbers_cb.setVisible(mode in ("words", "time"))

        if new_test:
            self._db.set_setting("last_mode", mode)
            self._new_test()

    def _set_word_count(self, count: int, new_test: bool = True):
        self._word_count = count
        for wc, btn in self._word_count_btns.items():
            btn.setChecked(wc == count)
        if new_test:
            self._db.set_setting("last_word_count", str(count))
            self._new_test()

    def _set_duration(self, duration: int, new_test: bool = True):
        self._duration = duration
        for d, btn in self._duration_btns.items():
            btn.setChecked(d == duration)
        if new_test:
            self._db.set_setting("last_duration", str(duration))
            self._new_test()

    def _on_options_changed(self):
        self._punctuation = self._punct_cb.isChecked()
        self._numbers = self._numbers_cb.isChecked()
        self._word_list = self._word_list_combo.currentText()
        self._db.set_setting("punctuation", "true" if self._punctuation else "false")
        self._db.set_setting("numbers_mode", "true" if self._numbers else "false")
        self._db.set_setting("last_word_list", self._word_list)
        self._new_test()

    def _generate_text(self) -> str:
        if self._mode == "quote":
            return self._text_gen.generate_quote()
        if self._mode == "code":
            return self._text_gen.generate_code("python", 8)
        if self._mode == "time":
            return self._text_gen.generate_words(
                self._word_list, count=200,
                punctuation=self._punctuation, numbers=self._numbers
            )
        return self._text_gen.generate_words(
            self._word_list, count=self._word_count,
            punctuation=self._punctuation, numbers=self._numbers
        )

    def _new_test(self):
        self._countdown_timer.stop()
        self._timer_label.setVisible(False)
        self._live_graph.reset()
        self._live_graph.setVisible(False)
        self._stack.setCurrentIndex(0)

        text = self._generate_text()
        duration = self._duration if self._mode == "time" else 0
        self._typing_area.load_text(text, mode=self._mode, duration=duration)
        self._countdown = self._duration

    def _on_first_keypress(self):
        self._live_graph.setVisible(True)
        if self._mode == "time":
            self._countdown = self._duration
            self._timer_label.setText(str(self._countdown))
            self._timer_label.setVisible(True)
            self._countdown_timer.start()

    def _tick_countdown(self):
        self._countdown -= 1
        self._timer_label.setText(str(self._countdown))
        if self._countdown <= 0:
            self._countdown_timer.stop()
            engine = self._typing_area.get_engine()
            if engine:
                result = engine.get_result(mode=f"time_{self._duration}", duration=self._duration)
                self._on_test_complete(result)

    def _on_wpm_updated(self, wpm: float, raw_wpm: float):
        self._live_graph.update_wpm(wpm, raw_wpm)

    def _on_key_pressed(self, char: str, correct: bool):
        if not correct and self._typing_area.get_engine():
            e = self._typing_area.get_engine()
            self._live_graph.add_error_marker(e.elapsed_seconds, e.wpm)

    def _on_test_complete(self, result: TestResult):
        self._countdown_timer.stop()
        if self._mode == "words":
            result.mode = f"words_{self._word_count}"
        elif self._mode == "time":
            result.mode = f"time_{self._duration}"

        row_id = self._db.save_test_result(result)
        result.id = row_id

        pb = self._db.get_personal_best_for_mode(result.mode)
        is_pb = pb is None or result.wpm > pb.wpm
        pb_wpm = result.wpm if is_pb else (pb.wpm if pb else 0)

        self._results_panel.show_result(result, is_pb=is_pb, pb_wpm=pb_wpm)
        self._stack.setCurrentIndex(1)
        self.test_finished.emit(result)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Tab:
            self._new_test()
        else:
            super().keyPressEvent(event)

    def apply_settings(self, settings: dict):
        fs = int(settings.get("font_size", 18))
        self._typing_area.set_font_size(fs)
        self._typing_area.set_caret_style(settings.get("caret_style", "line"))
