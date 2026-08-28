@echo off
setlocal
cd /d "%~dp0"
title InvoiceM8 - tests

echo.
echo   ##### #   # #   #  ###  ##### #### ##### #   #  ###
echo     #   ##  # #   # #   #   #   #    #    ## ## #   #
echo     #   # # # #   # #   #   #   #    ###  # # #  ###
echo     #   #  ## #   # #   #   #   #    #    #   # #   #
echo   ##### #   #   #    ###  ##### #### ##### #   #  ###
echo   test suite   github.com/Mikeyau-ai/Invoicem8
echo.

python -m unittest discover -s tests -v
if errorlevel 1 (
  echo.
  echo  TESTS FAILED - do not release this build.
  pause
  exit /b 1
)

echo.
echo  All tests passed.
echo.
pause
