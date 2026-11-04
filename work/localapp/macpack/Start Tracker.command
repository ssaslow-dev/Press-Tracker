#!/bin/bash
# Start Tracker.command: double-click to start the AJG Tracker on a Mac. Installs nothing, needs no password, talks to this Mac only (127.0.0.1).
DIR="$(cd "$(dirname "$0")" && pwd)" || exit 1
cd "$DIR" || exit 1

fail() {
  echo
  echo "The tracker did not start. Nothing in your data was changed."
  echo "If this keeps happening, take a photo of this window and send it to Claude."
  echo
  read -r -p "Press Return to close this window. " _
  exit 1
}

# Downloaded folders carry a "from the internet" mark that makes macOS ask questions. Removing it from our own folder needs no password.
xattr -dr com.apple.quarantine "$DIR" 2>/dev/null

# Which chip? A Terminal running under Rosetta says x86_64 on an Apple-silicon Mac; ask the hardware instead.
ARCH="$(uname -m)"
if [ "$ARCH" = "x86_64" ] && [ "$(sysctl -n hw.optional.arm64 2>/dev/null)" = "1" ]; then ARCH="arm64"; fi
case "$ARCH" in arm64|x86_64) ;; *) echo "This Mac's chip ($ARCH) is not supported."; fail ;; esac
PY="$DIR/python-$ARCH/bin/python3.13"
if [ ! -x "$PY" ]; then
  chmod +x "$DIR"/python-*/bin/python3.13 2>/dev/null
fi
if [ ! -x "$PY" ]; then
  echo "The tracker's Python is missing from this folder (python-$ARCH/bin/python3.13)."
  echo "The folder may not have been unzipped completely. Unzip it again, in full, then try again."
  fail
fi

if [ "${1:-}" = "--selfcheck" ]; then
  "$PY" -B -X utf8 -I app/station/selfcheck.py; exit $?
fi
"$PY" -B -X utf8 -I app/station/launcher.py "$@" || fail
