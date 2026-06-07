from __future__ import annotations
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QPushButton, QLabel, QStackedWidget, QFrame,
                               QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QKeyEvent, QShortcut, QKeySequence

from app.database import Database
from app.core.text_generator import TextGenerator
from app.core.badge_checker import check_badges, BADGE_DEFS
from app.theme import apply_theme

from app.ui.pages.home_page import HomePage
from app.ui.pages.test_page import TestPage
from app.ui.pages.learn_page import LearnPage
from app.ui.pages.lesson_page import LessonPage
from app.ui.pages.history_page import HistoryPage
from app.ui.pages.profile_page import ProfilePage
from app.ui.pages.settings_page import SettingsPage


NAV_ITEMS = [
    ("home",    "Home",     "~"),
    ("test",    "Test",     ">"),
    ("learn",   "Learn",    "#"),
    ("history", "History",  "%"),
    ("profile", "Profile",  "@"),
    ("settings","Settings", "="),
]


class Toast(QWidget):
    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)

        lbl = QLabel(message)
        lbl.setStyleSheet(
            "color: #e0e0e0; font-size: 13px; background: transparent;"
        )
        lay.addWidget(lbl)

        self.setStyleSheet("""
            QWidget {
                background: #252540;
                border-radius: 8px;
                border: 1px solid #3a3a5a;
            }
        """)
        self.adjustSize()

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self.close)
        self._dismiss_timer.start(3000)


class ToastManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._toasts: list[Toast] = []

    def show_toast(self, message: str):
        toast = Toast(message, parent=self.parent())
        self._toasts.append(toast)
        self._reposition()
        toast.show()
        toast.destroyed.connect(lambda: self._on_toast_destroyed(toast))

    def _on_toast_destroyed(self, toast: Toast):
        if toast in self._toasts:
            self._toasts.remove(toast)
        self._reposition()

    def _reposition(self):
        if not self.parent():
            return
        pw = self.parent()
        margin = 16
        y = pw.height() - margin
        for toast in reversed(self._toasts):
            if toast.isVisible():
                y -= toast.height() + 8
                x = pw.width() - toast.width() - margin
                toast.move(x, y)


class NavButton(QPushButton):
    def __init__(self, page_id: str, label: str, icon: str, parent=None):
        super().__init__(parent)
        self.page_id = page_id
        self._label = label
        self._icon = icon
        self._collapsed = False
        self.setObjectName("nav_button")
        self.setCheckable(True)
        self.setFixedHeight(44)
        self._update_text()

    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        self._update_text()

    def _update_text(self):
        if self._collapsed:
            self.setText(self._icon)
            self.setToolTip(self._label)
        else:
            self.setText(f"  {self._icon}  {self._label}")
            self.setToolTip("")


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self._db = db
        self._text_gen = TextGenerator()
        self._sidebar_collapsed = False

        self._restore_geometry()
        self.setWindowTitle("TypeForge")
        self.setMinimumSize(900, 600)

        self._setup_ui()
        self._setup_shortcuts()

        theme = self._db.get_setting("theme") or "dark"
        apply_theme(QApplication.instance(), theme)

        self._navigate("test")

    def _restore_geometry(self):
        try:
            w = int(self._db.get_setting("window_width") or 1200)
            h = int(self._db.get_setting("window_height") or 750)
            x = int(self._db.get_setting("window_x") or -1)
            y = int(self._db.get_setting("window_y") or -1)
            self.resize(w, h)
            if x >= 0 and y >= 0:
                self.move(x, y)
        except Exception:
            self.resize(1200, 750)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        self._sidebar = QWidget()
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setFixedWidth(200)
        self._sidebar.setMinimumWidth(200)
        sidebar_lay = QVBoxLayout(self._sidebar)
        sidebar_lay.setContentsMargins(8, 16, 8, 8)
        sidebar_lay.setSpacing(2)

        logo = QLabel("TypeForge")
        logo.setFont(QFont("JetBrains Mono", 14, QFont.Weight.Bold))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("color: #4d9de0; padding: 8px 0 16px 0; letter-spacing: -0.5px;")
        sidebar_lay.addWidget(logo)

        self._nav_buttons: dict[str, NavButton] = {}
        for page_id, label, icon in NAV_ITEMS:
            btn = NavButton(page_id, label, icon)
            btn.clicked.connect(lambda checked, pid=page_id: self._navigate(pid))
            self._nav_buttons[page_id] = btn
            sidebar_lay.addWidget(btn)

        sidebar_lay.addStretch()

        self._collapse_btn = QPushButton("◀")
        self._collapse_btn.setFixedHeight(32)
        self._collapse_btn.setStyleSheet(
            "background: transparent; border: none; color: #4a4a6a; font-size: 12px;"
        )
        self._collapse_btn.clicked.connect(self._toggle_sidebar)
        sidebar_lay.addWidget(self._collapse_btn)

        main_layout.addWidget(self._sidebar)

        # ── Page area ─────────────────────────────────────────────────────────
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(0)

        self._page_stack = QStackedWidget()
        right_col.addWidget(self._page_stack)

        right_widget = QWidget()
        right_widget.setLayout(right_col)
        main_layout.addWidget(right_widget, 1)

        # ── Pages ─────────────────────────────────────────────────────────────
        self._home_page = HomePage()
        self._home_page.navigate.connect(self._navigate)
        self._page_stack.addWidget(self._home_page)

        self._test_page = TestPage(self._db, self._text_gen)
        self._test_page.test_finished.connect(self._on_test_finished)
        self._page_stack.addWidget(self._test_page)

        self._learn_page = LearnPage(self._db)
        self._learn_page.lesson_selected.connect(self._open_lesson)
        self._page_stack.addWidget(self._learn_page)

        self._lesson_page = LessonPage(self._db)
        self._lesson_page.back_requested.connect(lambda: self._navigate("learn"))
        self._lesson_page.lesson_complete.connect(self._on_lesson_complete)
        self._page_stack.addWidget(self._lesson_page)

        self._history_page = HistoryPage(self._db)
        self._page_stack.addWidget(self._history_page)

        self._profile_page = ProfilePage(self._db)
        self._page_stack.addWidget(self._profile_page)

        self._settings_page = SettingsPage(self._db)
        self._settings_page.theme_changed.connect(self._on_theme_changed)
        self._settings_page.settings_changed.connect(self._on_settings_changed)
        self._page_stack.addWidget(self._settings_page)

        self._page_map = {
            "home":     self._home_page,
            "test":     self._test_page,
            "learn":    self._learn_page,
            "lesson":   self._lesson_page,
            "history":  self._history_page,
            "profile":  self._profile_page,
            "settings": self._settings_page,
        }

        # ── Toast manager ─────────────────────────────────────────────────────
        self._toast_manager = ToastManager(self)

    def _setup_shortcuts(self):
        pages = ["home", "test", "learn", "history", "profile", "settings"]
        for i, page_id in enumerate(pages, start=1):
            sc = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            sc.activated.connect(lambda pid=page_id: self._navigate(pid))

    def _navigate(self, page_id: str):
        page = self._page_map.get(page_id)
        if not page:
            return

        self._page_stack.setCurrentWidget(page)

        for pid, btn in self._nav_buttons.items():
            btn.setChecked(pid == page_id or (page_id == "lesson" and pid == "learn"))

        if page_id == "history":
            self._history_page.refresh()
        elif page_id == "profile":
            self._profile_page.refresh()
        elif page_id == "learn":
            self._learn_page.refresh()

    def _open_lesson(self, lesson: dict):
        self._lesson_page.load_lesson(lesson)
        self._navigate("lesson")

    def _on_lesson_complete(self, lesson_id: str):
        self._learn_page.refresh()

    def _on_test_finished(self, result):
        history = self._db.get_test_history(limit=200)
        new_badges = check_badges(result, history, self._db)
        for badge_id in new_badges:
            info = BADGE_DEFS.get(badge_id, {})
            self._toast_manager.show_toast(
                f"Badge earned: {info.get('title', badge_id)}"
            )

    def _on_theme_changed(self, theme: str):
        apply_theme(QApplication.instance(), theme)

    def _on_settings_changed(self, settings: dict):
        self._test_page.apply_settings(settings)

    def _toggle_sidebar(self):
        self._sidebar_collapsed = not self._sidebar_collapsed
        new_width = 60 if self._sidebar_collapsed else 200
        self._sidebar.setFixedWidth(new_width)
        for btn in self._nav_buttons.values():
            btn.set_collapsed(self._sidebar_collapsed)
        self._collapse_btn.setText("▶" if self._sidebar_collapsed else "◀")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._toast_manager.resize(self.size())

    def closeEvent(self, event):
        self._db.set_setting("window_width", str(self.width()))
        self._db.set_setting("window_height", str(self.height()))
        self._db.set_setting("window_x", str(self.x()))
        self._db.set_setting("window_y", str(self.y()))
        self._db.close()
        super().closeEvent(event)
