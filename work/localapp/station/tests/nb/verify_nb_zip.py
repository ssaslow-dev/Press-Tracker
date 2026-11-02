#!/usr/bin/env python3
"""Check an update zip made by the station's NewsBank card with the PC side's own code (updatefolder formats + take_update) and pypdf.
Usage: python3 -I verify_nb_zip.py ZIP SCRATCH_DIR"""
import json, sys, zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / 'work' / 'localapp' / 'updatefolder')); sys.path.insert(0, str(REPO / 'work' / 'localapp' / 'newsbank_pc'))
import formats as F, take_update as TU          # noqa: E402
from layout import PCLayout                     # noqa: E402
import pdftext_pypdf as T                       # noqa: E402
from pypdf import PdfReader                     # noqa: E402

zp, scratch = Path(sys.argv[1]), Path(sys.argv[2])
bad = 0
def check(n, ok, x=''):
    global bad
    bad += 0 if ok else 1; print(('PASS ' if ok else 'FAIL ') + n + ('' if ok else '  -> ' + str(x)))

with zipfile.ZipFile(zp) as z:
    infos = F.scan_zip(z, zp.stat().st_size); entries = {i.filename: F.read_entry(z, i) for i in infos}
man = json.loads(entries.pop('manifest.json')); F.check_manifest(man, entries)
check('the reference checker accepts the zip (allow-list, caps, hashes, PDF safety, pages doc <-> PDF cross-check)', True)
pdfs = {n: b for n, b in entries.items() if F.is_pdf_entry(n)}
pages = {n: json.loads(b) for n, b in entries.items() if n.startswith('db/pages/')}
nbdocs = {n: d for n, d in pages.items() if d.get('nb')}
check('33 story PDFs, one per pages doc that names one', len(pdfs) == 33 and len(nbdocs) == 33, (len(pdfs), len(nbdocs)))
check('the manifest marks them as pdf and carries their checksums', all(man['files'][n].get('kind') == 'pdf' for n in pdfs))
runs = [json.loads(b) for n, b in entries.items() if n.startswith('db/runs/')]
check('one run doc, mode newsbank', len(runs) == 1 and runs[0]['mode'] == 'newsbank', [r.get('mode') for r in runs])
titles = {d['title'] for d in nbdocs.values()}
import io
shared = banded = 0
for n, d in nbdocs.items():
    nb = d['nb']; b = pdfs[nb['file']]; r = PdfReader(io.BytesIO(b)); a, z_ = nb['batch']['pages']
    ctx = d['title'][:40]
    if len(r.pages) != z_ - a + 1: check(ctx + ': page count', False, (len(r.pages), a, z_))
    t = T.pdf_text_bytes(b) if hasattr(T, 'pdf_text_bytes') else None
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f: f.write(b); path = f.name
    t = T.pdf_text(path); os.unlink(path)
    flat = ' '.join((t or '').split())
    if d['title'] not in flat.replace('\n', ' ') and not all(w in flat for w in d['title'].split()[:4]): check(ctx + ': its own headline in its text', False, flat[:100])
    others = [x for x in titles if x != d['title'] and not x.startswith('Second search') or (x != d['title'] and x.startswith('Second search') and x[:22] != d['title'][:22])]
    leak = [x for x in titles if x != d['title'] and x in flat]
    if leak: check(ctx + ': no neighbour’s headline in its text', False, leak)
    if 'docref=' + nb['docref'].replace('%', '%') not in flat.replace(' ', '') and nb['docref'].replace('%3A', ':') not in flat.replace(' ', ''): check(ctx + ': its own docref in its text', False, nb['docref'])
    if nb['batch']['bands']:
        shared += 1; banded += 1 if r.metadata.get('/AJGBands') else 0
        check(ctx + ': a shared page has its band in the info dictionary and a crop box', bool(r.metadata.get('/AJGBands')) and any(float(p.cropbox.height) < float(p.mediabox.height) - 1 for p in r.pages), r.metadata.get('/AJGBands'))
    check(ctx + ': no annotations, actions or links', all('/Annots' not in p and '/AA' not in p for p in r.pages) and '/OpenAction' not in r.trailer['/Root'])
print('stories on shared pages with bands:', banded, 'of', shared)
app = Path(scratch) / 'app'; lay = PCLayout(app); lay.workbook.parent.mkdir(parents=True, exist_ok=True)
ins = TU.inspect_update(zp, lay)
st = Path(ins['stage']) / 'db' / 'files'
check('take_update.inspect unpacks the PDFs to staging/<id>/db/files/ (where sheet_task reads them)', len(list(st.glob('*.pdf'))) == 33, len(list(st.glob('*.pdf'))))
print('all passed' if not bad else f'{bad} FAILED'); sys.exit(1 if bad else 0)
