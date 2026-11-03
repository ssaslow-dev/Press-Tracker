"""Test-only: runs the app's save program, but writes one cell of the pass-2 workbook just before the diff reads it (what a faulty sheet_task would do).
    AJG_TAMPER="Sheet|row|Column|value" AJG_SAVER_DIR=<build>/app/saver  python -I tamper_saver.py <the save program's arguments>
Used with take_update.py --saver. The production program has no such hook; this wraps saver_diff.compare from outside (as work/saver/tests/tamper_driver.py)."""
import os
import sys
from pathlib import Path

SAVER_DIR = Path(os.environ['AJG_SAVER_DIR'])          # <build>/app/saver
sys.path.insert(0, str(SAVER_DIR))
import saver   # noqa: E402

spec = os.environ['AJG_TAMPER']
real = saver.D.compare


def tampered(before, after, *a, **k):
    import openpyxl
    sheet, row, col, val = spec.split('|', 3)
    wb = openpyxl.load_workbook(str(after))
    ws = wb[sheet]
    ws.cell(int(row), {c.value: c.column for c in ws[1]}[col]).value = val
    wb.save(str(after))
    return real(before, after, *a, **k)


saver.D.compare = tampered
sys.exit(saver.main(sys.argv[1:]))
