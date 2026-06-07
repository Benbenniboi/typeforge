from __future__ import annotations
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from app.ui.widgets.wpm_graph import WpmGraph
from app.ui.widgets.heatmap import KeyHeatmap
from app.core.engine import TestResult


class StatCard(QWidget):
    def __init__(self, label: str, value: str, sub: str = "", parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)

        self._val_label = QLabel(value)
        self._val_label.setFont(QFont("JetBrains Mono", 28, QFont.Weight.Bold))
        self._val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._val_label.setStyleSheet("color: #c8d6e8; font-family: 'JetBrains Mono', monospace;")

        self._lbl = QLabel(label)
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl.setStyleSheet("color: #2e2e42; font-size: 11px; letter-spacing: 1px; font-family: 'JetBrains Mono', monospace;")

        self._sub = QLabel(sub)
        self._sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub.setStyleSheet("color: #363650; font-size: 10px;")

        lay.addWidget(self._val_label)
        lay.addWidget(self._lbl)
        if sub:
            lay.addWidget(self._sub)

    def set_value(self, value: str):
        self._val_label.setText(value)

    def set_sub(self, sub: str):
        self._sub.setText(sub)
        self._sub.setVisible(bool(sub))


class ResultsPanel(QWidget):
    restart_requested = pyqtSignal()
    next_test_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: TestResult | None = None
        self._is_pb = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(16)

        self._pb_label = QLabel("New Personal Best!")
        self._pb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pb_label.setStyleSheet("color: #4d9de0; font-size: 14px; font-weight: bold; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px;")
        self._pb_label.setVisible(False)
        main_layout.addWidget(self._pb_label)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(0)
        self._wpm_card = StatCard("wpm", "0")
        self._wpm_card._val_label.setStyleSheet(
            "color: #4d9de0; font-family: 'JetBrains Mono', monospace; font-size: 40px;"
        )
        self._wpm_card._val_label.setFont(QFont("JetBrains Mono", 40, QFont.Weight.Bold))
        self._raw_card = StatCard("raw", "0")
        self._acc_card = StatCard("acc", "0%")
        self._con_card = StatCard("consistency", "0%")
        self._time_card = StatCard("time", "0s")
        self._chars_card = StatCard("chars", "0/0")
        for card in (self._wpm_card, self._raw_card, self._acc_card,
                     self._con_card, self._time_card, self._chars_card):
            stats_row.addWidget(card)
        main_layout.addLayout(stats_row)

        self._graph = WpmGraph()
        self._graph.setMinimumHeight(140)
        main_layout.addWidget(self._graph)

        heatmap_label = QLabel("error heatmap")
        heatmap_label.setStyleSheet("color: #1c1c28; font-size: 11px; font-family: 'JetBrains Mono', monospace; letter-spacing: 1px;")
        main_layout.addWidget(heatmap_label)

        self._heatmap = KeyHeatmap()
        self._heatmap.setMinimumHeight(120)
        main_layout.addWidget(self._heatmap)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._restart_btn = QPushButton("Restart (Tab)")
        self._restart_btn.setObjectName("accent_button")
        self._restart_btn.clicked.connect(self.restart_requested)
        self._next_btn = QPushButton("Next Test")
        self._next_btn.clicked.connect(self.next_test_requested)
        btn_row.addWidget(self._restart_btn)
        btn_row.addWidget(self._next_btn)
        btn_row.addStretch()
        main_layout.addLayout(btn_row)

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate_wpm)
        self._anim_target = 0.0
        self._anim_current = 0.0

    def show_result(self, result: TestResult, is_pb: bool = False, pb_wpm: float = 0):
        self._result = result
        self._is_pb = is_pb

        self._pb_label.setVisible(is_pb)

        self._raw_card.set_value(f"{result.raw_wpm:.0f}")
        self._acc_card.set_value(f"{result.accuracy:.0f}%")
        self._con_card.set_value(f"{result.consistency:.0f}%")
        self._time_card.set_value(f"{result.elapsed_seconds:.0f}s")
        self._chars_card.set_value(
            f"{result.char_count}/{result.char_count + result.error_count}"
        )

        self._graph.reset()
        self._graph.load_result_data(result.wpm_snapshots, pb_wpm)
        self._heatmap.set_error_map(result.error_map)

        self._anim_current = 0.0
        self._anim_target = result.wpm
        self._anim_timer.start(16)

    def _animate_wpm(self):
        self._anim_current = min(self._anim_current + self._anim_target / 40, self._anim_target)
        self._wpm_card.set_value(f"{self._anim_current:.0f}")
        if self._anim_current >= self._anim_target:
            self._anim_timer.stop()
