@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Run setup.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --name WhiteDragon --add-data "assets;assets" main.py
if errorlevel 1 goto fail
echo Build complete: dist\WhiteDragon\WhiteDragon.exe
pause
exit /b 0
:fail
echo Build failed. Check the errors above.
pause
exit /b 1
