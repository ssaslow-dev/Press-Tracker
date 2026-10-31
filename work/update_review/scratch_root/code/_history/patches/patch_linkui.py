#!/usr/bin/env python3
"""LINKUI-v1 (agent-insights, 2026-10-27; Sammy's artifact comment): link UI cleanup. Idempotent (marker per target).
  python3 -I patch_linkui.py [--js build/js_merged.js] [--build-data code/build_data.py] [--view build/insights/bill_timeline.js]
1. No NewsBank print-page links (kind nbpg, "NewsBank print page via CA State Library") anywhere:
   build_data links_of() stops emitting them; the tracker's LINK_KIND loses nbpg, so linksOf() drops them from old data,
   and NewsBank image (print-page) URLs on records without lk (Update finds, live reprints) are not listed either.
   Kept: nbpa (print edition), nb, pq, pub, tv, and the "Full print edition (PDF)" link.
2. A copy-link icon button sits immediately LEFT of every link's text: linkA() (story panel), the PDF link, the Update
   review lists (found, reprints, left out) and the Insights views (ctx.cpBtn; bill_timeline's leginfo link). One
   delegated handler copies the URL and shows a check for 1.5 s. The old text "Copy link" button is removed."""
import argparse, sys
MARK = 'LINKUI-v1'

CP_JS = r'''
/* LINKUI-v1: a copy-link icon button to the LEFT of every link's text (one delegated handler below) */
const CP_ICON = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><rect x="5.5" y="5.5" width="8" height="8" rx="1.6" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M10.5 3.5v-.4A1.6 1.6 0 0 0 8.9 1.5H4.1A1.6 1.6 0 0 0 2.5 3.1v4.8a1.6 1.6 0 0 0 1.6 1.6h.4" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>';
const CP_OK = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><path d="M3 8.5l3.2 3L13 4.5" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const cpBtn = u => u ? `<button type="button" class="cpb" data-cp="${esc(u)}" title="Copy link" aria-label="Copy link">${CP_ICON}</button>` : '';
try { document.head.insertAdjacentHTML('beforeend', `<style id="linkui-css">
.cpb{border:0;background:none;color:var(--ink-3);padding:0;width:22px;height:22px;display:inline-grid;place-items:center;border-radius:5px;flex:none;cursor:pointer;vertical-align:middle;position:relative;margin-right:2px}
.cpb:hover{color:var(--accent);background:var(--panel-2)} .cpb:focus-visible{outline:2px solid var(--focus);outline-offset:1px}
.cpb.ok{color:var(--good)} .cpb svg{display:block}
.lkw{display:inline-flex;align-items:center;gap:2px;min-width:0}
.dlinks .lkw a{align-items:baseline}
.upd-item .h .cpb{margin:-2px 4px 0 -2px}
@media (pointer:coarse){.cpb::after{content:"";position:absolute;inset:-11px -3px -11px -11px}}
</style>`); } catch(e){}
document.addEventListener('click', e => { const b = e.target.closest('button[data-cp]'); if (!b) return;
  e.preventDefault(); e.stopPropagation();
  let u = b.dataset.cp; try { u = new URL(u, location.href).href; } catch(x){}
  copy(u, 'Copied the link');
  b.innerHTML = CP_OK; b.classList.add('ok'); clearTimeout(b._cpT);
  b._cpT = setTimeout(() => { b.innerHTML = CP_ICON; b.classList.remove('ok'); }, 1500); }, true);
/* /LINKUI-v1 */
'''

JS_R = [
 ("  nbpa: ['NewsBank print edition via CA State Library', 'library card login'], nbpg: ['NewsBank print page via CA State Library', 'library card login'],\n",
  "  nbpa: ['NewsBank print edition via CA State Library', 'library card login'],  /* LINKUI-v1: no NewsBank print-page (nbpg) links */\n"),
 ("    else if (/^https?:\\/\\/infoweb-newsbank-com\\.castatelib\\.idm\\.oclc\\.org\\//i.test(u)) add('nb', u);\n",
  "    else if (/[?&]docref=image(\\/|%2F)/i.test(u)) {}  /* LINKUI-v1: a NewsBank print page is not listed */\n"
  "    else if (/^https?:\\/\\/infoweb-newsbank-com\\.castatelib\\.idm\\.oclc\\.org\\//i.test(u)) add('nb', u);\n"),
 ("  return `<a href=\"${esc(p[1])}\" target=\"_blank\" rel=\"noopener\" data-lk=\"${p[0]}\"><b>${label} ↗</b><span>${esc(sub || h)}</span></a>`; }\n",
  "  return `<span class=\"lkw\">${cpBtn(p[1])}<a href=\"${esc(p[1])}\" target=\"_blank\" rel=\"noopener\" data-lk=\"${p[0]}\"><b>${label} ↗</b><span>${esc(sub || h)}</span></a></span>`; }\n"
  + CP_JS),
 ("dl.insertAdjacentHTML('afterbegin', `<a href=\"${esc(pdf.url)}\" target=\"_blank\" rel=\"noopener\"><b>${pdf.text ? 'ProQuest PDF' : 'Full print edition (PDF)'} ↗</b><span>${pdf.pages ? pl(pdf.pages, 'page') : 'PDF'}</span></a>`);",
  "dl.insertAdjacentHTML('afterbegin', `<span class=\"lkw\">${cpBtn(pdf.url)}<a href=\"${esc(pdf.url)}\" target=\"_blank\" rel=\"noopener\"><b>${pdf.text ? 'ProQuest PDF' : 'Full print edition (PDF)'} ↗</b><span>${pdf.pages ? pl(pdf.pages, 'page') : 'PDF'}</span></a></span>`);"),
 ("<div class=\"dlinks\">${links.join('')}<button class=\"linkbtn\" data-clink>Copy link</button><button class=\"linkbtn\" data-editstory>Edit details</button></div>",
  "<div class=\"dlinks\">${links.join('')}<button class=\"linkbtn\" data-editstory>Edit details</button></div>"),
 ("      <div class=\"h\"><a href=\"${esc(r.link)}\" target=\"_blank\" rel=\"noopener\">${esc(r.hl)}</a></div>",
  "      <div class=\"h\">${cpBtn(r.link)}<a href=\"${esc(r.link)}\" target=\"_blank\" rel=\"noopener\">${esc(r.hl)}</a></div>"),
 ("      <div class=\"h\"><a href=\"${esc(p.link)}\" target=\"_blank\" rel=\"noopener\">${esc(p.hl)}</a></div>",
  "      <div class=\"h\">${cpBtn(p.link)}<a href=\"${esc(p.link)}\" target=\"_blank\" rel=\"noopener\">${esc(p.hl)}</a></div>"),
 ("<div class=\"h\"><a href=\"${esc(s.c.url)}\" target=\"_blank\" rel=\"noopener\">${esc(s.c.title||s.c.url)}</a></div>",
  "<div class=\"h\">${cpBtn(s.c.url)}<a href=\"${esc(s.c.url)}\" target=\"_blank\" rel=\"noopener\">${esc(s.c.title||s.c.url)}</a></div>"),
]

def _apply(path, R, mark_line, mark=MARK):
    import os
    if not os.path.exists(path):
        return 'skipped (no file)'
    s = open(path, encoding='utf-8').read()
    if mark in s:
        return 'unchanged'
    for a, b in R:
        n = s.count(a)
        if n != 1:
            raise SystemExit(f'{path}: anchor found {n}x: {a[:80]}')
        s = s.replace(a, b)
    if mark_line and MARK not in s:
        s = s.rstrip('\n') + '\n' + mark_line + '\n'
    open(path, 'w', encoding='utf-8').write(s)
    return 'patched'

def patch_js(path):
    return _apply(path, JS_R, None, '/* LINKUI-v1: a copy-link icon button')

def patch_build_data(path):
    return _apply(path, [(
        "                               ('nbpg', 'NewsBank print-page link', 'NewsBank print page article link via CA State Library'),\n",
        "                               # LINKUI-v1: no NewsBank print-page (nbpg) links; the print edition (nbpa) stays\n")], None, '# LINKUI-v1')

def patch_view(path):
    return _apply(path, [(
        "    if (url) notes.push(`<a class=\"linkbtn\" href=\"${ctx.esc(url)}\" target=\"_blank\" rel=\"noopener\">leginfo history</a>`);",
        "    if (url) notes.push(`<span class=\"lkw\">${ctx.cpBtn ? ctx.cpBtn(url) : ''}<a class=\"linkbtn\" href=\"${ctx.esc(url)}\" target=\"_blank\" rel=\"noopener\">leginfo history</a></span>`);  // LINKUI-v1")], None, '// LINKUI-v1')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--js'); ap.add_argument('--build-data'); ap.add_argument('--view', action='append', default=[])
    a = ap.parse_args()
    if a.js: print('js:', patch_js(a.js))
    if a.build_data: print('build_data:', patch_build_data(a.build_data))
    for v in a.view: print('view:', v, patch_view(v))
