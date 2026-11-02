"""After a save: bring the files the saver produced into the tracker folder (APP-POSTSAVE).

The saver (work/saver) writes the workbook, the library and the ledger itself. What it leaves in its working folder, for an
"adapter" to publish (SAVER_SPEC section 8; the manual procedure's step 7), is copied here:
  - the rebuilt page (site/index.html, site/data/sheet.json)  -> data/site/
  - the article shards the save changed (copies_out_merged)    -> data/copies/articles/  (the page reads them from /articles/)
  - the pipeline's own state files that a save changes (lookup cache, outlets, bills, release texts, release related)
                                                                -> app/pipeline/  and PIPELINE.sha256 is written again
Every file that is replaced is first copied to a "replaced" folder (nothing is deleted). Runs while the caller holds the station lock.
"""
from __future__ import annotations

import json
from pathlib import Path

import common as C

STATE_FILES = ('lookup_cache.json', 'outlets.json', 'gabriel_bills_leginfo.json', 'release_texts.json', 'release_related.json')


def write_pipeline_sha(pipe: Path) -> None:
    import hashlib
    lines = []
    for p in sorted(pipe.rglob('*')):
        rel = p.relative_to(pipe)
        if not p.is_file() or rel.parts[0] in ('docs', '__pycache__') or '__pycache__' in rel.parts or p.name == 'PIPELINE.sha256' or p.suffix == '.pyc':
            continue
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {rel.as_posix()}")
    C.atomic_write(pipe / 'PIPELINE.sha256', ('\n'.join(lines) + '\n').encode('utf-8'))


def sync(lay, res: dict) -> dict:
    """res = the saver's save result (with out_dir). Returns {copied: [...], errors: [...]}; never raises for one bad file."""
    out = Path(res['out_dir'])
    pub = res.get('publish') or {}
    stamp = C.stamp()
    done, errors = [], []
    replaced_site = lay.data / 'site_replaced' / stamp
    replaced_copies = lay.copies / '_replaced' / stamp
    replaced_pipe = lay.state / 'pipeline_replaced' / stamp

    def put(src: Path, dst: Path, keep: Path, label: str):
        try:
            if not src.is_file():
                errors.append(f'{label}: {src.name} was not produced')
                return False
            C.keep_old(dst, keep)
            C.atomic_copy(src, dst)
            done.append(label)
            return True
        except OSError as e:
            errors.append(f'{label}: {e!r}'[:200])
            return False

    # 1. the page
    if res.get('site_rebuilt'):
        put(out / 'site' / 'index.html', lay.data / 'site' / 'index.html', replaced_site, 'site/index.html')
        put(out / 'site' / 'data' / 'sheet.json', lay.data / 'site' / 'data' / 'sheet.json', replaced_site, 'site/data/sheet.json')
    # 2. article shards (RELBUTTON-v1: copies_out over copies/articles, INTO that folder, not nested)
    for name in pub.get('copies_out_merged') or []:
        put(out / 'copies' / 'articles' / name, lay.copies / 'articles' / name, replaced_copies, 'articles/' + name)
    # 3. pipeline state files
    changed_pipe = False
    pf = pub.get('pipeline_files') or {}
    for name in STATE_FILES:
        info = pf.get(name) or {}
        src = None
        if name == 'lookup_cache.json' and pub.get('lookup_cache_out'):
            src = Path(pub['lookup_cache_out'])
        elif info.get('changed') and info.get('path'):
            src = Path(info['path'])
        if src is not None and src.is_file():
            if put(src, lay.pipeline / name, replaced_pipe, 'pipeline/' + name):
                changed_pipe = True
                if name == 'release_texts.json':
                    put(src, lay.data / 'site' / 'data' / 'release_texts.json', replaced_site, 'site/data/release_texts.json')
    if changed_pipe:
        try:
            write_pipeline_sha(lay.pipeline)
            done.append('pipeline/PIPELINE.sha256')
        except OSError as e:
            errors.append(f'PIPELINE.sha256: {e!r}'[:200])
    rep = {'at': C.utc_now().isoformat(timespec='seconds'), 'update_id': res.get('update_id'), 'copied': done, 'errors': errors}
    try:
        (lay.state / 'logs').mkdir(parents=True, exist_ok=True)
        (lay.state / 'logs' / f'sync-{stamp}.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
    except OSError:
        pass
    return rep
