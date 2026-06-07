from __future__ import annotations
from datetime import datetime

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QScrollArea, QFrame, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.database import Database
from app.core.badge_checker import BADGE_DEFS


class PBCard(QWidget):
    def __init__(self, mode: str, data: dict, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #1e1e32; border-radius: 8px;")
        self.setMinimumWidth(180)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(4)

        mode_lbl = QLabel(mode.replace("_", " "))
        mode_lbl.setStyleSheet("color: #666688; font-size: 11px; text-transform: uppercase;")
        lay.addWidget(mode_lbl)

        wpm_lbl = QLabel(f"{data['wpm']:.0f} WPM")
        wpm_lbl.setFont(QFont("JetBrains Mono", 22, QFont.Weight.Bold))
        wpm_lbl.setStyleSheet("color: #e94560;")
        lay.addWidget(wpm_lbl)

        acc_lbl = QLabel(f"{data.get('accuracy', 0):.0f}% accuracy")
        acc_lbl.setStyleSheet("color: #888899; font-size: 12px;")
        lay.addWidget(acc_lbl)

        ts = data.get("timestamp", "")
        if ts:
            date_str = datetime.fromisoformat(ts).strftime("%b %d, %Y")
            date_lbl = QLabel(date_str)
            date_lbl.setStyleSheet("color: #4a4a6a; font-size: 11px;")
            lay.addWidget(date_lbl)


class BadgeCard(QWidget):
    def __init__(self, badge_id: str, earned_at: str | None, parent=None):
        super().__init__(parent)
        info = BADGE_DEFS.get(badge_id, {})
        earned = earned_at is not None

        self.setFixedSize(120, 120)
        self.setStyleSheet(
            f"background: {'#1e1e32' if earned else '#131320'}; "
            f"border-radius: 8px; "
            f"border: 1px solid {'#2a2a4a' if earned else '#1a1a2a'};"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel(info.get("icon", "?"))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(
            f"font-size: 28px; {'opacity: 1;' if earned else 'color: #333344;'}"
        )
        if not earned:
            icon_lbl.setStyleSheet("font-size: 28px; color: #2a2a3a;")
        lay.addWidget(icon_lbl)

        title_lbl = QLabel(info.get("title", badge_id))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(
            f"color: {'#e0e0e0' if earned else '#333344'}; font-size: 10px; font-weight: bold;"
        )
        lay.addWidget(title_lbl)

        if earned and earned_at:
            date_str = datetime.fromisoformat(earned_at).strftime("%b %Y")
            date_lbl = QLabel(date_str)
            date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            date_lbl.setStyleSheet("color: #555570; font-size: 9px;")
            lay.addWidget(date_lbl)

        self.setToolTip(info.get("description", ""))


class ProfilePage(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(32, 24, 32, 24)
        content_lay.setSpacing(24)

        title = QLabel("Profile")
        title.setObjectName("title_label")
        content_lay.addWidget(title)

        # Personal Bests
        pb_title = QLabel("Personal Bests")
        pb_title.setStyleSheet("color: #888899; font-size: 14px; font-weight: bold;")
        content_lay.addWidget(pb_title)

        self._pb_container = QHBoxLayout()
        self._pb_container.setSpacing(8)
        self._pb_container.addStretch()
        content_lay.addLayout(self._pb_container)

        sep = QFrame()
        sep.setObjectName("divider")
        sep.setFixedHeight(1)
        content_lay.addWidget(sep)

        # Badges
        badges_title = QLabel("Achievements")
        badges_title.setStyleSheet("color: #888899; font-size: 14px; font-weight: bold;")
        content_lay.addWidget(badges_title)

        self._badges_grid = QGridLayout()
        self._badges_grid.setSpacing(8)
        content_lay.addLayout(self._badges_grid)

        content_lay.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    def refresh(self):
        pbs = self._db.get_personal_bests()
        earned_badges = {b["badge_id"]: b["earned_at"] for b in self._db.get_badges()}

        # Clear and repopulate PB cards
        while self._pb_container.count() > 1:
            item = self._pb_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for mode, data in sorted(pbs.items()):
            card = PBCard(mode, data)
            self._pb_container.insertWidget(self._pb_container.count() - 1, card)

        if not pbs:
            no_pb = QLabel("Complete some tests to see your personal bests!")
            no_pb.setStyleSheet("color: #4a4a6a; font-size: 13px;")
            self._pb_container.insertWidget(0, no_pb)

        # Clear and repopulate badge grid
        while self._badges_grid.count():
            item = self._badges_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = 6
        for i, (badge_id, _) in enumerate(BADGE_DEFS.items()):
            earned_at = earned_badges.get(badge_id)
            card = BadgeCard(badge_id, earned_at)
            self._badges_grid.addWidget(card, i // cols, i % cols)
