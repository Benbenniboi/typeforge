from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from app.core.lesson_runner import load_curriculum, is_lesson_unlocked
from app.ui.widgets.progress_bar import StarRating
from app.database import Database


class LessonEntry(QWidget):
    clicked = pyqtSignal(dict)

    def __init__(self, lesson: dict, stars: int, locked: bool, parent=None):
        super().__init__(parent)
        self._lesson = lesson
        self._locked = locked
        self.setCursor(Qt.CursorShape.PointingHandCursor if not locked else Qt.CursorShape.ForbiddenCursor)
        self.setFixedHeight(64)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 8, 16, 8)
        lay.setSpacing(12)

        num = QLabel(lesson["id"].replace("lesson_", ""))
        num.setFixedWidth(30)
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num.setStyleSheet(f"color: {'#4a4a6a' if locked else '#888899'}; font-size: 12px;")
        lay.addWidget(num)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        title = QLabel(lesson["title"])
        title.setStyleSheet(f"color: {'#444458' if locked else '#e0e0e0'}; font-size: 13px; font-weight: bold;")
        desc = QLabel(lesson["description"])
        desc.setStyleSheet("color: #555570; font-size: 11px;")
        info_col.addWidget(title)
        info_col.addWidget(desc)
        lay.addLayout(info_col)
        lay.addStretch()

        if locked:
            lock = QLabel("[locked]")
            lock.setStyleSheet("font-size: 10px; color: #2e2e42; font-family: 'JetBrains Mono', monospace;")
            lay.addWidget(lock)
        else:
            star_widget = StarRating(stars, 3)
            star_widget.setFixedWidth(70)
            lay.addWidget(star_widget)

        self._update_style()

    def _update_style(self):
        if self._locked:
            self.setStyleSheet("""
                LessonEntry { background: #141422; border-radius: 6px; }
                LessonEntry:hover { background: #141422; }
            """)
        else:
            self.setStyleSheet("""
                LessonEntry { background: #1e1e32; border-radius: 6px; }
                LessonEntry:hover { background: #252540; }
            """)

    def mousePressEvent(self, event):
        if not self._locked:
            self.clicked.emit(self._lesson)


class LearnPage(QWidget):
    lesson_selected = pyqtSignal(dict)

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left panel
        left = QWidget()
        left.setFixedWidth(260)
        left.setObjectName("sidebar")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(16, 16, 16, 16)
        left_lay.setSpacing(8)

        title = QLabel("Learn to Type")
        title.setObjectName("title_label")
        left_lay.addWidget(title)

        self._stats_label = QLabel("")
        self._stats_label.setStyleSheet("color: #666688; font-size: 12px;")
        self._stats_label.setWordWrap(True)
        left_lay.addWidget(self._stats_label)

        left_lay.addStretch()

        root.addWidget(left)

        # Right — scrollable lesson list
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(24, 16, 24, 16)
        right_lay.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._lesson_container = QWidget()
        self._lesson_layout = QVBoxLayout(self._lesson_container)
        self._lesson_layout.setContentsMargins(0, 0, 8, 0)
        self._lesson_layout.setSpacing(4)
        self._lesson_layout.addStretch()

        scroll.setWidget(self._lesson_container)
        right_lay.addWidget(scroll)

        root.addWidget(right, 1)

    def refresh(self):
        curriculum = load_curriculum()
        progress = self._db.get_lesson_progress()

        # Clear existing entries
        while self._lesson_layout.count() > 1:
            item = self._lesson_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        categories = {}
        for lesson in curriculum:
            cat = lesson.get("category", "beginner")
            categories.setdefault(cat, []).append(lesson)

        completed = sum(1 for p in progress.values() if p.get("completed"))
        total = len(curriculum)
        self._stats_label.setText(
            f"{completed}/{total} lessons completed\n"
            f"Keep practicing every day!"
        )

        for cat in ("beginner", "intermediate", "advanced"):
            lessons = categories.get(cat, [])
            if not lessons:
                continue

            cat_label = QLabel(cat.capitalize())
            cat_label.setStyleSheet(
                "color: #666688; font-size: 11px; font-weight: bold; "
                "padding: 12px 0 4px 0; text-transform: uppercase; letter-spacing: 1px;"
            )
            self._lesson_layout.insertWidget(self._lesson_layout.count() - 1, cat_label)

            for lesson in lessons:
                lid = lesson["id"]
                p = progress.get(lid, {})
                stars = p.get("best_stars", 0)
                locked = not is_lesson_unlocked(lid, progress)

                entry = LessonEntry(lesson, stars, locked)
                entry.clicked.connect(self.lesson_selected)
                self._lesson_layout.insertWidget(self._lesson_layout.count() - 1, entry)
