import sys
import os

# Ensure the typeforge directory is on sys.path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import Qt

from app.database import Database
from app.ui.main_window import MainWindow
from app.config import FONTS_DIR


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TypeForge")
    app.setOrganizationName("TypeForge")

    # Load bundled fonts
    jetbrains_path = FONTS_DIR / "JetBrainsMono.ttf"
    if jetbrains_path.exists():
        QFontDatabase.addApplicationFont(str(jetbrains_path))

    db = Database()
    window = MainWindow(db)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
