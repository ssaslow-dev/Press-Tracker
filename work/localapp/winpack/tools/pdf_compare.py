"""Compare pdftotext with pure-Python extractors on library PDFs, through the release rule's own tokenising.
Read-only. Run: python3 -I tools/pdf_compare.py [N] [seed]   (needs pypdf, pdfminer.six; poppler's pdftotext on PATH)
For each PDF it builds what release_rule.file_versions builds (the 'pdf' version after the citation cut, and the excerpt
version) from each extractor's text and reports whether the token lists (raw) are identical."""
import glob, os, random, re, subprocess, sys, time, io, json
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')) if False else '/home/user/Press-Tracker'
sys.path.insert(0, os.path.join(REPO, 'code'))
import release_rule as REL
import reprint_rule as RR

def t_poppler(p):
    return subprocess.run(['pdftotext', p, '-'], capture_output=True, text=True, timeout=60).stdout

def t_pypdf(p):
    from pypdf import PdfReader
    r = PdfReader(p)
    return '\n'.join((pg.extract_text(extraction_mode='layout') or '') for pg in r.pages)

def t_pdfminer(p):
    from pdfminer.high_level import extract_text
    return extract_text(p)

def versions(t):
    ev = REL.excerpt_version(t)
    t = re.split(r'\n\s*Citation \(apa Style\)', t)[0]
    return [RR.version(t, 'nb', 'pdf')] + ([ev] if ev else [])

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    files = sorted(glob.glob(os.path.join(REPO, 'data', 'library', '*', '*.pdf')))
    random.Random(seed).shuffle(files)
    files = files[:n]
    ext = {'pypdf': t_pypdf, 'pdfminer': t_pdfminer}
    if os.environ.get('ONLY'):
        ext = {k: v for k, v in ext.items() if k == os.environ['ONLY']}
    stat = {k: {'same': 0, 'diff': 0, 'err': 0, 'secs': 0.0, 'worst': []} for k in ext}
    ptime = 0.0
    for i, f in enumerate(files):
        t0 = time.time(); base = t_poppler(f); ptime += time.time() - t0
        bv = versions(base)
        for k, fn in ext.items():
            s = stat[k]
            t0 = time.time()
            try:
                tv = versions(fn(f))
            except Exception as e:
                s['err'] += 1; s['worst'].append((os.path.basename(f), 'ERR ' + repr(e)[:80])); continue
            s['secs'] += time.time() - t0
            same = [a['raw'] for a in bv] == [a['raw'] for a in tv]
            if same:
                s['same'] += 1
            else:
                s['diff'] += 1
                a, b = bv[0]['raw'], tv[0]['raw']
                import difflib
                sm = difflib.SequenceMatcher(None, a, b, autojunk=False) if len(a) < 4000 else None
                ratio = round(sm.ratio(), 4) if sm else None
                s['worst'].append((os.path.basename(f), len(a), len(b), ratio, len(bv), len(tv)))
    print(json.dumps({'n': len(files), 'poppler_secs': round(ptime, 1), 'stats': {k: {**v, 'worst': v['worst'][:12]} for k, v in stat.items()}}, indent=1))

if __name__ == '__main__':
    main()
