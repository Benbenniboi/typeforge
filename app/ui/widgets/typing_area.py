from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import (QPainter, QColor, QFont, QPen, QFontMetrics,
                          QKeyEvent, QPainterPath, QBrush)

from app.core.engine import TypingEngine, TestResult


class TypingArea(QWidget):
    key_pressed = pyqtSignal(str, bool)
    test_complete = pyqtSignal(object)
    wpm_updated = pyqtSignal(float, float)
    first_keypress = pyqtSignal()

    _COLORS = {
        "untyped":    QColor("#363645"),
        "correct":    QColor("#c8d6e8"),
        "error":      QColor("#c84b55"),
        "error_bg":   QColor("#1f0e10"),
        "caret":      QColor("#4d9de0"),
        "bg":         QColor("#0b0b0f"),
        "wpm_text":   QColor("#2e2e42"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine: TypingEngine | None = None
        self._mode = "test"
        self._font_size = 20
        self._caret_style = "line"
        self._caret_visible = True
        self._started = False
        self._hint_char = ""

        self._font = QFont("JetBrains Mono", self._font_size)
        self._fm = QFontMetrics(self._font)

        self._lines: list[str] = []
        self._line_start_positions: list[int] = []
        self._current_line = 0
        self._scroll_offset = 0.0

        self._caret_timer = QTimer(self)
        self._caret_timer.timeout.connect(self._blink_caret)
        self._caret_timer.start(530)

        self._wpm_timer = QTimer(self)
        self._wpm_timer.timeout.connect(self._emit_wpm)
        self._wpm_timer.start(500)

        self._hint_timer = QTimer(self)
        self._hint_timer.setSingleShot(True)
        self._hint_timer.timeout.connect(self._show_hint)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(160)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    def set_theme(self, colors: dict):
        self._COLORS.update(colors)
        self.update()

    def set_font_size(self, size: int):
        self._font_size = size
        self._font = QFont("JetBrains Mono", size)
        self._fm = QFontMetrics(self._font)
        self._layout_text()
        self.update()

    def set_caret_style(self, style: str):
        self._caret_style = style
        self.update()

    def set_mode(self, mode: str):
        self._mode = mode

    def load_text(self, text: str, mode: str = "words", duration: int = 0):
        self.engine = TypingEngine(text, mode=mode, duration=duration)
        self._mode = mode
        self._started = False
        self._hint_char = ""
        self._caret_visible = True
        self._layout_text()
        self.update()
        self.setFocus()

    def _layout_text(self):
        if not self.engine:
            return
        self._lines = []
        self._line_start_positions = []
        text = self.engine.target
        max_w = max(self.width() - 80, 400)
        words = text.split(" ")
        current_line = ""
        pos = 0
        line_start = 0

        for i, word in enumerate(words):
            test = current_line + (" " if current_line else "") + word
            if self._fm.horizontalAdvance(test) > max_w and current_line:
                self._lines.append(current_line)
                self._line_start_positions.append(line_start)
                line_start = pos
                current_line = word
            else:
                current_line = test
            pos += len(word) + (1 if i < len(words) - 1 else 0)

        if current_line:
            self._lines.append(current_line)
            self._line_start_positions.append(line_start)

    def _get_current_line_index(self) -> int:
        if not self.engine:
            return 0
        pos = self.engine.current_position
        for i in range(len(self._line_start_positions) - 1, -1, -1):
            if pos >= self._line_start_positions[i]:
                return i
        return 0

    def keyPressEvent(self, event: QKeyEvent):
        if not self.engine or self.engine.is_complete:
            return

        key = event.key()
        text = event.text()

        if key == Qt.Key.Key_Backspace:
            char = "\x08"
        elif key == Qt.Key.Key_Tab:
            return
        elif key == Qt.Key.Key_Escape:
            return
        elif text and text.isprintable():
            char = text
        else:
            return

        if not self._started and char != "\x08":
            self._started = True
            self.first_keypress.emit()

        if self._mode == "lesson":
            self._hint_timer.stop()
            self._hint_char = ""
            self._hint_timer.start(3000)

        correct = self.engine.process_key(char)

        if char != "\x08":
            self.key_pressed.emit(char, correct)

        if self.engine.is_complete:
            result = self.engine.get_result()
            self.test_complete.emit(result)
            self._hint_timer.stop()

        self._current_line = self._get_current_line_index()
        self.update()

    def _blink_caret(self):
        self._caret_visible = not self._caret_visible
        self.update()

    def _emit_wpm(self):
        if self.engine and self._started:
            self.wpm_updated.emit(self.engine.wpm, self.engine.raw_wpm)

    def _show_hint(self):
        if self.engine and not self.engine.is_complete:
            self._hint_char = self.engine.target[self.engine.current_position] if self.engine.current_position < len(self.engine.target) else ""
            self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_text()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, self._COLORS["bg"])

        if not self.engine or not self._lines:
            painter.setPen(QPen(self._COLORS["untyped"]))
            painter.setFont(self._font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Load a text to begin typing...")
            return

        line_h = self._fm.height() + 10
        visible_lines = 3
        total_h_needed = visible_lines * line_h
        start_y = (h - total_h_needed) // 2 + self._fm.ascent()

        cur_line = self._current_line
        first_visible = max(0, cur_line - 1)
        typed_pairs = self.engine.typed_pairs
        pos = self.engine.current_position

        for rel_idx in range(visible_lines):
            line_idx = first_visible + rel_idx
            if line_idx >= len(self._lines):
                break

            line_text = self._lines[line_idx]
            line_start = self._line_start_positions[line_idx]
            y = start_y + rel_idx * line_h

            alpha = 255 if line_idx == cur_line else (180 if abs(line_idx - cur_line) == 1 else 80)

            x = (w - self._fm.horizontalAdvance(line_text)) // 2

            for char_rel, ch in enumerate(line_text):
                char_abs = line_start + char_rel
                char_x = x + self._fm.horizontalAdvance(line_text[:char_rel])
                char_w = self._fm.horizontalAdvance(ch)

                if char_abs < len(typed_pairs):
                    _, correct = typed_pairs[char_abs]
                    if correct:
                        color = QColor(self._COLORS["correct"])
                    else:
                        painter.fillRect(char_x, y - self._fm.ascent(), char_w, line_h - 4,
                                         self._COLORS["error_bg"])
                        color = QColor(self._COLORS["error"])
                elif char_abs == pos and self._caret_visible:
                    color = QColor(self._COLORS["untyped"])
                else:
                    color = QColor(self._COLORS["untyped"])

                color.setAlpha(alpha)
                painter.setPen(QPen(color))
                painter.setFont(self._font)
                painter.drawText(char_x, y, ch)

                if char_abs == pos and line_idx == cur_line:
                    self._draw_caret(painter, char_x, y, char_w, line_h)

        if self._hint_char and self._mode == "lesson":
            self._draw_hint(painter, w, h)

        if self._mode in ("test", "timed") and self._started and self.engine:
            self._draw_live_wpm(painter, w)

    def _draw_caret(self, painter: QPainter, x: int, y: int, char_w: int, line_h: int):
        if not self._caret_visible:
            return
        c = self._COLORS["caret"]
        if self._caret_style == "block":
            block_color = QColor(c)
            block_color.setAlpha(80)
            painter.fillRect(x, y - self._fm.ascent(), char_w, line_h - 4, block_color)
        elif self._caret_style == "underline":
            painter.setPen(QPen(c, 2))
            painter.drawLine(x, y + 2, x + char_w, y + 2)
        else:
            painter.setPen(QPen(c, 2))
            painter.drawLine(x, y - self._fm.ascent(), x, y + self._fm.descent())

    def _draw_hint(self, painter: QPainter, w: int, h: int):
        hint_text = f"Next key: {self._hint_char}"
        font = QFont("Segoe UI", 12)
        painter.setFont(font)
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(hint_text) + 16
        th = fm.height() + 8
        x = (w - tw) // 2
        y = h - th - 10
        bg = QColor(60, 60, 80, 200)
        painter.fillRect(x, y, tw, th, bg)
        painter.setPen(QPen(QColor("#aaaacc")))
        painter.drawText(x, y, tw, th, Qt.AlignmentFlag.AlignCenter, hint_text)

    def _draw_live_wpm(self, painter: QPainter, w: int):
        if not self.engine:
            return
        wpm_text = f"{self.engine.wpm:.0f} WPM"
        font = QFont("JetBrains Mono", 13)
        painter.setFont(font)
        painter.setPen(QPen(self._COLORS["wpm_text"]))
        fm = QFontMetrics(font)
        x = w - fm.horizontalAdvance(wpm_text) - 16
        painter.drawText(x, 24, wpm_text)

    def get_engine(self) -> TypingEngine | None:
        return self.engine

    def reset(self, new_text: str = None):
        if self.engine:
            self.engine.reset(new_text)
        self._started = False
        self._hint_char = ""
        self._caret_visible = True
        self._hint_timer.stop()
        self._current_line = 0
        if new_text:
            self._layout_text()
        self.update()
        self.setFocus()
