"""pdftext_pypdf.py - PROPOSED REPLACEMENT for work/localapp/winpack/patches/pdftext_pypdf.py (NEWSBANKPDF-v1). Not wired into assemble_app.py.

Identical to the winpack module for every PDF that has no /AJGBands in its info dictionary (same function, same results). New: a NewsBank story PDF
made by the Update station from a page it shares with a neighbouring story carries /AJGBands (JSON [{"i": page index, "top": y, "bottom": y}], PDF
user-space y). Its text is read inside those bands only, so a neighbour's lines on a shared page never reach the reprint test, the release-text
test or the Clips search. Text is attributed to a band by its baseline y (text matrix x text space), as pypdf reports it to visitor_text.

pdf_text(path) -> str, or None when the file cannot be read (release_rule treats None like pdftotext failing: no versions)."""
import json
import re


def _words(t):
    return len(re.findall(r'\w+', t))


def _bands(reader):
    try:
        raw = (reader.metadata or {}).get('/AJGBands')
        if not raw:
            return None
        out = {}
        for b in json.loads(str(raw)):
            out[int(b['i'])] = (float(b['bottom']), float(b['top']))
        return out or None
    except Exception:
        return None


def _banded_text(reader, bands):
    parts = []
    for i, pg in enumerate(reader.pages):
        band = bands.get(i)
        chunks = []

        def visit(text, cm, tm, font_dict, font_size, _c=chunks, _b=band):
            if not text:
                return
            y = tm[5] * cm[3] + tm[4] * cm[1] + cm[5]
            if _b is None or (_b[0] - 1.0 <= y <= _b[1] + 1.0):
                _c.append(text)
        pg.extract_text(visitor_text=visit)
        parts.append(''.join(chunks))
    return '\n'.join(parts)


def pdf_text(path):
    try:
        from pypdf import PdfReader
        r = PdfReader(path)
        bands = _bands(r)
        if bands:
            return _banded_text(r, bands)
        lay = '\n'.join((pg.extract_text(extraction_mode='layout') or '') for pg in r.pages)
        pln = '\n'.join((pg.extract_text() or '') for pg in r.pages)
        return pln if _words(pln) > 1.2 * _words(lay) else lay
    except Exception:
        return None
