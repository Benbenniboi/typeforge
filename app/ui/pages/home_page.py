from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from app.config import APP_NAME, VERSION


class HomePage(QWidget):
    navigate = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(60, 60, 60, 60)
        root.setSpacing(24)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(APP_NAME)
        title.setFont(QFont("JetBrains Mono", 42, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #e94560;")
        root.addWidget(title)

        subtitle = QLabel("The free, offline typing trainer")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666688; font-size: 16px;")
        root.addWidget(subtitle)

        root.addSpacing(24)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for label, desc, nav in (
            ("Speed Test", "Test your typing speed\nwith real-time feedback", "test"),
            ("Learn", "Structured lessons from\nhome row to symbols", "learn"),
            ("History", "View your progress and\nall past results", "history"),
        ):
            card = self._make_mode_card(label, desc, nav)
            cards_row.addWidget(card)

        root.addLayout(cards_row)

        root.addSpacing(16)

        version_lbl = QLabel(f"v{VERSION} — No ads. No telemetry. No accounts.")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_lbl.setStyleSheet("color: #2a2a4a; font-size: 11px;")
        root.addWidget(version_lbl)

    def _make_mode_card(self, label: str, desc: str, nav: str) -> QWidget:
        card = QPushButton()
        card.setFixedSize(200, 160)
        card.setStyleSheet("""
            QPushButton {
                background: #1e1e32;
                border: 1px solid #2a2a4a;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
            }
            QPushButton:hover {
                background: #252540;
                border-color: #4d9de0;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_lbl = QLabel(label)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("color: #c8d6e8; font-size: 15px; font-weight: bold; background: transparent; font-family: 'JetBrains Mono', monospace;")
        card_layout.addWidget(name_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #363650; font-size: 11px; background: transparent; font-family: 'JetBrains Mono', monospace;")
        card_layout.addWidget(desc_lbl)

        card.clicked.connect(lambda: self.navigate.emit(nav))
        return card
