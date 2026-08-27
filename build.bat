@echo off
setlocal

echo.
echo  Building InvoiceM8...
echo.

:: Clean previous build
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

:: Invoked as "python -m PyInstaller", not the bare "pyinstaller" shim: this
:: machine has more than one Python on PATH and the shim can resolve to the
:: wrong interpreter, silently building against the wrong site-packages.
::
:: Build from a venv that has the full requirements.txt installed if you want
:: the AI / Graph / attachment features baked in (the spec skips any that are
:: missing).
python -m pip install -q --upgrade pyinstaller
if errorlevel 1 (
  echo  Could not install PyInstaller.
  pause
  exit /b 1
)

python -m PyInstaller --noconfirm --clean InvoiceM8.spec
if errorlevel 1 (
  echo.
  echo  BUILD FAILED.
  pause
  exit /b 1
)

echo.
echo  Built: dist\InvoiceM8.exe
echo  (settings + database still live in %%LOCALAPPDATA%%\InvoiceM8)
echo.
pause
