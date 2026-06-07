from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QToolTip
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (QPainter, QColor, QPen, QBrush, QFont,
                          QFontMetrics, QPainterPath)

ROWS = [
    ["`","1","2","3","4","5","6","7","8","9","0","-","=","⌫"],
    ["⇥","q","w","e","r","t","y","u","i","o","p","[","]","\\"],
    ["⇪","a","s","d","f","g","h","j","k","l",";","'","↵"],
    ["⇧","z","x","c","v","b","n","m",",",".","/","⇧"],
    ["ctrl","alt","⎵","alt","ctrl"],
]
WIDE_KEYS = {"⌫": 2.0, "⇥": 1.5, "⇪": 1.75, "↵": 2.25,
             "⇧": 2.25, "ctrl": 1.5, "alt": 1.25, "⎵": 6.25}

ROW_OFFSETS = [0.0, 0.5, 0.75, 1.25, 1.5]


def _heat_color(count: int, max_count: int) -> QColor:
    if max_count == 0 or count == 0:
        return QColor("#2a5a2a")
    ratio = min(count / max_count, 1.0)
    r = int(40 + ratio * 200)
    g = int(90 - ratio * 60)
    b = int(40)
    return QColor(r, g, b)


class KeyHeatmap(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._error_map: dict[str, int] = {}
        self._max_errors = 0
        self._key_rects: list[tuple[str, QRectF]] = []
        self.setMouseTracking(True)
        self.setMinimumHeight(130)

    def set_error_map(self, error_map: dict[str, int]):
        self._error_map = error_map
        self._max_errors = max(error_map.values()) if error_map else 0
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.position() if hasattr(event, "position") else QPointF(event.x(), event.y())
        for key, rect in self._key_rects:
            if rect.contains(pos):
                count = self._error_map.get(key.lower(), 0)
                if count > 0:
                    QToolTip.showText(
                        event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos(),
                        f"{count} error{'s' if count != 1 else ''} on '{key}'"
                    )
                else:
                    QToolTip.hideText()
                return
        QToolTip.hideText()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        unit = min(w / 15.0, h / 5.5)
        key_h = unit * 0.9
        margin = unit * 0.06
        start_y = (h - (key_h + margin) * 5) / 2.0
        font = QFont("Segoe UI", max(5, int(unit * 0.25)))
        painter.setFont(font)
        fm = QFontMetrics(font)

        self._key_rects = []

        for row_idx, row in enumerate(ROWS):
            row_w = sum(WIDE_KEYS.get(k, 1.0) * unit for k in row)
            x = (w - row_w) / 2.0 + ROW_OFFSETS[row_idx] * unit
            y = start_y + row_idx * (key_h + margin)

            for key in row:
                key_w = WIDE_KEYS.get(key, 1.0) * unit - margin
                key_lower = key.lower() if len(key) == 1 else key
                count = self._error_map.get(key_lower, 0)
                bg = _heat_color(count, self._max_errors)

                rect = QRectF(x, y, key_w, key_h)
                self._key_rects.append((key_lower, rect))

                path = QPainterPath()
                path.addRoundedRect(rect, 4, 4)
                painter.setBrush(QBrush(bg))
                painter.setPen(QPen(QColor("#1a1a2e"), 1))
                painter.drawPath(path)

                text_color = QColor("#cccccc") if count == 0 else QColor("#ffffff")
                painter.setPen(QPen(text_color))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, key)

                x += WIDE_KEYS.get(key, 1.0) * unit
