@echo off
setlocal
title Install a new version of the AJG Tracker
pushd "%~dp0"
if errorlevel 1 (
  echo This folder could not be opened. Open the drive in File Explorer first, then try again.
  goto :end
)
if not exist "python\python.exe" (
  echo The new version's Python is missing from this folder. Unzip the new zip again, in full.
  goto :end
)
echo This puts the NEW version of the tracker into the tracker folder you already use.
echo Your data (workbook, library, backups, notes) is not touched.
echo.
echo Close the tracker first (its black window). Then:
echo   Open File Explorer, find the folder you use now (the one with "Start Tracker" and "data" in it),
echo   and drag that folder into this window. Then press Enter.
echo.
set "TARGET="
set /p TARGET=Folder of the tracker you use now: 
if not defined TARGET (
  echo Nothing was typed. Nothing was changed.
  goto :end
)
python\python.exe -B -X utf8 -I app\station\install_update.py "%TARGET%"
:end
echo.
pause
popd
