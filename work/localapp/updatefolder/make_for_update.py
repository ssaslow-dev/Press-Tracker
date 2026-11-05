#!/usr/bin/env python3
"""make_for_update.py: build the "for Update" file (FORMAT.md section 1) from the PC's workbook, the local db folder and the pipeline files.

    python3 -I make_for_update.py --app-root APP                       (PC layout, FORMAT.md section 3)
    python3 -I make_for_update.py --workbook W --db DB --pipeline P --out OUT.json [options]

No article text goes into the file. The workbook is only read (a copy is made first and its checksum compared). build_data.py runs
as a subprocess on a copy of the pipeline files, never edited. No network, nothing written outside the output file and a temp folder.
Exit codes: 0 made, 2 refused (nothing written), 4 bad arguments.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import formats as F          # noqa: E402
import fs_retry as FR        # noqa: E402  (A15: wait and retry when Windows holds a file)
from layout import PCLayout  # noqa: E402

# per story: what the Update page reads (SURVEY 7e); everything else, and all long text, is left out
STORY_KEEP = ('id', 'code', 'aid', 'date', 'prec', 'year', 'outlet', 'pub', 'hl', 'hl_en', 'link', 'plink', 'lstat', 'pq', 'also', 'rep',
              'media', 'county', 'reach', 'lang', 'fmt', 'topic', 'issue', 'bills', 'author', 'authors', 'atitle', 'role', 'tone', 'tauto',
              'src', 'added')
REP_KEEP = ('aid', 'outlet', 'date', 'county', 'state', 'link', 'hl', 'src')
RUN_KEEP = ('at', 'mode', 'newsbank', 'searched_to', 'since', 'since_manual', 'status', 'failed', 'stories', 'reprints')
SHEET_KEEP = ('at', 'written', 'line', 'stories', 'bills', 'newbills')
PIPELINE_COPY_SUFFIXES = ('.py', '.json', '.csv')


class Refused(Exception):
    pass


def project_story(r: dict) -> dict:
    o = {k: r[k] for k in STORY_KEEP if k in r}
    o['reps'] = [{k: x.get(k, '') for k in REP_KEEP} for x in r.get('reps') or []]
    return o


def project_run(doc: dict) -> dict:
    o = {k: doc[k] for k in RUN_KEEP if k in doc}
    sh = doc.get('sheet')
    if isinstance(sh, dict):
        o['sheet'] = {k: sh[k] for k in SHEET_KEEP if k in sh}
    written = isinstance(sh, dict) and sh.get('written') is True
    n = len(doc.get('rows') or [])
    if n and not written:
        o['unsaved_rows'] = n        # finds nobody has taken into the workbook yet; counts only, the rows travel in their own update folder
    return o


def project_clip(doc: dict) -> dict:
    return {k: doc[k] for k in ('date', 'outlet', 'pub', 'hl', 'link', 'plink', 'also', 'rep', 'added') if k in doc}


def project_reprint(doc: dict) -> dict:
    return {k: doc[k] for k in ('story', 'outlet', 'link', 'date', 'added') if k in doc}


def read_collection(db_dir: Path, name: str) -> dict:
    out = {}
    d = Path(db_dir) / name if db_dir else None
    for f in sorted(d.glob('*.json')) if d and d.is_dir() else []:
        try:
            doc = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if isinstance(doc, dict):
            out[f.stem] = doc
    return out


def button_memory(db_dir) -> dict:
    runs = {rid: project_run(d) for rid, d in read_collection(db_dir, 'runs').items()}
    done = [(r.get('at') or '', rid) for rid, r in runs.items() if r.get('mode', 'find') == 'find' and r.get('searched_to')]
    last = max(done) if done else None      # the page's lastSearched(): newest find run that has a searched_to
    return {
        'searched_to': runs[last[1]]['searched_to'] if last else '',
        'searched_run': last[1] if last else '',
        'runs': runs,
        'clips': {i: project_clip(d) for i, d in read_collection(db_dir, 'clips').items()},
        'reprints': {i: project_reprint(d) for i, d in read_collection(db_dir, 'reprints').items()},
        'edits_removed': sorted(i for i, d in read_collection(db_dir, 'edits').items() if d.get('removed')),
    }


def extend_rows(rows_block: dict, workbook: Path) -> dict:
    """PRINTPAGES-v1 / ORIGCOPIES-v1 (proposal): the Update station must (1) recognise a NewsBank print page that the workbook already lists, and (2) know which rows already
    hold a NewsBank PDF. So the rows block gets (a) a column `files` (the row's File name; File name 2; Other files, "; "-joined; '' when none) and (b) one row of kind 'P' for every
    row of the "Unlinked print pages" tab that has a print-page link: [Article ID, '', 'P', Outlet, Date, '', [links], files]. No article text. A row with an old column list is left alone."""
    import openpyxl
    cols = list(rows_block.get('cols') or [])
    if 'files' in cols or not cols:
        return rows_block
    wb = openpyxl.load_workbook(workbook, read_only=True, data_only=True)
    def table(name):
        if name not in wb.sheetnames:
            return [], []
        it = wb[name].iter_rows(values_only=True)
        hdr = [str(c or '') for c in next(it, [])]
        return hdr, [r for r in it if r and any(v not in (None, '') for v in r)]
    ch, crows = table('Coverage')
    ix = {h: i for i, h in enumerate(ch)}
    files = {}
    for r in crows:
        aid = str(r[ix['Article ID']] or '').strip() if 'Article ID' in ix else ''
        if aid:
            files[aid] = '; '.join(str(r[ix[c]]).strip() for c in ('File name', 'File name 2', 'Other files') if c in ix and r[ix[c]] not in (None, ''))
    ai = cols.index('aid')
    out = dict(rows_block)
    out['cols'] = cols + ['files']
    out['rows'] = [list(a) + [files.get(str(a[ai]), '')] for a in rows_block['rows']]
    ph, prows = table('Unlinked print pages')
    pi = {h: i for i, h in enumerate(ph)}
    for r in prows:
        links = [str(r[pi[c]]).strip() for c in ('NewsBank print-page link', 'NewsBank print article link') if c in pi and r[pi[c]] not in (None, '')]
        aid = str(r[pi['Article ID']] or '').strip() if 'Article ID' in pi else ''
        if not aid or not links:
            continue
        d = r[pi['Date']] if 'Date' in pi else ''
        d = d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d or '')[:10]
        row = [''] * len(cols)
        for k, v in (('aid', aid), ('kind', 'P'), ('outlet', str(r[pi['Outlet']] or '') if 'Outlet' in pi else ''), ('date', d), ('links', links)):
            if k in cols:
                row[cols.index(k)] = v
        out['rows'].append(row + [''])
    wb.close()
    return out


def build_blocks(workbook: Path, pipeline: Path, tmp: Path, *, legacy=None, sid_map=None, insights=None) -> tuple[dict, list]:
    """Run build_data.py (a copy of it, in a temp folder) and return ({block name: parsed JSON}, notes)."""
    notes = []
    pipe = tmp / 'pipe'
    pipe.mkdir()
    for f in pipeline.iterdir():
        if f.is_file() and f.suffix in PIPELINE_COPY_SUFFIXES:
            shutil.copy2(f, pipe / f.name)
    if not (pipe / 'build_data.py').is_file():
        raise Refused(f'build_data.py is not in {pipeline}')
    if legacy and Path(legacy).is_file():
        leg = Path(legacy)
    else:
        leg = tmp / 'legacy_stub.html'
        leg.write_text('<script id="data" type="application/json">[]</script>', encoding='utf-8')
        notes.append('no legacy_index.html: fields that only the old page carried (src, added, pub fallbacks) come from the workbook alone')
    sm = sid_map or (pipeline / 'sid_map.json')
    sm = Path(sm) if sm and Path(sm).is_file() else None
    if not sm:
        notes.append('no sid_map.json: idmap lacks the legacy jg- ids whose number changed')
    ins_src = Path(insights) if insights else pipeline / 'insights'
    env = {k: v for k, v in os.environ.items() if k not in ('TABS_DIR', 'INS_DIR')}
    rp = ins_src / 'release_pickup_data.py'
    if rp.is_file():
        ins = tmp / 'ins'
        ins.mkdir()
        shutil.copy2(rp, ins / rp.name)
        env['INS_DIR'] = str(ins)          # only the release-pickup view: it is the one block the Update page reads
    else:
        notes.append('release_pickup_data.py not found: the ins-release_pickup block is empty')
    out = tmp / 'blocks'
    cmd = [sys.executable, '-I', str(pipe / 'build_data.py'), str(workbook), str(leg), str(out)] + ([str(sm)] if sm else [])
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', env=env, cwd=str(tmp))
    if p.returncode != 0:
        raise Refused('build_data.py failed: ' + (p.stderr or p.stdout)[-600:])
    blocks = {}
    for name, fn in (('data', 'data'), ('rows', 'rows'), ('idmap', 'idmap'), ('covcols', 'covcols'), ('fetchrules', 'fetchrules'),
                     ('billsinfo', 'billsinfo'), ('ins_release_pickup', 'ins_release_pickup')):
        f = out / f'{fn}.json'
        if f.is_file():
            blocks[name] = json.loads(f.read_text(encoding='utf-8'))
        elif name in ('data', 'rows', 'idmap', 'covcols'):
            raise Refused(f'build_data.py did not write {fn}.json')
        else:
            notes.append(f'{fn}.json was not produced')
    rep = out / 'report.json'
    if rep.is_file():
        r = json.loads(rep.read_text(encoding='utf-8'))
        for k in ('fetchrules_error', 'prid_error', 'av_error'):
            if r.get(k):
                notes.append(f'build_data {k}: {r[k]}')
    return blocks, notes


def newest_story_date(stories, rows_block, today: str) -> str:
    """NEWEST-v1 (Sammy 2026-11-05): the date of the newest story or row in the tracker (YYYY-MM-DD), never later than today (a mistyped future date is ignored); '' when none"""
    import re
    ds = [str(x.get('date') or '')[:10] for x in stories or []]
    if isinstance(rows_block, dict):
        cols = rows_block.get('cols') or []
        di, ki = (cols.index('date') if 'date' in cols else 4), (cols.index('kind') if 'kind' in cols else 2)
        ds += [str(r[di] or '')[:10] for r in rows_block.get('rows') or [] if len(r) > di and (len(r) <= ki or r[ki] not in ('X', 'P'))]
    ds = [d for d in ds if re.fullmatch(r'\d{4}-\d\d-\d\d', d) and d <= today]
    return max(ds) if ds else ''


def make(workbook, db_dir, pipeline, out_file, *, legacy=None, sid_map=None, insights=None, release_texts=True, now=None) -> dict:
    """Returns {'path', 'bytes', 'workbook_sha256', 'stories', 'notes'}. Never writes next to or into the workbook."""
    workbook, pipeline, out_file = Path(workbook), Path(pipeline), Path(out_file)
    if not workbook.is_file():
        raise Refused(f'workbook {workbook} is not there')
    if not pipeline.is_dir():
        raise Refused(f'pipeline folder {pipeline} is not there')
    notes = []
    if (workbook.parent / ('~$' + workbook.name)).exists():
        notes.append('the workbook is open in Excel; the file on disk (last saved state) was used')
    with tempfile.TemporaryDirectory(prefix='forupdate_') as t:
        tmp = Path(t)
        copy = tmp / 'wb.xlsx'
        sha = F.sha256_file(workbook)
        shutil.copy2(workbook, copy)
        if F.sha256_file(copy) != sha:
            raise Refused('the workbook changed while it was being copied; try again')
        blocks, n2 = build_blocks(copy, pipeline, tmp, legacy=legacy, sid_map=sid_map, insights=insights)
        notes += n2
        if isinstance(blocks.get('rows'), dict):
            blocks['rows'] = extend_rows(blocks['rows'], copy)   # PRINTPAGES-v1 (proposal)
    data = [project_story(r) for r in blocks.pop('data')]
    created = now or F.utc_now_iso()
    newest = newest_story_date(data, blocks.get('rows'), created[:10])
    body = {
        'format': F.FORMAT_FOR_UPDATE,
        'format_version': F.FORMAT_VERSION,
        'created_at': created,
        'newest_story_date': newest,     # NEWEST-v1: the station searches from the day before this (no date to pick)
        'fingerprint': {'workbook_sha256': sha, 'workbook_name': workbook.name, 'workbook_bytes': workbook.stat().st_size},
        'notes': notes,
        'stories': data,
        'rows': blocks['rows'],          # {cols, rows, next}: every Coverage row incl. Reprints, Removed, unverified
        'idmap': blocks['idmap'],
        'covcols': blocks['covcols'],
        'billsinfo': blocks.get('billsinfo', {}),
        'fetchrules': blocks.get('fetchrules', {}),
        'ins_release_pickup': blocks.get('ins_release_pickup', {}),
        'memory': button_memory(db_dir),
    }
    rt = pipeline / 'release_texts.json'
    if release_texts and rt.is_file():
        body['release_texts'] = json.loads(rt.read_text(encoding='utf-8'))
    elif release_texts:
        notes.append('release_texts.json not found: release pickup searches have no sentences')
    blob = F.dumps_compact(body)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    target = out_file
    n = 1
    while target.exists():                 # never overwrite
        n += 1
        target = out_file.with_name(f'{out_file.stem} ({n}){out_file.suffix}')
    tmpf = target.with_name(target.name + f'.part{os.getpid()}')
    tmpf.write_bytes(blob)
    FR.replace(tmpf, target)
    return {'path': str(target), 'bytes': len(blob), 'workbook_sha256': sha, 'stories': len(data), 'notes': notes}


def default_name(sha: str, now: str) -> str:
    return f'for_update_{re.sub(r"[^0-9]", "", now)[:12]}_{sha[:8]}.json'


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--app-root')
    ap.add_argument('--workbook')
    ap.add_argument('--db', help='local db folder: <collection>/<id>.json')
    ap.add_argument('--pipeline')
    ap.add_argument('--out', help='output file (default with --app-root: <data>/for_update/for_update_<time>_<sha8>.json)')
    ap.add_argument('--legacy', help='legacy_index.html if available (optional)')
    ap.add_argument('--sid-map')
    ap.add_argument('--insights', help='folder with release_pickup_data.py (default <pipeline>/insights)')
    ap.add_argument('--no-release-texts', action='store_true')
    a = ap.parse_args(argv)
    try:
        if a.app_root:
            lay = PCLayout(a.app_root)
            wb, db, pipe = lay.workbook, lay.db, lay.pipeline
            out = Path(a.out) if a.out else None
            if out is not None:
                lay.inside(out)
        else:
            if not (a.workbook and a.pipeline and a.out):
                ap.error('give --app-root, or --workbook, --pipeline and --out')
            wb, db, pipe, out = Path(a.workbook), Path(a.db) if a.db else None, Path(a.pipeline), Path(a.out)
        if out is None:
            from datetime import datetime, timezone
            now = F.utc_now_iso()
            out = lay.for_update / default_name(F.sha256_file(wb), now)
        res = make(wb, db, pipe, out, legacy=a.legacy, sid_map=a.sid_map, insights=a.insights, release_texts=not a.no_release_texts)
    except Refused as e:
        print(json.dumps({'ok': False, 'error': str(e)}))
        return 2
    except (OSError, ValueError) as e:
        print(json.dumps({'ok': False, 'error': repr(e)[:300]}))
        return 4
    print(json.dumps(dict(res, ok=True)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
