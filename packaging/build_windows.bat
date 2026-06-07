@echo off
cd /d "%~dp0\.."

set ICON_FLAG=
if exist "assets\icons\typeforge.ico" (
  set ICON_FLAG=--icon assets\icons\typeforge.ico
)

pyinstaller ^
  --windowed ^
  --name TypeForge ^
  %ICON_FLAG% ^
  --add-data "app\data;app\data" ^
  --add-data "assets;assets" ^
  --hidden-import PyQt6.QtSvg ^
  --hidden-import PyQt6.QtSvgWidgets ^
  --hidden-import pyqtgraph ^
  --hidden-import numpy ^
  --noconfirm ^
  main.py

echo Build complete: dist\TypeForge.exe
