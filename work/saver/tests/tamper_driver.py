"""Test-only driver: runs saver.py's CLI but edits one cell of the pass-2 workbook just before the diff reads it.
    python3 -I tamper_driver.py "Sheet|row|col|value" <saver arguments...>
The production program has no such hook; this wraps saver_diff.compare from outside."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
import saver   # noqa: E402

spec = sys.argv[1]
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
sys.exit(saver.main(sys.argv[2:]))
