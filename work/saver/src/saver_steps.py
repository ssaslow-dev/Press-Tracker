"""saver_steps.py: the subprocess calls of the manual procedure (sheet_task_prompt.md step 3) with their exact flags, the pipeline
checksum check, and read-only helpers that take rule data from sheet_task.py's SOURCE (ast, nothing is executed or copied).

Nothing here touches the network. Every pipeline script runs as [sys.executable, "-I", script, ...] with cwd = the working folder O
(the parent of O/pipeline), the way the prompt runs them from its working folder."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PIPELINE_SHA = 'PIPELINE.sha256'
DEAD_PROXY = 'http://127.0.0.1:9'    # nothing listens on the discard port: a fetch attempt fails at once
PROXY_VARS = ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy')


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- reading rule data from sheet_task.py without running it


def read_sheet_task_constants(path, names=('VT_DERIVED_REL', 'VT_NEW_OK')) -> dict:
    """literal module-level assignments of sheet_task.py, by ast (the file is not imported). Raises KeyError if one is missing or not a literal."""
    tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in names:
            found[node.targets[0].id] = ast.literal_eval(node.value)
    missing = [n for n in names if n not in found]
    if missing:
        raise KeyError(f'sheet_task.py has no literal {missing}')
    return found


def load_pure_functions(path, names=('sheet_applied', 'run_done')) -> dict:
    """the named module-level functions of sheet_task.py, compiled alone (they use builtins only). The rule stays in sheet_task.py."""
    tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    wanted = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in wanted} != set(names):
        raise KeyError(f'sheet_task.py lacks {sorted(set(names) - {n.name for n in wanted})}')
    ns: dict = {}
    exec(compile(ast.Module(body=wanted, type_ignores=[]), str(path), 'exec'), ns)   # noqa: S102 (our own pipeline file, builtins only)
    return {n: ns[n] for n in names}


# ---------------------------------------------------------------- pipeline folder


def read_pipeline_sha(folder) -> dict:
    """{posix relative path: sha} from PIPELINE.sha256 ("<sha>  <path>" per line, sha256sum style). FileNotFoundError if absent."""
    out = {}
    for line in (Path(folder) / PIPELINE_SHA).read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        sha, _, rel = line.partition(' ')
        out[rel.strip().lstrip('*').strip()] = sha.strip()
    return out


def verify_pipeline(folder) -> dict:
    """{'missing': [...], 'mismatch': [...], 'n': count}; never raises for a bad file, only for an absent PIPELINE.sha256"""
    listed = read_pipeline_sha(folder)
    missing, bad = [], []
    for rel, sha in listed.items():
        p = Path(folder).joinpath(*rel.split('/'))
        if not p.is_file():
            missing.append(rel)
        elif sha256_file(p) != sha:
            bad.append(rel)
    return {'missing': missing, 'mismatch': bad, 'n': len(listed)}


def copy_pipeline(src, dest) -> None:
    """copy exactly the files PIPELINE.sha256 lists (plus the list); an unlisted file never reaches the run"""
    src, dest = Path(src), Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for rel in list(read_pipeline_sha(src)) + [PIPELINE_SHA]:
        t = dest.joinpath(*rel.split('/'))
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src.joinpath(*rel.split('/')), t)


# ---------------------------------------------------------------- running scripts


def offline_env() -> dict:
    """the environment for every pipeline subprocess: proxies point at a dead port so the one network user in the pipeline
    (img_embed.fetch_one, photos of new saves, cache first) cannot reach anything. NO_PROXY is removed so nothing bypasses the dead proxy."""
    env = dict(os.environ)
    for k in PROXY_VARS:
        env[k] = DEAD_PROXY
    for k in ('NO_PROXY', 'no_proxy', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE', 'SSL_CERT_FILE'):
        env.pop(k, None)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return env


class Step:
    def __init__(self, label, rc, out, err):
        self.label, self.rc, self.out, self.err = label, rc, out, err

    def tail(self, n=600):
        return (self.err or self.out or '')[-n:]


def run_script(work: Path, script: str, args: list, label: str, logdir: Path, env=None, timeout=3600) -> Step:
    cmd = [sys.executable, '-I', script] + [str(a) for a in args]
    p = subprocess.run(cmd, cwd=str(work), env=env or offline_env(), capture_output=True, text=True, encoding='utf-8', errors='replace',
                       timeout=timeout)
    logdir.mkdir(parents=True, exist_ok=True)
    (logdir / f'{label}.stdout').write_text(p.stdout, encoding='utf-8')
    (logdir / f'{label}.stderr').write_text(p.stderr, encoding='utf-8')
    (logdir / f'{label}.cmd').write_text(' '.join(cmd) + f'\nexit {p.returncode}\n', encoding='utf-8')
    return Step(label, p.returncode, p.stdout, p.stderr)


def json_of(step: Step):
    """the JSON value a pipeline script printed (whole stdout, else the last JSON-looking line)"""
    try:
        return json.loads(step.out)
    except ValueError:
        for line in reversed(step.out.strip().splitlines()):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return None


def check_only(work, db_args, logdir):
    """sheet_task --check-only: rc 0 = work, 3 = nothing queued"""
    return run_script(work, 'pipeline/sheet_task.py', db_args + ['--check-only'], 'check_only', logdir)


def copies_needed(work, db_json, logdir):
    return run_script(work, 'pipeline/sheet_task.py', ['--db', db_json, '--xlsx', 'in.xlsx', '--copies-needed'], 'copies_needed', logdir)


def release_candidates(work, db_json, logdir):
    return run_script(work, 'pipeline/sheet_task.py', ['--db', db_json, '--xlsx', 'in.xlsx', '--release-candidates'], 'release_candidates', logdir)


def pass1_args(*, today, queue=None, idmap=None, library=None, img_cache=True, lookup_cache=True) -> list:
    """the prompt's main run, flag for flag, plus LEARN-v1's lookup cache flags and the optional --queue / --idmap / --library"""
    a = ['--db', 'db.json', '--xlsx', 'in.xlsx', '--out', 'out1.xlsx', '--result', 'result.json', '--pages-dir', 'pages',
         '--copies', 'copies', '--copies-out', 'copies_out']
    if img_cache:
        a += ['--img-cache', 'img_cache']
    a += ['--bills', 'pipeline/gabriel_bills_leginfo.json', '--release-texts', 'pipeline/release_texts.json',
          '--release-related', 'pipeline/release_related.json']
    if queue:
        a += ['--queue', queue]
    if idmap:
        a += ['--idmap', idmap]
    if library:
        a += ['--library', library]
    if lookup_cache:
        a += ['--lookup-cache', 'pipeline/lookup_cache.json', '--lookup-cache-out', 'lookup_cache.out.json']
    return a + ['--today', today]


def build_data_args() -> list:
    return ['out1.xlsx', 'pipeline/legacy_index.html', 'blocks/', 'pipeline/sid_map.json']


def merge_copies_out(work: Path) -> list:
    """RELBUTTON-v1: "copy copies_out/ over copies/articles/". copies_out holds articles/<file>; the changed shards go INTO
    copies/articles/ (the manual run of 2026-10-30 copied the folder itself and left a nested copies/articles/articles/; see README finding)."""
    done = []
    src, dst = work / 'copies_out' / 'articles', work / 'copies' / 'articles'
    if os.environ.get('SAVER_TEST_COPIES_OUT_LITERAL') == '1':   # test hook: reproduce the manual run's nested copy (diagnostics only)
        dst = dst / 'articles'
    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(src.iterdir()):
            if f.is_file():
                shutil.copy2(f, dst / f.name)
                done.append(f.name)
    return done


def relmatch_args(result: dict):
    """None when result.relmatch names nothing; otherwise the prompt's relmatch flags (a flag whose list is empty is left out)"""
    rm = result.get('relmatch') or {}
    rel, sto = rm.get('releases') or [], rm.get('stories') or []
    if not rel and not sto:
        return None
    a = ['--data', 'blocks/data.json', '--pickup', 'blocks/ins_release_pickup.json', '--release-texts', 'pipeline/release_texts.json',
         '--articles', 'copies/articles', '--update', 'pipeline/release_related.json', '--json', 'pipeline/release_related.json']
    if rel:
        a += ['--releases', ','.join(str(x) for x in rel)]
    if sto:
        a += ['--stories', ','.join(str(x) for x in sto)]
    return a


def pass2_args(*, today, out_name) -> list:
    return ['--after-relmatch', 'pipeline/release_related.json', '--xlsx', 'out1.xlsx', '--out', out_name, '--result', 'result2.json',
            '--prev-result', 'result.json', '--pages-dir', 'pages', '--copies', 'copies', '--bills', 'pipeline/gabriel_bills_leginfo.json',
            '--today', today]
