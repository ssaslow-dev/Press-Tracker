#!/bin/bash
# Install update.command: puts this NEW version of the AJG Tracker into the tracker folder you already use. Your data (workbook, library, backups, notes) is not touched.
DIR="$(cd "$(dirname "$0")" && pwd)" || exit 1
cd "$DIR" || exit 1
xattr -dr com.apple.quarantine "$DIR" 2>/dev/null
ARCH="$(uname -m)"
if [ "$ARCH" = "x86_64" ] && [ "$(sysctl -n hw.optional.arm64 2>/dev/null)" = "1" ]; then ARCH="arm64"; fi
PY="$DIR/python-$ARCH/bin/python3.13"
chmod +x "$DIR"/python-*/bin/python3.13 2>/dev/null
if [ ! -x "$PY" ]; then
  echo "The new version's Python is missing from this folder. Unzip the new zip again, in full."
  read -r -p "Press Return to close this window. " _
  exit 1
fi
echo "This puts the NEW version of the tracker into the tracker folder you already use."
echo "Your data (workbook, library, backups, notes) is not touched."
echo
echo "Close the tracker first (its Terminal window). Then drag the folder you use now"
echo "(the one with Start Tracker.command and data in it) into this window and press Return."
echo
read -r -p "Folder of the tracker you use now: " TARGET
TARGET="${TARGET%\"}"; TARGET="${TARGET#\"}"; TARGET="${TARGET%\'}"; TARGET="${TARGET#\'}"
TARGET="$(printf '%s' "$TARGET" | sed 's/\\ / /g; s/[[:space:]]*$//')"
if [ -z "$TARGET" ]; then echo "Nothing was typed. Nothing was changed."; read -r -p "Press Return to close. " _; exit 1; fi
"$PY" -B -X utf8 -I app/station/install_update.py "$TARGET"
echo
read -r -p "Press Return to close this window. " _
