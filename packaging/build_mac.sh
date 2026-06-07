#!/bin/bash
set -e
cd "$(dirname "$0")/.."

ICON_FLAG=""
if [ -f "assets/icons/typeforge.icns" ]; then
  ICON_FLAG="--icon assets/icons/typeforge.icns"
fi

pyinstaller \
  --windowed \
  --name TypeForge \
  $ICON_FLAG \
  --add-data "app/data:app/data" \
  --add-data "assets:assets" \
  --hidden-import PyQt6.QtSvg \
  --hidden-import PyQt6.QtSvgWidgets \
  --hidden-import pyqtgraph \
  --hidden-import numpy \
  --noconfirm \
  main.py

echo "Build complete: dist/TypeForge.app"
