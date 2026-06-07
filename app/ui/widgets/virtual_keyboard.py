from __future__ import annotations
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath

FINGER_COLORS = {
    "left_pinky":  QColor("#e85555"),
    "left_ring":   QColor("#e8a135"),
    "left_middle": QColor("#e8d735"),
    "left_index":  QColor("#55bb55"),
    "right_index": QColor("#5588e8"),
    "right_middle":QColor("#8855e8"),
    "right_ring":  QColor("#bb55e8"),
    "right_pinky": QColor("#e855bb"),
    "thumb":       QColor("#888888"),
}

FINGER_MAP = {
    "q": "left_pinky", "a": "left_pinky", "z": "left_pinky",
    "1": "left_pinky", "`": "left_pinky",
    "w": "left_ring",  "s": "left_ring",  "x": "left_ring",  "2": "left_ring",
    "e": "left_middle","d": "left_middle", "c": "left_middle","3": "left_middle",
    "r": "left_index", "f": "left_index", "v": "left_index",
    "t": "left_index", "g": "left_index", "b": "left_index",
    "4": "left_index", "5": "left_index",
    "y": "right_index","h": "right_index","n": "right_index",
    "u": "right_index","j": "right_index","m": "right_index",
    "6": "right_index","7": "right_index",
    "i": "right_middle","k": "right_middle",",": "right_middle","8": "right_middle",
    "o": "right_ring",  "l": "right_ring", ".": "right_ring", "9": "right_ring",
    "p": "right_pinky", ";": "right_pinky","/": "right_pinky","0": "right_pinky",
    "'": "right_pinky","[": "right_pinky","]": "right_pinky",
    "\\":"right_pinky","-": "right_pinky","=": "right_pinky",
    " ": "thumb",
}

ROWS = [
    ["`","1","2","3","4","5","6","7","8","9","0","-","=","⌫"],
    ["⇥","q","w","e","r","t","y","u","i","o","p","[","]","\\"],
    ["⇪","a","s","d","f","g","h","j","k","l",";","'","↵"],
    ["⇧","z","x","c","v","b","n","m",",",".","/","⇧"],
    ["ctrl","alt","⎵","alt","ctrl"],
]

WIDE_KEYS = {"⌫": 2.0, "⇥": 1.5, "⇪": 1.75, "↵": 2.25,
             "⇧": 2.25, "ctrl": 1.5, "alt": 1.25, "⎵": 6.25}


class VirtualKeyboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._highlighted: set[str] = set()
        self._anchor: set[str] = set()
        self.setMinimumHeight(140)
        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            self.sizePolicy().verticalPolicy()
        )
        self._theme = {
            "key_bg": QColor("#2a2a3a"),
            "key_text": QColor("#cccccc"),
            "key_border": QColor("#3a3a5a"),
            "highlight_bg": QColor("#ffffff"),
            "highlight_text": QColor("#000000"),
            "anchor_bg": QColor("#666688"),
        }

    def set_theme_colors(self, bg: str, border: str, text: str, accent: str):
        self._theme["key_bg"] = QColor(bg)
        self._theme["key_border"] = QColor(border)
        self._theme["key_text"] = QColor(text)
        self._theme["highlight_bg"] = QColor(accent)
        self.update()

    def highlight_key(self, char: str):
        self._highlighted = {char.lower()}
        self.update()

    def highlight_anchor(self, chars: list[str]):
        self._anchor = {c.lower() for c in chars}
        self.update()

    def reset(self):
        self._highlighted.clear()
        self._anchor.clear()
        self.update()

    def _key_color(self, key_lower: str) -> QColor:
        finger = FINGER_MAP.get(key_lower)
        if finger:
            base = FINGER_COLORS[finger]
            dark = base.darker(160)
            return dark
        return self._theme["key_bg"]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        unit = min(w / 15.0, h / 5.5)
        key_h = unit * 0.9
        margin = unit * 0.06
        start_y = (h - (key_h + margin) * 5) / 2.0

        row_offsets = [0.0, 0.5, 0.75, 1.25, 1.5]

        for row_idx, row in enumerate(ROWS):
            x = (w - self._row_width(row, unit)) / 2.0 + row_offsets[row_idx] * unit
            y = start_y + row_idx * (key_h + margin)

            for key in row:
                key_w = WIDE_KEYS.get(key, 1.0) * unit - margin
                key_lower = key.lower() if len(key) == 1 else key

                is_highlighted = key_lower in self._highlighted
                is_anchor = key_lower in self._anchor

                rect = QRectF(x, y, key_w, key_h)

                if is_highlighted:
                    bg = self._theme["highlight_bg"]
                    text_color = self._theme["highlight_text"]
                elif is_anchor:
                    bg = self._theme["anchor_bg"]
                    text_color = QColor("#ffffff")
                else:
                    bg = self._key_color(key_lower)
                    text_color = self._theme["key_text"]

                path = QPainterPath()
                path.addRoundedRect(rect, 4, 4)
                painter.setBrush(QBrush(bg))
                painter.setPen(QPen(self._theme["key_border"], 1))
                painter.drawPath(path)

                if is_highlighted:
                    glow = QColor(255, 255, 255, 60)
                    painter.setBrush(QBrush(glow))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawPath(path)

                font = QFont("Segoe UI", max(6, int(unit * 0.28)))
                painter.setFont(font)
                painter.setPen(QPen(text_color))
                display = key if key in ("⌫","⇥","⇪","↵","⇧","ctrl","alt") else key
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, display)

                x += WIDE_KEYS.get(key, 1.0) * unit

    def _row_width(self, row: list[str], unit: float) -> float:
        return sum(WIDE_KEYS.get(k, 1.0) * unit for k in row)
