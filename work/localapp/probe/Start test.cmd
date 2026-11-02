@echo off
setlocal
title AJG Tracker test
cd /d "%~dp0"
echo Running the test. Please wait...
echo.
"%~dp0python\python.exe" -I -s "%~dp0app\probe.py"
if errorlevel 1 goto :failed
goto :end
:failed
echo.
echo ------------------------------------------------------------
echo Something went wrong or Windows blocked a step.
echo If you see this, copy this window's text to Claude.
echo (Click the window, press Ctrl+A, then Enter, then paste.)
echo ------------------------------------------------------------
:end
echo.
pause
