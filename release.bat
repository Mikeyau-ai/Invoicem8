@echo off
setlocal
cd /d "%~dp0"

echo.
echo  Building + publishing InvoiceM8 release...
echo.

if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

python -m pip install -q --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean InvoiceM8.spec
if errorlevel 1 (
  echo  BUILD FAILED - not releasing.
  pause
  exit /b 1
)

python release.py %*
pause
