@echo off
setlocal
title AJG Tracker (keep this window open)
rem pushd also works when this folder is on a network drive (UNC path): Windows gives it a drive letter for now.
pushd "%~dp0"
if errorlevel 1 (
  echo This folder could not be opened. If it is on a network drive, open the drive in File Explorer first, then try again.
  goto :fail
)
if not exist "python\python.exe" (
  echo The tracker's Python is missing from this folder ^(python\python.exe^).
  echo The folder may not have been unzipped completely. Unzip it again, in full, then try again.
  goto :fail
)
python\python.exe -B -X utf8 -I app\station\launcher.py
if errorlevel 1 goto :fail
popd
exit /b 0

:fail
echo.
echo The tracker did not start. Nothing in your data was changed.
echo If this keeps happening, take a photo of this window and send it to Claude.
echo.
pause
popd
exit /b 1
