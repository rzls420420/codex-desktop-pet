@echo off
cd /d "%~dp0"
if exist "dist\WhiteDragon\WhiteDragon.exe" (
  start "" "dist\WhiteDragon\WhiteDragon.exe" --pet
) else if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" "%~dp0main.py" --pet
) else (
  echo Run setup.bat first.
  pause
)
