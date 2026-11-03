"""Shared helpers for the three datafix checks (read-only: nothing here writes to the workbook or library)."""
import os, re, sys, pickle, collections, glob
ROOT = '/home/user/Press-Tracker'
S = '/tmp/claude-0/-home-user-Press-Tracker/ec7aac73-d461-552b-aaac-9f8ebc5e7581/scratchpad'
WB = S + '/wb_0bccc1fc.xlsx'
LIB = ROOT + '/data/library'
sys.path.insert(0, ROOT + '/code')

def load_coverage(tab='Coverage'):
    import openpyxl
    wb = openpyxl.load_workbook(WB, read_only=True)
    rows = list(wb[tab].iter_rows(values_only=True))
    h = list(rows[0]); out = []
    for i, r in enumerate(rows[1:], start=2):
        d = dict(zip(h, r)); d['_row'] = i; out.append(d)
    return h, out

def s(v): return '' if v is None else str(v).strip()

def aid(r): return s(r.get('Article ID')).zfill(5)

def lib_path(fname, date=None):
    fname = s(fname)
    if not fname: return None
    for y in ([s(date)[:4]] if date else []) + [p for p in os.listdir(LIB) if p.isdigit()]:
        p = os.path.join(LIB, y, fname)
        if os.path.exists(p): return p
    return None

def read_text(path, limit=20000):
    """plain text of a saved copy (html / pdf / ocr.txt / txt), '' when unreadable"""
    if not path: return ''
    try:
        if path.endswith('.pdf'):
            import pypdf
            rd = pypdf.PdfReader(path)
            return '\n'.join((p.extract_text() or '') for p in rd.pages[:12])[:limit]
        raw = open(path, encoding='utf-8', errors='replace').read()
        if path.endswith('.html'):
            import reprint_rule as rr
            return rr.html_text(raw)[0][:limit]
        return raw[:limit]
    except Exception:
        return ''
