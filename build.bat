@echo off
setlocal
cd /d "%~dp0"
title InvoiceM8 - build

echo.
echo   ##### #   # #   #  ###  ##### #### ##### #   #  ###
echo     #   ##  # #   # #   #   #   #    #    ## ## #   #
echo     #   # # # #   # #   #   #   #    ###  # # #  ###
echo     #   #  ## #   # #   #   #   #    #    #   # #   #
echo   ##### #   #   #    ###  ##### #### ##### #   #  ###
echo   build script   github.com/Mikeyau-ai/Invoicem8
echo.

:: Thin wrapper: release.py is the one system (test -> build -> publish).
:: --build-only runs the tests and the PyInstaller build, then stops -
:: no GitHub CLI, no release. Use release.bat to also publish.
python release.py --build-only
set RC=%errorlevel%
pause
exit /b %RC%
