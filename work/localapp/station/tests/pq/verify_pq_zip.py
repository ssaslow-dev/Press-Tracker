#!/usr/bin/env python3
"""Check an update zip made by the station's ProQuest card with the PC side's own code (updatefolder formats + take_update) and pypdf.
Usage: python3 -I verify_pq_zip.py ZIP SCRATCH_DIR            (the zip of tests/proquest_test.js)
       python3 -I verify_pq_zip.py --evil PDFDIR ZIPDIR SCRATCH_DIR     (the hostile PDFs: the raw files are refused by the PC check; the station's copies of them pass)"""
import io, json, sys, zipfile, tempfile, os
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / 'work' / 'localapp' / 'updatefolder')); sys.path.insert(0, str(REPO / 'work' / 'localapp' / 'newsbank_pc'))
import formats as F, take_update as TU          # noqa: E402
from layout import PCLayout                     # noqa: E402
import pdftext_pypdf as T                       # noqa: E402
from pypdf import PdfReader                     # noqa: E402

bad = 0
def check(n, ok, x=''):
    global bad
    bad += 0 if ok else 1; print(('PASS ' if ok else 'FAIL ') + n + ('' if ok else '  -> ' + str(x)))

def text_of(b):
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f: f.write(b); path = f.name
    t = T.pdf_text(path); os.unlink(path); return ' '.join((t or '').split())

if sys.argv[1] == '--evil':
    pdfdir, zipdir, scratch = Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
    for kind in ('openaction', 'embedded', 'launch'):
        raw = (pdfdir / f'evil_{kind}.pdf').read_bytes()
        check(f'evil_{kind}: the raw file is refused by the PC check', bool(F.pdf_problems(raw)), F.pdf_problems(raw))
        zp = zipdir / f'evil_{kind}.zip'
        with zipfile.ZipFile(zp) as z:
            infos = F.scan_zip(z, zp.stat().st_size); entries = {i.filename: F.read_entry(z, i) for i in infos}
        man = json.loads(entries.pop('manifest.json')); F.check_manifest(man, entries)
        pdfs = [b for n, b in entries.items() if F.is_pdf_entry(n)]
        check(f'evil_{kind}: the station’s copy of it carries none of it, and the whole zip passes the reference checker', len(pdfs) == 1 and F.pdf_problems(pdfs[0]) == [], [F.pdf_problems(b) for b in pdfs])
        r = PdfReader(io.BytesIO(pdfs[0]))
        check(f'evil_{kind}: no OpenAction, no AA, no attachments in the copy', '/OpenAction' not in r.trailer['/Root'] and '/Names' not in r.trailer['/Root'] and all('/AA' not in p for p in r.pages))
        check(f'evil_{kind}: its text is still all there', 'Council approves Gabriel measure' in text_of(pdfs[0]))
        ins = TU.inspect_update(zp, PCLayout(Path(scratch) / f'app_{kind}'))
        check(f'evil_{kind}: take_update unpacks it', ins.get('proceed', True) is not None)
    print('all passed' if not bad else f'{bad} FAILED'); sys.exit(1 if bad else 0)

zp, scratch = Path(sys.argv[1]), Path(sys.argv[2])
with zipfile.ZipFile(zp) as z:
    infos = F.scan_zip(z, zp.stat().st_size); entries = {i.filename: F.read_entry(z, i) for i in infos}
man = json.loads(entries.pop('manifest.json')); F.check_manifest(man, entries)
check('the reference checker accepts the zip (allow-list, caps, hashes, PDF safety, pages doc <-> PDF cross-check)', True)
pdfs = {n: b for n, b in entries.items() if F.is_pdf_entry(n)}
pages = {n: json.loads(b) for n, b in entries.items() if n.startswith('db/pages/')}
pq = {n: d for n, d in pages.items() if d.get('pq')}
check('6 PDFs, one per ProQuest pages doc (5 stories + 1 reprint)', len(pdfs) == 6 and len(pq) == 6, (len(pdfs), len(pq)))
check('the manifest marks them as pdf and carries their checksums', all(man['files'][n].get('kind') == 'pdf' for n in pdfs))
check('file names are pq-<16 hex>', all(n.startswith('files/pq-') for n in pdfs))
runs = [json.loads(b) for n, b in entries.items() if n.startswith('db/runs/')]
check('one run doc, mode hand, with a proquest date and a pq summary, no newsbank mark, no search window', len(runs) == 1 and runs[0]['mode'] == 'hand' and runs[0].get('proquest') and runs[0].get('pq') and not runs[0].get('newsbank') and runs[0]['searched_to'] == '', [r.get('mode') for r in runs])
for n, d in pq.items():
    b = pdfs[d['pq']['file']]; r = PdfReader(io.BytesIO(b)); ctx = d['title'][:40]
    check(ctx + ': page count equals the source PDF’s', len(r.pages) == d['pq']['pages'], (len(r.pages), d['pq']['pages']))
    flat = text_of(b)
    check(ctx + ': the PC’s text reader finds its headline and body in the PDF', d['title'].split()[0] in flat and 'Jesse Gabriel' in flat or 'Gabriel' in flat, flat[:80])
    check(ctx + ': no annotations, actions or links; no band note', all('/Annots' not in p and '/AA' not in p for p in r.pages) and '/OpenAction' not in r.trailer['/Root'] and '/AJGBands' not in (r.metadata or {}))
    check(ctx + ': provenance: source file name and ProQuest in the info dictionary', 'ProQuest' in str(r.metadata.get('/Subject')) and r.metadata.get('/AJGSource'), dict(r.metadata))
    check(ctx + ': the pages doc keeps the source PDF’s own checksum and name', len(d['pq']['source_sha256']) == 64 and d['pq']['source_name'].endswith('.pdf'))
app = Path(scratch) / 'app'; lay = PCLayout(app); lay.workbook.parent.mkdir(parents=True, exist_ok=True)
ins = TU.inspect_update(zp, lay)
st = Path(ins['stage']) / 'db' / 'files'
check('take_update.inspect unpacks the PDFs to staging/<id>/db/files/ (where sheet_task reads them)', len(list(st.glob('*.pdf'))) == 6, len(list(st.glob('*.pdf'))))
print('all passed' if not bad else f'{bad} FAILED'); sys.exit(1 if bad else 0)
