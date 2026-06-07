from __future__ import annotations
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath


class LessonProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._progress = 0.0
        self._stars = 0
        self._accent = QColor("#e94560")
        self._bg = QColor("#2a2a4a")
        self.setFixedHeight(8)

    def set_progress(self, fraction: float):
        self._progress = max(0.0, min(1.0, fraction))
        self.update()

    def set_stars(self, stars: int):
        self._stars = stars
        self.update()

    def set_accent(self, color: str):
        self._accent = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        bg_rect = QRectF(0, 0, w, h)
        path = QPainterPath()
        path.addRoundedRect(bg_rect, h / 2, h / 2)
        painter.setBrush(QBrush(self._bg))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)

        if self._progress > 0:
            fill_rect = QRectF(0, 0, w * self._progress, h)
            fill_path = QPainterPath()
            fill_path.addRoundedRect(fill_rect, h / 2, h / 2)
            painter.setBrush(QBrush(self._accent))
            painter.drawPath(fill_path)


class StarRating(QWidget):
    def __init__(self, stars: int = 0, max_stars: int = 3, parent=None):
        super().__init__(parent)
        self._stars = stars
        self._max = max_stars
        self._accent = QColor("#e8d735")
        self._empty = QColor("#3a3a5a")
        self.setFixedHeight(20)

    def set_stars(self, stars: int):
        self._stars = stars
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self.height()
        star_size = h - 2
        spacing = star_size + 4
        total_w = self._max * spacing
        x_start = (self.width() - total_w) // 2

        for i in range(self._max):
            cx = x_start + i * spacing + star_size // 2
            cy = h // 2
            color = self._accent if i < self._stars else self._empty
            self._draw_star(painter, cx, cy, star_size // 2, color)

    def _draw_star(self, painter: QPainter, cx: int, cy: int, r: int, color: QColor):
        import math
        path = QPainterPath()
        for i in range(5):
            angle = math.pi / 2 + i * 2 * math.pi / 5
            outer_x = cx + r * math.cos(angle)
            outer_y = cy - r * math.sin(angle)
            inner_angle = angle + math.pi / 5
            inner_x = cx + (r * 0.4) * math.cos(inner_angle)
            inner_y = cy - (r * 0.4) * math.sin(inner_angle)
            if i == 0:
                path.moveTo(outer_x, outer_y)
            else:
                path.lineTo(outer_x, outer_y)
            path.lineTo(inner_x, inner_y)
        path.closeSubpath()
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
