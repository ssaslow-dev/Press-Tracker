"""PREVIEW-v1: one read-only HTML file of the tracker, with the sheet's data inside it.

Usage (python3 -I):
  make_preview.py --page <PC build's data/site/index.html> --out <file.html> [--workbook <xlsx>] [--as-of YYYY-MM-DD]
                  [--manifest <articles/manifest.json>] [--no-internal]

- Start: the PC tracker's own page (same look and code). Its data is already inside the page; this adds what a double-clicked
  file needs: fonts inlined, a small stand-in for the runtime (shim.js), and CSS that hides everything that writes or updates.
- Left out on purpose: saved article copies, photos, print originals ("View original"), full release texts, the workbook
  itself, notes and edits. Long English translations are cut to 600 characters (no full article text in a shareable file).
- --no-internal also drops Tone, Tone note and "tone rated by" (tauto) from every story (off by default).
- Nothing here touches the repository's shared code; the input page is only read.
"""
import argparse, base64, datetime, json, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT_CAP = 600
HIDE = (  # everything that writes, updates, downloads or opens a library file
    '#runFind,#runRefresh,#raStrip,[data-runfind],#updGo,#updRefresh,#updSave,#updAdd,#updCopy,#updAgain,'
    '[data-trate],[data-afind],[data-trstory],[data-tstop],[data-astop],[data-dl],#bkCsv,#ajgf-btn,'
    '[data-editstory],.tsel,.notebox,.tonebox .tone-status,#fileIn,#dirIn,'
    '#mgTabs [data-mg="upd"],#mgTabs [data-mg="log"],#mgTabs [data-mg="saved"],[data-mgopen="upd"],[data-mgopen="log"],[data-mgopen="saved"]'
    '{display:none!important}')
NO_INTERNAL_HIDE = '.tonebox,.badge.tone,[data-rtone]{display:none!important}'
PREV_CSS = ('.prev-line{font-size:var(--fs-sm);letter-spacing:.06em;text-transform:uppercase;color:#b9c8dc;'
            'padding:0 0 10px;line-height:1.35}')
PLACEHOLDER = ('<div class="lbl">Not in this preview</div>', '<div class="lbl">Saved copy not added yet</div>')


def one(s, old, new, what):
    n = s.count(old)
    if n != 1:
        sys.exit('make_preview: %s: expected 1 match, found %d (the page changed; adapt the patch)' % (what, n))
    return s.replace(old, new)


def block(s, bid):
    m = re.search(r'(<script id="%s" type="application/json">)(.*?)(</script>)' % re.escape(bid), s, re.S)
    if not m:
        sys.exit('block %s not found' % bid)
    return m


def jdump(o):
    return json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def as_of_from(wb):
    try:
        z = zipfile.ZipFile(wb)
        m = re.search(r'<dcterms:modified[^>]*>(\d{4}-\d\d-\d\d)', z.read('docProps/core.xml').decode('utf-8', 'replace'))
        return m.group(1) if m else None
    except Exception:
        return None


def inline_fonts(s, fonts_dir):
    css = open(os.path.join(fonts_dir, 'page.css'), encoding='utf-8').read()
    css = re.sub(r'url\(\./([^)]+\.woff2)\)', lambda m: 'url(data:font/woff2;base64,%s)' % base64.b64encode(
        open(os.path.join(fonts_dir, m.group(1)), 'rb').read()).decode(), css)
    return one(s, '<link rel="stylesheet" href="/fonts/page.css">', '<style>' + css + '</style>', 'fonts link')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--page', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--workbook')
    ap.add_argument('--as-of')
    ap.add_argument('--manifest', help='articles/manifest.json (which stories have saved copies; paths only). Default: next to --page')
    ap.add_argument('--no-internal', action='store_true')
    a = ap.parse_args()

    s = open(a.page, encoding='utf-8').read()
    site = os.path.dirname(os.path.abspath(a.page))
    as_of = a.as_of or (a.workbook and as_of_from(a.workbook))
    if not as_of:
        sys.exit('give --as-of YYYY-MM-DD or --workbook')
    day = datetime.date.fromisoformat(as_of)
    as_of_txt = '%s %d, %d' % (day.strftime('%b'), day.day, day.year)

    # 1. data: cut long translations, drop print originals, optionally the internal fields
    m = block(s, 'data')
    D = json.loads(m.group(2))
    cut = 0
    for r in D:
        t = r.get('text_en')
        if t and len(t) > TEXT_CAP:
            r['text_en'] = t[:TEXT_CAP].rstrip() + '…'
            cut += 1
        if r.get('po'):
            r['po'] = []
        if a.no_internal:
            for k in ('twhy', 'tauto'):
                if k in r:
                    r[k] = '' if k == 'twhy' else False
            if 'tone' in r:
                r['tone'] = ''
    s = s[:m.start(2)] + jdump(D) + s[m.end(2):]

    # 2. fonts inside the file
    s = inline_fonts(s, os.path.join(site, 'fonts'))

    # 3. wording that points at things a preview does not have
    s = one(s, PLACEHOLDER[1], PLACEHOLDER[0], 'saved-copy placeholder label')
    s = re.sub(r'(<div class="ph-note">).*?(</div>)',
               lambda mm: mm.group(1) + 'Saved article copies are not part of this preview. Use the links above to read or watch it at the source.' + mm.group(2),
               s, count=1, flags=re.S)
    s = one(s, '${age > 3 ? `<div class="attn-i"><i class="warn"></i>', '${false ? `<div class="attn-i"><i class="warn"></i>', 'update reminder in Data checks')

    s = one(s, "pick:new Set(), mg:'log',", "pick:new Set(), mg:'quality',", 'Manage opens on Data checks')

    # 4. title, masthead line, hiding rules, shim (before the page's first script)
    s = re.sub(r'<title>AJG Press Coverage Tracker</title>', '<title>AJG Press Coverage Tracker (Preview)</title>', s, count=1)
    line = '<div class="prev-line" id="prevLine">Preview, read-only, data as of %s</div>' % as_of_txt
    s = one(s, '      </div>\n    </div>\n  </div>\n</header>', '      </div>\n    </div>\n' + line + '\n  </div>\n</header>', 'masthead')
    manifest = a.manifest or os.path.join(site, 'articles', 'manifest.json')
    man = {}
    if os.path.isfile(manifest):
        man = json.load(open(manifest, encoding='utf-8')).get('articles', {})
    mj = {'articles': man}
    css = '<style id="prev-hide">' + HIDE + (NO_INTERNAL_HIDE if a.no_internal else '') + PREV_CSS + '</style>'
    shim = open(os.path.join(HERE, 'shim.js'), encoding='utf-8').read()
    inject = css + '<script id="prev-manifest" type="application/json">' + jdump(mj) + '</script><script>' + shim + '</script>'
    i = s.find('<script')
    if i < 0:
        sys.exit('no script in page')
    s = s[:i] + inject + s[i:]

    open(a.out, 'w', encoding='utf-8').write(s)
    print('written %s (%.1f MB); as of %s; %d stories; %d long translations cut; %d saved-copy paths listed' % (
        a.out, os.path.getsize(a.out) / 1e6, as_of, len(D), cut, len(man)))


if __name__ == '__main__':
    main()
