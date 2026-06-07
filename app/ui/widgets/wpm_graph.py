from __future__ import annotations
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtGui import QColor
import numpy as np


pg.setConfigOption("background", "#0b0b0f")
pg.setConfigOption("foreground", "#2e2e42")


class WpmGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setBackground("#0b0b0f")
        self._plot_widget.showGrid(x=False, y=True, alpha=0.08)
        self._plot_widget.getAxis("bottom").setTextPen(pg.mkPen(color="#2e2e42"))
        self._plot_widget.getAxis("left").setTextPen(pg.mkPen(color="#2e2e42"))
        self._plot_widget.getAxis("bottom").setPen(pg.mkPen(color="#13131e"))
        self._plot_widget.getAxis("left").setPen(pg.mkPen(color="#13131e"))
        self._plot_widget.setLabel("bottom", "Time (s)", color="#2e2e42", size="9pt")
        self._plot_widget.setLabel("left", "WPM", color="#2e2e42", size="9pt")
        self._plot_widget.setMinimumHeight(120)

        self._layout.addWidget(self._plot_widget)

        self._wpm_line = self._plot_widget.plot(
            [], [], pen=pg.mkPen(color="#4d9de0", width=2), name="WPM"
        )
        self._raw_line = self._plot_widget.plot(
            [], [], pen=pg.mkPen(color="#1e3a58", width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine), name="Raw"
        )
        self._error_scatter = pg.ScatterPlotItem(
            size=6, brush=pg.mkBrush("#c84b55"), pen=pg.mkPen(None)
        )
        self._plot_widget.addItem(self._error_scatter)

        self._pb_line: pg.InfiniteLine | None = None

        self._times: list[float] = []
        self._wpm_vals: list[float] = []
        self._raw_vals: list[float] = []
        self._error_times: list[float] = []
        self._error_wpms: list[float] = []

        self._interval = 0.5
        self._elapsed = 0.0

    def set_theme(self, bg: str, accent: str, muted: str):
        self._plot_widget.setBackground(bg)
        self._wpm_line.setPen(pg.mkPen(color=accent, width=2))
        self.update()

    def update_wpm(self, wpm: float, raw_wpm: float):
        self._elapsed += self._interval
        self._times.append(self._elapsed)
        self._wpm_vals.append(wpm)
        self._raw_vals.append(raw_wpm)
        self._wpm_line.setData(self._times, self._wpm_vals)
        self._raw_line.setData(self._times, self._raw_vals)

    def add_error_marker(self, elapsed: float, wpm: float):
        self._error_times.append(elapsed)
        self._error_wpms.append(wpm)
        self._error_scatter.setData(
            x=self._error_times, y=self._error_wpms
        )

    def load_result_data(self, wpm_snapshots: list[float], personal_best: float = 0):
        self._times = [i * self._interval for i in range(len(wpm_snapshots))]
        self._wpm_vals = wpm_snapshots
        self._wpm_line.setData(self._times, self._wpm_vals)
        self._raw_line.setData([], [])
        self._error_scatter.setData(x=[], y=[])

        if personal_best > 0:
            if self._pb_line:
                self._plot_widget.removeItem(self._pb_line)
            self._pb_line = pg.InfiniteLine(
                pos=personal_best, angle=0,
                pen=pg.mkPen(color="#5588e8", width=1, style=pg.QtCore.Qt.PenStyle.DashLine),
                label=f"PB: {personal_best:.0f}",
                labelOpts={"color": "#5588e8", "position": 0.9}
            )
            self._plot_widget.addItem(self._pb_line)

    def reset(self):
        self._times = []
        self._wpm_vals = []
        self._raw_vals = []
        self._error_times = []
        self._error_wpms = []
        self._elapsed = 0.0
        self._wpm_line.setData([], [])
        self._raw_line.setData([], [])
        self._error_scatter.setData(x=[], y=[])
        if self._pb_line:
            self._plot_widget.removeItem(self._pb_line)
            self._pb_line = None
