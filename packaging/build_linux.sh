#!/bin/bash
set -e
cd "$(dirname "$0")/.."

pyinstaller \
  --onedir \
  --name TypeForge \
  --add-data "app/data:app/data" \
  --add-data "assets:assets" \
  --hidden-import PyQt6.QtSvg \
  --hidden-import PyQt6.QtSvgWidgets \
  --hidden-import pyqtgraph \
  --hidden-import numpy \
  --noconfirm \
  main.py

echo "Build complete: dist/TypeForge/"
