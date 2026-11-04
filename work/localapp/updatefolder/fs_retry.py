"""Wait-and-retry for file moves on Windows (A15, 2026-11-04).

Windows (the virus scanner, the search indexer) sometimes holds a file for a moment after it is written, and a rename or replace of it then
fails with PermissionError 13 "Access is denied". Waiting a few seconds and trying again always worked on the office PC.

retry_busy(fn, *args) calls fn(*args). On PermissionError only it waits and tries again, for about 10 seconds in all (0.05 s, doubling, up to
1 s a pause), then raises that same PermissionError so the caller's own clean refusal still happens. Any other error is raised at once.

This file exists as three identical copies (work/saver/src, work/localapp/updatefolder, and in the built app app/saver and app/updatefolder);
the test work/localapp/app/tests/test_retry_busy.py checks they stay the same. The station layer reaches it as station.common.retry_busy."""
import os
import time

TRIES = 16          # about 11 seconds of waiting before the last try
_sleep = time.sleep   # tests replace this


def retry_busy(fn, *args, **kw):
    delay = 0.05
    for attempt in range(TRIES):
        try:
            return fn(*args, **kw)
        except PermissionError:
            if attempt == TRIES - 1:
                raise
            _sleep(delay)
            delay = min(delay * 2, 1.0)


def replace(src, dst):
    return retry_busy(os.replace, src, dst)


def rename(src, dst):
    return retry_busy(os.rename, src, dst)


def unlink(path, missing_ok=False):
    """delete a file (the app's own temporary files only; the library is never deleted)"""
    def _u():
        try:
            os.unlink(path)
        except FileNotFoundError:
            if not missing_ok:
                raise
    return retry_busy(_u)


def move(src, dst):
    """shutil.move that waits when the file is busy"""
    import shutil
    return retry_busy(shutil.move, str(src), str(dst))
