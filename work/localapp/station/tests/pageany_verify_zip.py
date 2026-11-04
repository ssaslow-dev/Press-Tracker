#!/usr/bin/env python3
"""N14: check an update zip made from newspaper pages with the PC side's own code (updatefolder formats: allow-list, caps, hashes, PDF safety, pages doc <-> PDF cross-check, names block).
Usage: python3 -I pageany_verify_zip.py ZIP  -> prints PASS/FAIL lines; also prints the PDF names found."""
import json, sys, zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'work' / 'localapp' / 'updatefolder'))
import formats as F  # noqa: E402

zp = Path(sys.argv[1])
with zipfile.ZipFile(zp) as z:
    infos = F.scan_zip(z, zp.stat().st_size)
    entries = {i.filename: F.read_entry(z, i) for i in infos}
man = json.loads(entries.pop('manifest.json'))
F.check_manifest(man, entries)
print('PASS the reference checker accepts the zip (allow-list, caps, hashes, PDF safety, pages doc <-> PDF cross-check, names)')
pdfs = sorted(n for n in entries if F.is_pdf_entry(n))
print('PDFS ' + json.dumps(pdfs))
print('ITEMS ' + json.dumps([(i['fmt'], i['kind'], i['copy']) for i in (man.get('names') or {}).get('items', [])]))
