from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QDialog, QDialogButtonBox,
                               QSizePolicy, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent

from app.core.lesson_runner import LessonRunner, get_lesson_by_id
from app.ui.widgets.typing_area import TypingArea
from app.ui.widgets.virtual_keyboard import VirtualKeyboard
from app.ui.widgets.progress_bar import LessonProgressBar, StarRating
from app.database import Database


class LessonCompleteDialog(QDialog):
    def __init__(self, passed: bool, stars: int, wpm: float, accuracy: float,
                 min_wpm: float, min_acc: float, next_lesson_id: str | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lesson Complete")
        self.setModal(True)
        self.setMinimumWidth(320)

        lay = QVBoxLayout(self)
        lay.setSpacing(16)

        if passed:
            header = QLabel("Well done!")
            header.setStyleSheet("font-size: 22px; font-weight: bold; color: #a8d8a8;")
        else:
            header = QLabel("Keep practicing!")
            header.setStyleSheet("font-size: 22px; font-weight: bold; color: #e8c060;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(header)

        stars_w = StarRating(stars, 3)
        stars_w.setFixedHeight(32)
        lay.addWidget(stars_w)

        stats = QLabel(
            f"WPM: {wpm:.0f}  •  Accuracy: {accuracy:.0f}%\n"
            f"Required: {min_wpm} WPM  •  {min_acc}% accuracy"
        )
        stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats.setStyleSheet("color: #888899; font-size: 13px;")
        lay.addWidget(stats)

        if not passed:
            msg = QLabel(
                f"You need {min_wpm} WPM and {min_acc}% accuracy to pass.\n"
                "You can do it — try again!"
            )
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setStyleSheet("color: #666688; font-size: 12px;")
            lay.addWidget(msg)

        btns = QDialogButtonBox()
        if passed and next_lesson_id:
            self._next_btn = btns.addButton("Next Lesson", QDialogButtonBox.ButtonRole.AcceptRole)
        retry_btn = btns.addButton("Try Again", QDialogButtonBox.ButtonRole.RejectRole)
        lay.addWidget(btns)

        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)


class LessonPage(QWidget):
    back_requested = pyqtSignal()
    lesson_complete = pyqtSignal(str)

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._runner: LessonRunner | None = None
        self._lesson: dict | None = None
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 16, 32, 16)
        root.setSpacing(12)

        # Top bar
        top_bar = QHBoxLayout()
        self._back_btn = QPushButton("← Back")
        self._back_btn.setStyleSheet(
            "background: transparent; border: none; color: #666688; font-size: 13px;"
        )
        self._back_btn.clicked.connect(self.back_requested)
        top_bar.addWidget(self._back_btn)
        top_bar.addStretch()

        self._title_label = QLabel("")
        self._title_label.setObjectName("title_label")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(self._title_label)
        top_bar.addStretch()

        self._req_label = QLabel("")
        self._req_label.setStyleSheet("color: #666688; font-size: 12px;")
        self._req_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        top_bar.addWidget(self._req_label)

        root.addLayout(top_bar)

        # Virtual keyboard
        self._keyboard = VirtualKeyboard()
        self._keyboard.setMinimumHeight(130)
        self._keyboard.setMaximumHeight(150)
        root.addWidget(self._keyboard)

        # Typing area
        self._typing_area = TypingArea()
        self._typing_area.set_mode("lesson")
        self._typing_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        root.addWidget(self._typing_area, 1)

        # Bottom bar: progress + live stats
        bottom_bar = QHBoxLayout()
        self._progress_bar = LessonProgressBar()
        bottom_bar.addWidget(self._progress_bar)

        self._wpm_label = QLabel("0 WPM")
        self._wpm_label.setStyleSheet("color: #888899; font-size: 13px; min-width: 70px;")
        self._acc_label = QLabel("100%")
        self._acc_label.setStyleSheet("color: #888899; font-size: 13px; min-width: 55px;")
        bottom_bar.addWidget(self._wpm_label)
        bottom_bar.addWidget(self._acc_label)

        root.addLayout(bottom_bar)

        self._typing_area.key_pressed.connect(self._on_key_pressed)
        self._typing_area.test_complete.connect(self._on_lesson_complete)
        self._typing_area.wpm_updated.connect(self._on_wpm_updated)

    def load_lesson(self, lesson: dict):
        self._lesson = lesson
        self._runner = LessonRunner(lesson)

        self._title_label.setText(lesson["title"])
        self._req_label.setText(
            f"Pass: {lesson['min_wpm_to_pass']} WPM  •  {lesson['min_accuracy_to_pass']}% acc"
        )

        anchor_keys = lesson.get("anchor_keys", ["f", "j"])
        self._keyboard.highlight_anchor(anchor_keys)

        self._typing_area.load_text(lesson["content"], mode="lesson", duration=0)
        self._update_next_key()

    def _update_next_key(self):
        if not self._runner:
            return
        next_char = self._runner.next_expected_char()
        if next_char and next_char != " ":
            self._keyboard.highlight_key(next_char)
        elif next_char == " ":
            self._keyboard.highlight_key(" ")
        else:
            self._keyboard.reset()

        # Re-highlight anchors
        if self._lesson:
            self._keyboard.highlight_anchor(self._lesson.get("anchor_keys", ["f", "j"]))

    def _on_key_pressed(self, char: str, correct: bool):
        if not self._runner:
            return
        self._update_next_key()

        # Update progress bar
        pos = self._typing_area.get_engine().current_position if self._typing_area.get_engine() else 0
        total = len(self._runner.target)
        self._progress_bar.set_progress(pos / total if total > 0 else 0)

    def _on_wpm_updated(self, wpm: float, raw_wpm: float):
        if self._typing_area.get_engine():
            e = self._typing_area.get_engine()
            self._wpm_label.setText(f"{e.wpm:.0f} WPM")
            self._acc_label.setText(f"{e.accuracy:.0f}%")

    def _on_lesson_complete(self, result):
        if not self._lesson or not self._runner:
            return

        passed, stars, wpm, accuracy = self._runner.check_pass()
        self._db.save_lesson_progress(
            self._lesson["id"], wpm, accuracy, stars, passed
        )

        next_id = self._lesson.get("next_lesson")
        dialog = LessonCompleteDialog(
            passed, stars, wpm, accuracy,
            self._lesson["min_wpm_to_pass"],
            self._lesson["min_accuracy_to_pass"],
            next_id,
            parent=self
        )
        result_code = dialog.exec()

        if result_code == QDialog.DialogCode.Accepted and next_id:
            next_lesson = get_lesson_by_id(next_id)
            if next_lesson:
                self.load_lesson(next_lesson)
                self.lesson_complete.emit(self._lesson["id"])
        else:
            self.load_lesson(self._lesson)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.back_requested.emit()
        else:
            super().keyPressEvent(event)
