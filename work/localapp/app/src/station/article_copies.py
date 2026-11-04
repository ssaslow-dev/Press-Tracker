"""Article data from the keeper's own library (A11, 2026-11-04).

The tracker page opens a story's saved copy from the article data (data\\copies\\articles: manifest.json plus year shards, each holding the copy of
every story as HTML text). The data shipped with the tracker only holds the stories saved before it was made, so a story saved later has a copy in the
library but none in the article data, and the tracker cannot open it. This module closes that gap from the keeper's own library:

  - for every story whose Original row says Saved Copy? = Yes, and that is not in the manifest yet, it takes the story's saved page
    (the Original row's File name, then File name 2, then the story's other rows in sheet order) from <library>\\<year>\\...
  - an .html page is used as it is (Audio & video stories get the same display clean-up the save gives them);
    a PDF story (NewsBank, ProQuest) gets a text copy made from the .ocr.txt beside it or, if there is none, from the text inside the PDF
  - existing entries are never changed or removed; shards that change are first kept in copies\\_replaced\\<stamp>; the manifest is written last
Reads the workbook and the library, never writes them. Standard library plus (for PDFs and the AV clean-up) the pipeline's own modules."""
from __future__ import annotations

import html as H
import json
import os
import re
import sys
from pathlib import Path

import common as C

SHARD_MB = 12.0
_SKIP_TOP = {'_original_html', '_original_pdf', 'Press releases', '_to_delete', '_renamed', '_replaced'}


def _norm(v) -> str:
    return '' if v is None else str(v).strip()


def read_rows(wb_path: Path):
    """-> (rows of Coverage as dicts, {Article ID: Item type} from Audio & video details)"""
    import openpyxl
    wb = openpyxl.load_workbook(wb_path, read_only=True, data_only=True)
    try:
        def table(name):
            if name not in wb.sheetnames:
                return []
            it = wb[name].iter_rows(values_only=True)
            h = [_norm(x) for x in next(it, [])]
            return [{k: v for k, v in zip(h, r) if k} for r in it if any(r)]
        cov = table('Coverage')
        av = {_norm(r.get('Article ID')): _norm(r.get('Item type')) for r in table('Audio & video details')}
    finally:
        wb.close()
    return cov, av


def library_index(lib: Path) -> dict:
    """file name -> [paths] for the year folders (<year>\\ and undated\\) of the library"""
    idx: dict = {}
    if not lib.is_dir():
        return idx
    for d in sorted(lib.iterdir()):
        if d.is_dir() and d.name not in _SKIP_TOP and not d.name.startswith('.'):
            for f in d.iterdir():
                if f.is_file():
                    idx.setdefault(f.name, []).append(f)
    return idx


def _pdf_page(row: dict, text: str) -> str:
    """a text copy of a PDF story (same look as the NewsBank text copies already in the article data)"""
    e = H.escape
    lines = [ln.strip() for ln in text.replace('\r', '').split('\n')]
    paras, cur = [], []
    for ln in lines:
        if not ln:
            if cur:
                paras.append(' '.join(cur))
                cur = []
            continue
        cur.append(ln)
        if re.search(r'[.!?]["”’\')]?$', ln) and len(ln) < 60:
            paras.append(' '.join(cur))
            cur = []
    if cur:
        paras.append(' '.join(cur))
    head = _norm(row.get('Headline'))
    by = _norm(row.get('Author / byline'))
    meta = ' · '.join(x for x in [_norm(row.get('Outlet')), _norm(row.get('Date'))[:10],
                                       _norm(row.get('Section')) and 'Section: ' + _norm(row.get('Section')),
                                       _norm(row.get('Page')) and 'Page ' + _norm(row.get('Page')),
                                       _norm(row.get('Word count')) and _norm(row.get('Word count')) + ' words'] if x)
    return (f'<html><head><title>{e(head)}</title></head><body><article class="jg-pdf-text">'
            '<p class="pdf-cap">Text of the saved PDF</p>'
            f'<h1>{e(head)}</h1>' + (f'<p class="byline">By {e(by)}</p>' if by else '') + f'<p class="pdf-cap">{e(meta)}</p>'
            + ''.join(f'<p>{e(p)}</p>' for p in paras if p) + '</article></body></html>')


def _pdf_text(lay, path: Path) -> str | None:
    t = path.with_suffix('.ocr.txt')
    if t.is_file():
        try:
            s = t.read_text(encoding='utf-8', errors='replace')
            if s.strip():
                return s
        except OSError:
            pass
    pipe = str(lay.pipeline)
    if pipe not in sys.path:
        sys.path.append(pipe)
    try:
        import pdftext_pypdf
        s = pdftext_pypdf.pdf_text(str(path))
    except Exception:       # noqa: BLE001
        s = None
    return s if s and s.strip() else None


def _av_clean(lay, html: str, lang: str) -> str:
    pipe = str(lay.pipeline)
    if pipe not in sys.path:
        sys.path.append(pipe)
    try:
        import av_display_clean
        return av_display_clean.clean(html, lang or 'English')[0] or html
    except Exception:       # noqa: BLE001  (the plain page is a fine copy)
        return html


def plan(lay) -> dict:
    """what is missing and what could be built. {'missing': n, 'items': [(sid, row, path)], 'unbuildable': [(sid, why)], 'in_manifest': n}"""
    man = {}
    try:
        man = (json.loads((lay.copies / 'articles' / 'manifest.json').read_text(encoding='utf-8')).get('articles') or {})
    except (OSError, ValueError):
        pass
    cov, av = read_rows(lay.workbook)
    by_story: dict = {}
    for r in cov:
        sid = _norm(r.get('Story ID'))
        if sid and _norm(r.get('Original or reprint')).lower() != 'reprint (unverified)':
            by_story.setdefault(sid, []).append(r)
    idx = library_index(lay.library)
    items, bad = [], []
    for sid, rows in by_story.items():
        if sid in man:
            continue
        orig = next((r for r in rows if _norm(r.get('Original or reprint')) == 'Original'), None)
        if orig is None or _norm(orig.get('Saved Copy?')).lower() != 'yes':
            continue
        ordered = [orig] + [r for r in rows if r is not orig and _norm(r.get('Saved Copy?')).lower() == 'yes']
        found = None
        for r in ordered:
            for col in ('File name', 'File name 2'):
                nm = _norm(r.get(col))
                if not nm or nm.upper().startswith('RETRY') or nm.startswith('['):
                    continue
                hit = idx.get(nm)
                if hit:
                    yr = _norm(r.get('Date'))[:4]
                    found = (next((p for p in hit if p.parent.name == yr), hit[0]), r)
                    break
            if found:
                break
        if not found:
            bad.append((sid, 'no saved page for it in the library'))
            continue
        items.append((sid, orig, found[0], found[1], av.get(_norm(orig.get('Article ID')), '')))
    return {'items': items, 'unbuildable': bad, 'in_manifest': len(man)}


def _entry(lay, orig: dict, row: dict, path: Path, item_type: str):
    """-> html text, or (None, why)"""
    ext = path.suffix.lower()
    if ext in ('.html', '.htm'):
        try:
            s = path.read_text(encoding='utf-8', errors='replace')
        except OSError as e:
            return None, f'could not be read ({e.__class__.__name__})'
        if not s.strip():
            return None, 'the saved page is empty'
        if item_type in ('Episode', 'Broadcast segment', 'Video clip'):
            s = _av_clean(lay, s, _norm(orig.get('Language')))
        return s, ''
    if ext == '.pdf':
        t = _pdf_text(lay, path)
        if not t:
            return None, 'no text could be read from the PDF'
        return _pdf_page(row, t), ''
    return None, f'{path.suffix} files have no text copy'


def rebuild(lay, dry_run: bool = False) -> dict:
    """Add the missing copies. Returns {'added': n, 'missing_before': n, 'skipped': [(sid, why)], 'shards': [...], 'dry_run': bool}.
    The caller holds the app lock. Nothing existing is changed; a shard that grows is kept first in copies/_replaced/<stamp>."""
    pl = plan(lay)
    res = {'missing_before': len(pl['items']) + len(pl['unbuildable']), 'added': 0, 'skipped': list(pl['unbuildable']), 'shards': [], 'dry_run': dry_run}
    if dry_run or not pl['items']:
        res['would_add'] = len(pl['items'])
        return res
    adir = lay.copies / 'articles'
    adir.mkdir(parents=True, exist_ok=True)
    mpath = adir / 'manifest.json'
    try:
        man = json.loads(mpath.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        man = {}
    arts = man.setdefault('articles', {})
    changed: dict = {}

    def load(name):
        if name not in changed:
            try:
                changed[name] = json.loads((adir / name).read_text(encoding='utf-8'))
            except (OSError, ValueError):
                changed[name] = {}
        return changed[name]

    def shard_for(year):
        names = sorted({v.split('/')[-1] for v in arts.values() if re.fullmatch(rf'{re.escape(year)}(-\d+)?\.json', v.split('/')[-1])},
                       key=lambda n: int((re.search(r'-(\d+)\.json$', n) or [0, 1])[1]))
        for n in list(changed):
            if re.fullmatch(rf'{re.escape(year)}(-\d+)?\.json', n) and n not in names:
                names.append(n)
        last = names[-1] if names else f'{year}.json'
        size = len(json.dumps(changed[last], ensure_ascii=False)) if last in changed else ((adir / last).stat().st_size if (adir / last).is_file() else 0)
        if size > SHARD_MB * 1e6:
            n = int((re.search(r'-(\d+)\.json$', last) or [0, 1])[1]) + 1
            last = f'{year}-{n}.json'
        return last

    for sid, orig, path, row, itype in pl['items']:
        text, why = _entry(lay, orig, row, path, itype)
        if text is None:
            res['skipped'].append((sid, why))
            continue
        name = shard_for(path.parent.name)
        load(name)[sid] = text
        arts[sid] = f'articles/{name}'
        res['added'] += 1
    if not changed:
        return res
    keep = lay.copies / '_replaced' / C.stamp()
    for name, d in changed.items():
        C.keep_old(adir / name, keep)
        C.atomic_write(adir / name, json.dumps(d, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
    C.keep_old(mpath, keep)
    C.atomic_write(mpath, json.dumps(man, separators=(',', ':')).encode('utf-8'))      # the manifest last: it only names shards that are written
    res['shards'] = sorted(changed)
    return res


def lines(res: dict) -> list:
    """plain-words lines for the panel"""
    out = []
    if res.get('added'):
        out.append(f'{res["added"]} saved copies were added to the tracker\'s article data from your library, so they open now.')
    elif not res.get('skipped'):
        out.append('Every saved copy in the library is already in the article data. Nothing to add.')
    sk = res.get('skipped') or []
    if sk:
        out.append(f'{len(sk)} stories have a saved copy that could not be added (first: ' + ', '.join(f'{s} ({w})' for s, w in sk[:3]) + (f' and {len(sk) - 3} more' if len(sk) > 3 else '') + ').')
    return out
