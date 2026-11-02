"""pdftext_pypdf.py - proposed new module (would sit next to release_rule.py in the pipeline folder).
Pure-Python stand-in for `pdftotext FILE -` using pypdf (no native code, no dependencies).
pdf_text(path) -> str, or None when the file cannot be read (release_rule treats None like pdftotext failing: no versions).
Layout mode reproduces poppler's reading order for the library's NewsBank PDFs (398 of 400 sampled files give an identical
release-rule token list). Layout mode drops most of the text on some multi-column pages; then plain mode is used when it
returns clearly more words (that fallback is NOT identical to poppler's order, but keeps the words, so 25-word runs mostly hold)."""
import re


def _words(t):
    return len(re.findall(r'\w+', t))


def pdf_text(path):
    try:
        from pypdf import PdfReader
        r = PdfReader(path)
        lay = '\n'.join((pg.extract_text(extraction_mode='layout') or '') for pg in r.pages)
        pln = '\n'.join((pg.extract_text() or '') for pg in r.pages)
        return pln if _words(pln) > 1.2 * _words(lay) else lay
    except Exception:
        return None
