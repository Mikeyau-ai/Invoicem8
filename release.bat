@echo off
setlocal
cd /d "%~dp0"
title InvoiceM8 - release

echo.
echo   ##### #   # #   #  ###  ##### #### ##### #   #  ###
echo     #   ##  # #   # #   #   #   #    #    ## ## #   #
echo     #   # # # #   # #   #   #   #    ###  # # #  ###
echo     #   #  ## #   # #   #   #   #    #    #   # #   #
echo   ##### #   #   #    ###  ##### #### ##### #   #  ###
echo   release script   github.com/Mikeyau-ai/Invoicem8
echo.

:: Thin wrapper: release.py is the one system - tests, PyInstaller build, then
:: (after a Y/N confirmation) publishes GitHub release v<APP_VERSION> with the
:: CHANGELOG notes. Pass --skip-build to publish the exe already in dist\,
:: or --yes to skip the confirmation.
python release.py %*
set RC=%errorlevel%
pause
exit /b %RC%
