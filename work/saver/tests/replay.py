"""Replay harness for `saver.py preview` (SAVER_SPEC section 9, fixture 1 only in this pass).

    python3 -I replay.py [--fixture DIR] [--scratch DIR] [--keep-going]

Builds a fresh working folder under L/work/saver/scratch/ (never inside the fixture), copies the fixture's inputs into it
(in.xlsx as the master, db/, queue/, pipeline/ + a generated PIPELINE.sha256, copies/, img_cache/), seeds a ledger with
init --sha sha256(in.xlsx), runs `saver.py preview --today <from result.at>`, then requires:

  1. the saver's pass-2 output equals the hand-made STAGED workbook cell for cell (sheet order, header rows, every value);
  2. the changes preview reports (in.xlsx -> output) equal the changes between in.xlsx and STAGED, computed here by a second, independent
     comparison (not saver_diff);
  3. result.json / result2.json of the replay equal the fixture's, apart from documented timestamp fields;
  4. the pages the replay wrote equal the fixture's pages byte for byte.

Every difference is printed with its location. Nothing is explained away by the harness: a difference is either listed under
DOCUMENTED (a timestamp field named below) or it is a finding. Exit 0 only when there are no findings."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAVER_DIR = HERE.parent
L = SAVER_DIR.parent.parent
DEFAULT_FIXTURE = SAVER_DIR / 'fixtures' / 'runsave_2026-10-30'
SAVER = SAVER_DIR / 'src' / 'saver.py'
PIPELINE_SHA_TOOL = SAVER_DIR / 'tools' / 'pipeline_sha.py'

# the only differences this harness accepts without calling them findings. The spec names result.at / result2.at and docProps/core.xml
# (never compared: only cells are). Pass-1 `at` lives in result.json['at']; pass 2 in result2.json['at'].
DOCUMENTED_JSON = {'result.json': {('at',)}, 'result2.json': {('at',)}}


def sha256(p) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def blank(v):
    return v is None or (isinstance(v, str) and v.strip() == '')


def canon(v):
    return int(v) if isinstance(v, float) and v.is_integer() and not isinstance(v, bool) else v


def read_values(path):
    import openpyxl
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=False)
    try:
        return wb.sheetnames, {ws.title: [list(r) for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets}
    finally:
        wb.close()


def cell_changes(a_path, b_path):
    """{(sheet, row number, column header): (kind, old, new)} between two workbooks, positional by row (an independent re-statement of
    runsave/fastdiff.py: blank vs blank is no change; added = row beyond the old sheet; filled = blank -> value; changed = anything else)"""
    an, A = read_values(a_path)
    bn, B = read_values(b_path)
    out = {}
    for n in bn:
        if n not in A:
            out[(n, 0, '(sheet)')] = ('added sheet', None, None)
            continue
        hdr = B[n][0] if B[n] else []
        for r in range(max(len(A[n]), len(B[n]))):
            ra = A[n][r] if r < len(A[n]) else []
            rb = B[n][r] if r < len(B[n]) else []
            for c in range(max(len(ra), len(rb))):
                va = ra[c] if c < len(ra) else None
                vb = rb[c] if c < len(rb) else None
                if blank(va) and blank(vb) or (not blank(va) and not blank(vb) and canon(va) == canon(vb)):
                    continue
                kind = 'added' if r >= len(A[n]) else ('filled' if blank(va) else 'changed')
                out[(n, r + 1, str(hdr[c]) if c < len(hdr) and hdr[c] is not None else f'#{c + 1}')] = (kind, va, vb)
    return an, bn, out


def compare_books(x_path, y_path, limit=40):
    """cell-for-cell equality of two workbooks (values, sheet order, header rows). Returns list of difference strings."""
    xn, X = read_values(x_path)
    yn, Y = read_values(y_path)
    diffs = []
    if xn != yn:
        diffs.append(f'sheet names/order differ: {xn} vs {yn}')
    for n in xn:
        if n not in Y:
            continue
        a, b = X[n], Y[n]
        if len(a) != len(b):
            diffs.append(f'{n}: {len(a)} rows vs {len(b)} rows')
        for r in range(min(len(a), len(b))):
            ra, rb = a[r], b[r]
            for c in range(max(len(ra), len(rb))):
                va = ra[c] if c < len(ra) else None
                vb = rb[c] if c < len(rb) else None
                if (blank(va) and blank(vb)) or (not blank(va) and not blank(vb) and canon(va) == canon(vb)):
                    continue
                diffs.append(f'{n} r{r + 1} c{c + 1}: {str(va)[:60]!r} vs {str(vb)[:60]!r}')
                if len(diffs) > limit * 10:
                    return diffs
    return diffs


def walk_diff(a, b, path=()):
    """differences between two JSON values as (path, a, b)"""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a:
                out.append((path + (k,), '<absent>', b[k]))
            elif k not in b:
                out.append((path + (k,), a[k], '<absent>'))
            else:
                out += walk_diff(a[k], b[k], path + (k,))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((path, f'<list of {len(a)}>', f'<list of {len(b)}>'))
        for i, (x, y) in enumerate(zip(a, b)):
            out += walk_diff(x, y, path + (i,))
    elif a != b:
        out.append((path, a, b))
    return out


def dirs_diff(a: Path, b: Path):
    fa = {p.relative_to(a).as_posix(): p for p in a.rglob('*') if p.is_file()}
    fb = {p.relative_to(b).as_posix(): p for p in b.rglob('*') if p.is_file()}
    out = [f'only in fixture: {k}' for k in sorted(set(fa) - set(fb))] + [f'only in replay: {k}' for k in sorted(set(fb) - set(fa))]
    out += [f'differs: {k}' for k in sorted(set(fa) & set(fb)) if fa[k].read_bytes() != fb[k].read_bytes()]
    return out


def prepare(fixture: Path, work: Path):
    work.mkdir(parents=True)
    master_dir = work / 'master'
    master_dir.mkdir()
    master = master_dir / 'AJG Coverage - NewsBank.xlsx'
    shutil.copy2(fixture / 'in.xlsx', master)
    shutil.copytree(fixture / 'db', work / 'db')
    shutil.copytree(fixture / 'queue', work / 'queue')
    # the fixture's pipeline folder as the manual run used it; docs/ and __pycache__ are not part of the published pipeline files
    shutil.copytree(fixture / 'pipeline', work / 'pipeline', ignore=shutil.ignore_patterns('docs', '__pycache__', '*.pyc'))
    subprocess.run([sys.executable, '-I', str(PIPELINE_SHA_TOOL), str(work / 'pipeline')], check=True, capture_output=True)
    # copies/articles/articles/ is the manual run's own output (the nested copy of copies_out), not an input
    shutil.copytree(fixture / 'copies', work / 'copies', ignore=lambda d, names: ['articles'] if Path(d).name == 'articles' and 'articles' in names else [])
    shutil.copytree(fixture / 'img_cache', work / 'img_cache_in')
    for d in ('library', 'backups'):
        (work / d).mkdir()
    return master


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--fixture', default=str(DEFAULT_FIXTURE))
    ap.add_argument('--scratch', default=str(SAVER_DIR / 'scratch'))
    ap.add_argument('--literal-copies', action='store_true', help='diagnostic: copy copies_out the way the manual run did (nested copies/articles/articles)')
    a = ap.parse_args(argv)
    fx = Path(a.fixture)
    staged = next(fx.glob('*STAGED*.xlsx'))
    exp1 = json.loads((fx / 'result.json').read_text(encoding='utf-8'))
    today = exp1['at'][:10]
    run = next(iter(k for k in exp1['runs'] if k != '_reprints'))
    work = Path(a.scratch) / f"replay_{fx.name}_{time.strftime('%Y%m%dT%H%M%S')}"
    master = prepare(fx, work)
    findings = []
    t0 = time.time()

    import os
    env = dict(os.environ, **({'SAVER_TEST_COPIES_OUT_LITERAL': '1'} if a.literal_copies else {}))

    def sv(*args):
        return subprocess.run([sys.executable, '-I', str(SAVER), *args], capture_output=True, text=True, encoding='utf-8', env=env)
    p = sv('init', '--workbook', str(master), '--state', str(work / 'state'), '--sha', sha256(master), '--note', 'replay seed')
    if p.returncode != 0:
        print('init failed', p.stdout, p.stderr)
        return 1
    master_sha = sha256(master)
    out = work / 'out'
    p = sv('preview', '--workbook', str(master), '--db', str(work / 'db'), '--queue', str(work / 'queue'), '--pipeline', str(work / 'pipeline'),
           '--copies', str(work / 'copies'), '--library', str(work / 'library'), '--backups', str(work / 'backups'), '--out', str(out),
           '--state', str(work / 'state'), '--today', today, '--run', run, '--img-cache', str(work / 'img_cache_in'))
    print(f'preview exit {p.returncode} in {time.time() - t0:.0f}s; work folder {work}')
    if p.stderr.strip():
        print('stderr:', p.stderr[-500:])
    try:
        res = json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        print('no JSON result on stdout:', p.stdout[-500:])
        return 1
    if p.returncode != 0 or not res.get('ok'):
        print('PREVIEW DID NOT COMPLETE:', json.dumps(res.get('refusal'), indent=1, default=str)[:3000])
        return 1
    print('line:', res['line'])
    print('diff summary:', json.dumps(res['diff'], default=str))
    if sha256(master) != master_sha:
        findings.append('THE MASTER CHANGED during preview')

    out_xlsx = Path(res['workbook']['out_path'])
    # 1. output vs STAGED, cell for cell
    d1 = compare_books(out_xlsx, staged)
    print(f'\n[1] saver output vs STAGED, cell for cell: {len(d1)} differences')
    for d in d1[:40]:
        print('   ', d)
    findings += [f'output vs STAGED: {d}' for d in d1]

    # 2. the predicted changes vs the changes between in.xlsx and STAGED (independent comparison)
    an, bn, exp_ch = cell_changes(fx / 'in.xlsx', staged)
    _, _, got_ch = cell_changes(fx / 'in.xlsx', out_xlsx)
    only_exp = sorted(set(exp_ch) - set(got_ch))
    only_got = sorted(set(got_ch) - set(exp_ch))
    diff_vals = sorted(k for k in set(exp_ch) & set(got_ch) if (exp_ch[k][0], canon(exp_ch[k][2])) != (got_ch[k][0], canon(got_ch[k][2])))
    # and the saver's own diff.tsv line count / allowed tags against the independent count
    tsv = Path(res['diff']['tsv']).read_text(encoding='utf-8').splitlines()[1:]
    print(f'\n[2] in.xlsx -> STAGED: {len(exp_ch)} changed cells; in.xlsx -> saver output: {len(got_ch)}; saver diff.tsv lines: {len(tsv)}; '
          f'only in STAGED diff: {len(only_exp)}, only in saver diff: {len(only_got)}, differing values: {len(diff_vals)}')
    if len(tsv) != len(exp_ch):
        findings.append(f'diff.tsv has {len(tsv)} lines, independent comparison finds {len(exp_ch)} changed cells')
    if any(not line.split('\t')[-1] or line.split('\t')[-1] == 'NOT_ALLOWED' for line in tsv):
        findings.append('diff.tsv contains a NOT_ALLOWED line')
    for k in only_exp[:20]:
        print('    only in STAGED diff:', k, exp_ch[k])
    for k in only_got[:20]:
        print('    only in saver diff:', k, got_ch[k])
    findings += [f'change only in STAGED: {k}' for k in only_exp] + [f'change only in saver output: {k}' for k in only_got]
    findings += [f'change value differs: {k}: {exp_ch[k]} vs {got_ch[k]}' for k in diff_vals]
    changed = [(k, v) for k, v in exp_ch.items() if v[0] == 'changed']
    print(f'    changed (non-blank -> different) cells in STAGED diff: {len(changed)}; expected 18 per runsave_changes_2026-10-30.csv')

    # 3. the pipeline results
    print('\n[3] result JSON')
    for name in ('result.json', 'result2.json'):
        exp = json.loads((fx / name).read_text(encoding='utf-8'))
        got = json.loads((out / name).read_text(encoding='utf-8'))
        dd = walk_diff(exp, got)
        documented = [d for d in dd if d[0] in DOCUMENTED_JSON.get(name, set())]
        rest = [d for d in dd if d not in documented]
        print(f'    {name}: {len(dd)} differences, {len(documented)} documented timestamp fields, {len(rest)} other')
        for path, x, y in rest[:25]:
            print('       ', '/'.join(map(str, path)), '|', str(x)[:80], '|', str(y)[:80])
        findings += [f'{name}: {"/".join(map(str, path))}: {str(x)[:60]} vs {str(y)[:60]}' for path, x, y in rest]

    # 3b. pipeline state files the run rewrites (compared with the fixture's post-run copies)
    for name in ('release_related.json', 'release_texts.json', 'gabriel_bills_leginfo.json'):
        dd = walk_diff(json.loads((fx / 'pipeline' / name).read_text(encoding='utf-8')), json.loads((out / 'pipeline' / name).read_text(encoding='utf-8')))
        print(f'    pipeline/{name}: {len(dd)} differences')
        for path, x, y in dd[:10]:
            print('       ', '/'.join(map(str, path)), '|', str(x)[:80], '|', str(y)[:80])
        findings += [f'pipeline/{name}: {"/".join(map(str, path))}: {str(x)[:60]} vs {str(y)[:60]}' for path, x, y in dd]
    for name in ('lookup_cache.out.json',):
        if (out / name).read_bytes() != (fx / name).read_bytes():
            findings.append(f'{name} differs')
    for rel in ('articles/2020.json', 'articles/2026.json', 'articles/manifest.json'):
        if (out / 'copies_out' / rel).read_bytes() != (fx / 'copies_out' / rel).read_bytes():
            findings.append(f'copies_out/{rel} differs')

    # 4. pages
    dp = dirs_diff(fx / 'pages', out / 'pages')
    print(f'\n[4] pages: {len(dp)} differences')
    for d in dp[:20]:
        print('   ', d)
    findings += [f'pages: {d}' for d in dp]

    # 5. no network, nothing written outside the work folder's out/ and state/
    ph = res.get('photos', {})
    print(f"\n[5] photo fetch attempts blocked offline: {ph.get('fetch_attempts_blocked_offline')}")
    if ph.get('fetch_attempts_blocked_offline'):
        findings.append(f"{ph['fetch_attempts_blocked_offline']} photo fetches were needed that the image cache did not hold")
    stray = [q.relative_to(work).as_posix() for q in work.rglob('*') if q.is_file() and q.relative_to(work).parts[0] not in ('out', 'state')
             and q.stat().st_mtime > t0 and q.relative_to(work).parts[0] not in ('master', 'db', 'queue', 'pipeline', 'copies', 'img_cache_in', 'library', 'backups')]
    changed_inputs = []
    for d in ('db', 'queue', 'pipeline', 'copies', 'img_cache_in', 'library', 'backups', 'master'):
        for q in (work / d).rglob('*'):
            if q.is_file() and q.stat().st_mtime > t0:
                changed_inputs.append(q.relative_to(work).as_posix())
    print(f'[6] input files modified or created by preview: {len(changed_inputs)} {changed_inputs[:5]}')
    findings += [f'input modified: {x}' for x in changed_inputs]

    print(f'\n{"MATCHED" if not findings else "FINDINGS: " + str(len(findings))}')
    for f in findings[:60]:
        print('  -', f)
    (work / 'replay_findings.json').write_text(json.dumps(findings, indent=1), encoding='utf-8')
    return 0 if not findings else 1


if __name__ == '__main__':
    sys.exit(main())
