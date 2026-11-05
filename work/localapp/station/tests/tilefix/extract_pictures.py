"""Independent of the station code: write every big page picture (JPEG) of a PDF as <out>/<objid>.jpg (raw bytes as stored). Usage: extract_pictures.py in.pdf outdir"""
import sys, os, pypdf
r = pypdf.PdfReader(sys.argv[1]); out = sys.argv[2]; os.makedirs(out, exist_ok=True); seen = set(); n = 0
for p in r.pages:
    xo = (p.get('/Resources') or {}).get('/XObject') or {}
    for k, ref in xo.items():
        o = ref.get_object()
        if o.get('/Subtype') != '/Image' or ref.idnum in seen or int(o['/Width']) < 400 or int(o['/Height']) < 400: continue
        seen.add(ref.idnum)
        if o.get('/Filter') == '/DCTDecode':
            open(os.path.join(out, '%d_%dx%d.jpg' % (ref.idnum, o['/Width'], o['/Height'])), 'wb').write(o._data); n += 1
print(n, 'pictures')
