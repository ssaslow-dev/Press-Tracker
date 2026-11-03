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
import os
from pathlib import Path

import common as C

STATE_FILES = ('lookup_cache.json', 'outlets.json', 'gabriel_bills_leginfo.json', 'release_texts.json', 'release_related.json')


PENDING = 'pipeline_sync.pending'     # in lay.state: present while the state files are being replaced and PIPELINE.sha256 is not yet rewritten


def _sha_text(pipe: Path) -> str:
    import hashlib
    lines = []
    for p in sorted(pipe.rglob('*')):
        rel = p.relative_to(pipe)
        if not p.is_file() or rel.parts[0] in ('docs', '__pycache__') or '__pycache__' in rel.parts or p.name == 'PIPELINE.sha256' or p.suffix == '.pyc':
            continue
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {rel.as_posix()}")
    return '\n'.join(lines) + '\n'


def write_pipeline_sha(pipe: Path) -> None:
    C.atomic_write(pipe / 'PIPELINE.sha256', _sha_text(pipe).encode('utf-8'))


def recover(lay) -> dict | None:
    """REVIEW_2 finding 5: a crash between replacing the pipeline state files and rewriting PIPELINE.sha256 would leave every later preview,
    save and rebuild refusing (pipeline files differ from the list). sync() leaves a marker while it is in that window. If the marker is found
    and the files really do not match the list, the files replaced so far are put back from state/pipeline_replaced/<stamp>/ (the new copies are
    kept aside in <stamp>-recovered/), the list is written again and the marker is moved to logs/. Nothing is deleted. Returns a note, or None."""
    marker = lay.state / PENDING
    if not marker.is_file():
        return None
    try:
        info = json.loads(marker.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        info = {}
    note = {'recovered': [], 'errors': []}
    try:
        sha_file = lay.pipeline / 'PIPELINE.sha256'
        consistent = sha_file.is_file() and sha_file.read_text(encoding='utf-8') == _sha_text(lay.pipeline)
        if not consistent:
            old = lay.state / 'pipeline_replaced' / str(info.get('stamp') or '')
            aside = lay.state / 'pipeline_replaced' / (str(info.get('stamp') or 'unknown') + '-recovered')
            for name in STATE_FILES:
                src = old / name
                if info.get('stamp') and src.is_file():
                    C.keep_old(lay.pipeline / name, aside)
                    C.atomic_copy(src, lay.pipeline / name)
                    note['recovered'].append(name)
            write_pipeline_sha(lay.pipeline)
            note['rewrote_list'] = True
        (lay.state / 'logs').mkdir(parents=True, exist_ok=True)
        t = lay.state / 'logs' / f'{PENDING}.{C.stamp()}'
        os.replace(marker, t)
    except OSError as e:
        note['errors'].append(repr(e)[:200])
    return note


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
    marker, marker_written = lay.state / PENDING, False
    pf = pub.get('pipeline_files') or {}
    for name in STATE_FILES:
        info = pf.get(name) or {}
        src = None
        if name == 'lookup_cache.json' and pub.get('lookup_cache_out'):
            src = Path(pub['lookup_cache_out'])
        elif info.get('changed') and info.get('path'):
            src = Path(info['path'])
        if src is not None and src.is_file():
            if not marker_written:
                try:
                    lay.state.mkdir(parents=True, exist_ok=True)
                    C.atomic_write(marker, json.dumps({'stamp': stamp, 'at': C.utc_now().isoformat(timespec='seconds')}).encode('utf-8'))
                    marker_written = True
                except OSError as e:
                    errors.append(f'pipeline marker: {e!r}'[:200])
            if put(src, lay.pipeline / name, replaced_pipe, 'pipeline/' + name):
                changed_pipe = True
                if name == 'release_texts.json':
                    put(src, lay.data / 'site' / 'data' / 'release_texts.json', replaced_site, 'site/data/release_texts.json')
    if changed_pipe:
        try:
            write_pipeline_sha(lay.pipeline)
            done.append('pipeline/PIPELINE.sha256')
            if marker_written:
                (lay.state / 'logs').mkdir(parents=True, exist_ok=True)
                os.replace(marker, lay.state / 'logs' / f'{PENDING}.{stamp}')       # the window is closed
        except OSError as e:
            errors.append(f'PIPELINE.sha256: {e!r}'[:200])
    rep = {'at': C.utc_now().isoformat(timespec='seconds'), 'update_id': res.get('update_id'), 'copied': done, 'errors': errors}
    try:
        (lay.state / 'logs').mkdir(parents=True, exist_ok=True)
        (lay.state / 'logs' / f'sync-{stamp}.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
    except OSError:
        pass
    return rep
