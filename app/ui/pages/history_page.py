from __future__ import annotations
import csv
from datetime import datetime, timedelta
from pathlib import Path

import pyqtgraph as pg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QComboBox, QSplitter, QScrollArea,
                               QFrame, QFileDialog, QSizePolicy, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from app.database import Database, TestResult
from app.config import EXPORTS_DIR


class StatSummaryCard(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(120)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)

        self._value = QLabel("—")
        self._value.setFont(QFont("JetBrains Mono", 20, QFont.Weight.Bold))
        self._value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value.setStyleSheet("color: #e0e0e0;")

        self._label = QLabel(label)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("color: #666688; font-size: 11px;")

        lay.addWidget(self._value)
        lay.addWidget(self._label)
        self.setStyleSheet("background: #1e1e32; border-radius: 8px;")

    def set_value(self, v: str):
        self._value.setText(v)


class HistoryPage(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._all_results: list[TestResult] = []
        self._filtered: list[TestResult] = []
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        # Title + filter bar
        top = QHBoxLayout()
        title = QLabel("History")
        title.setObjectName("title_label")
        top.addWidget(title)
        top.addStretch()

        self._mode_filter = QComboBox()
        self._mode_filter.addItems(["All", "Words", "Time", "Quote", "Code"])
        self._mode_filter.currentTextChanged.connect(self._apply_filter)
        top.addWidget(self._mode_filter)

        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self._export_csv)
        top.addWidget(export_btn)

        root.addLayout(top)

        # Summary cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(8)
        self._cards: dict[str, StatSummaryCard] = {}
        for lbl in ("Best WPM", "Avg WPM (10)", "Tests Taken", "Time Practiced", "Streak", "Accuracy Trend"):
            card = StatSummaryCard(lbl)
            self._cards[lbl] = card
            cards_row.addWidget(card)
        root.addLayout(cards_row)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # Charts
        charts_widget = QWidget()
        charts_layout = QHBoxLayout(charts_widget)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        charts_layout.setSpacing(8)

        self._wpm_chart = pg.PlotWidget(title="WPM over time")
        self._wpm_chart.setBackground("#1a1a2e")
        self._wpm_chart.showGrid(x=False, y=True, alpha=0.15)
        self._wpm_chart.setMinimumHeight(160)
        charts_layout.addWidget(self._wpm_chart)

        self._acc_chart = pg.PlotWidget(title="Accuracy over time")
        self._acc_chart.setBackground("#1a1a2e")
        self._acc_chart.showGrid(x=False, y=True, alpha=0.15)
        self._acc_chart.setMinimumHeight(160)
        charts_layout.addWidget(self._acc_chart)

        splitter.addWidget(charts_widget)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["Date", "Mode", "WPM", "Raw WPM", "Accuracy", "Consistency", "Duration"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("""
            QTableWidget { alternate-background-color: #1e1e32; background: #1a1a2e; }
        """)
        self._table.setMinimumHeight(200)
        splitter.addWidget(self._table)

        root.addWidget(splitter, 1)

    def refresh(self):
        self._all_results = self._db.get_test_history(limit=500)
        self._apply_filter()
        self._update_stats()

    def _apply_filter(self):
        mode_text = self._mode_filter.currentText().lower()
        if mode_text == "all":
            self._filtered = list(self._all_results)
        else:
            self._filtered = [r for r in self._all_results if r.mode.startswith(mode_text)]
        self._update_table()
        self._update_charts()

    def _update_stats(self):
        results = self._all_results
        if not results:
            return

        best_wpm = max((r.wpm for r in results), default=0)
        self._cards["Best WPM"].set_value(f"{best_wpm:.0f}")

        last10 = results[:10]
        avg_wpm = sum(r.wpm for r in last10) / len(last10) if last10 else 0
        self._cards["Avg WPM (10)"].set_value(f"{avg_wpm:.0f}")

        self._cards["Tests Taken"].set_value(str(len(results)))

        total_secs = sum(r.elapsed_seconds for r in results)
        hours = int(total_secs // 3600)
        minutes = int((total_secs % 3600) // 60)
        self._cards["Time Practiced"].set_value(f"{hours}h {minutes}m")

        streak = self._calc_streak(results)
        self._cards["Streak"].set_value(f"{streak}d")

        if len(last10) >= 2:
            old_acc = sum(r.accuracy for r in last10[5:]) / len(last10[5:])
            new_acc = sum(r.accuracy for r in last10[:5]) / len(last10[:5])
            diff = new_acc - old_acc
            arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "→")
            self._cards["Accuracy Trend"].set_value(f"{arrow} {abs(diff):.1f}%")
        else:
            self._cards["Accuracy Trend"].set_value("—")

    def _calc_streak(self, results: list[TestResult]) -> int:
        if not results:
            return 0
        dates = sorted({datetime.fromisoformat(r.timestamp).date() for r in results}, reverse=True)
        if not dates:
            return 0
        today = datetime.now().date()
        streak = 0
        for i, d in enumerate(dates):
            expected = today - timedelta(days=i)
            if d == expected:
                streak += 1
            else:
                break
        return streak

    def _update_table(self):
        self._table.setRowCount(len(self._filtered))
        for row, result in enumerate(self._filtered):
            ts = datetime.fromisoformat(result.timestamp).strftime("%Y-%m-%d %H:%M")
            self._table.setItem(row, 0, QTableWidgetItem(ts))
            self._table.setItem(row, 1, QTableWidgetItem(result.mode))
            self._table.setItem(row, 2, QTableWidgetItem(f"{result.wpm:.0f}"))
            self._table.setItem(row, 3, QTableWidgetItem(f"{result.raw_wpm:.0f}"))
            self._table.setItem(row, 4, QTableWidgetItem(f"{result.accuracy:.0f}%"))
            self._table.setItem(row, 5, QTableWidgetItem(f"{result.consistency:.0f}%"))
            self._table.setItem(row, 6, QTableWidgetItem(f"{result.elapsed_seconds:.0f}s"))

    def _update_charts(self):
        results = list(reversed(self._filtered[:100]))
        x = list(range(len(results)))
        wpm_vals = [r.wpm for r in results]
        acc_vals = [r.accuracy for r in results]

        self._wpm_chart.clear()
        if wpm_vals:
            self._wpm_chart.plot(x, wpm_vals,
                pen=pg.mkPen(color="#e8c060", width=2),
                symbol="o", symbolSize=4, symbolBrush="#e8c060", symbolPen=None)
            if len(wpm_vals) > 3:
                import numpy as np
                coeff = np.polyfit(x, wpm_vals, 1)
                trend = np.polyval(coeff, x)
                self._wpm_chart.plot(x, trend.tolist(),
                    pen=pg.mkPen(color="#5588e8", width=1, style=pg.QtCore.Qt.PenStyle.DashLine))

        self._acc_chart.clear()
        if acc_vals:
            self._acc_chart.plot(x, acc_vals,
                pen=pg.mkPen(color="#55bb55", width=2),
                symbol="o", symbolSize=4, symbolBrush="#55bb55", symbolPen=None)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export History", str(EXPORTS_DIR / "history.csv"), "CSV Files (*.csv)"
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "mode", "wpm", "raw_wpm", "accuracy",
                             "consistency", "duration", "char_count", "error_count"])
            for r in self._all_results:
                writer.writerow([
                    r.timestamp, r.mode, r.wpm, r.raw_wpm, r.accuracy,
                    r.consistency, r.elapsed_seconds, r.char_count, r.error_count
                ])
