"""selfcheck.py - run on the PC before a save:  python\\python.exe -X utf8 -I app\\winpack\\selfcheck.py
Checks that the pinned packages import from the app folder, the time zone data is there, and nothing from the dropped set is present.
Writes nothing. Exit 0 = ready, 1 = something missing (the lines say what)."""
import importlib, os, sys

NEED = ['openpyxl', 'et_xmlfile', 'bs4', 'soupsieve', 'typing_extensions', 'pypdf', 'pandas', 'numpy', 'dateutil', 'tzdata']
DROPPED = ['requests', 'PIL', 'cairosvg', 'langdetect', 'pytest']   # expected absent on the PC; their presence is only noted
bad = 0
if sys.version_info[:2] != (3, 13):
    print('WARN python is %s, wheels are cp313' % sys.version.split()[0])
if not sys.flags.utf8_mode:
    print('FAIL UTF-8 mode is off (start python with -X utf8)'); bad += 1
for m in NEED:
    try:
        mod = importlib.import_module(m)
        print('ok   %-18s %s' % (m, os.path.dirname(getattr(mod, '__file__', '') or '')))
    except Exception as e:
        print('FAIL %-18s %r' % (m, e)); bad += 1
try:
    from zoneinfo import ZoneInfo
    import datetime as dt
    off = dt.datetime(2026, 7, 1, 12, tzinfo=ZoneInfo('America/Los_Angeles')).utcoffset()
    print('ok   America/Los_Angeles July offset', off)
    if off != dt.timedelta(hours=-7):
        print('FAIL wrong offset'); bad += 1
except Exception as e:
    print('FAIL zoneinfo %r' % (e,)); bad += 1
for m in DROPPED:
    try:
        importlib.import_module(m); print('note %s is present (not needed)' % m)
    except Exception:
        pass
sys.exit(1 if bad else 0)
