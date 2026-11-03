#!/usr/bin/env python3
"""Build the tracker page for the local app from the snapshot workbook (LOCALAPP-v1, plan step 3).

Does NOT touch code/, build/ or data/ in the repository: it copies what the build scripts need into a staging root
(OUT/stage) laid out the way code/apply_all_patches.py and build/build.sh expect, adds the pieces the repo lacks (the page
shell, sid_map, legacy page, outlets tab, insights views: work/localapp/vendor/live_<version>/), and runs the repo's own
scripts there. Python 3.11+, pandas + openpyxl + beautifulsoup4 needed (the same as the pipeline). Run with:

    python3 -I work/localapp/build/build_tracker.py --out DIR [--xlsx FILE] [--legacy FILE] [--live-site DIR]

Outputs (in OUT/site/, ready to serve with a static server):
    index.html                      the tracker page (PIPELINE build = what the live tracker publishes)
    data/sheet.json                 {"filename", "b64"}: the workbook, for the page's download button (written by this script)
    data/release_texts.json         copy of code/release_texts.json (the pipeline file; the live page fetches it at runtime)
    articles/, img/, copies/        ONLY with --live-site: copied from a folder of files fetched read-only from the live
                                    tracker. They cannot be rebuilt here (see README.md). Without it, the page still loads;
                                    saved copies show as missing.
Also OUT/stage/work/build_last/ (build.sh output: lib/ and pipe/ builds, logs, block comparison).
"""
import argparse, base64, hashlib, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
VENDOR_DEFAULT = os.path.join(REPO, 'work', 'localapp', 'vendor')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def run(cmd, cwd, env=None, log=None):
    print('  $', ' '.join(cmd))
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    if log:
        open(log, 'w', encoding='utf-8').write(r.stdout + r.stderr)
    if r.returncode:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit(f'failed ({r.returncode}): {" ".join(cmd)}')
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True, help='output folder (created; an existing stage/ and site/ in it are replaced)')
    ap.add_argument('--xlsx', default=os.path.join(REPO, 'data', 'AJG Coverage - NewsBank.xlsx'), help='workbook to build from (read only)')
    ap.add_argument('--vendor', default=None, help='vendor/live_<version> folder (default: the newest under work/localapp/vendor)')
    ap.add_argument('--legacy', default=None,
                    help='legacy_index.html (the old published page: build_data reads its "data" block for fallback fields). It holds '
                         'translated story text, so it is not in the repository; default: vendor/pipeline/legacy_index.html if present')
    ap.add_argument('--live-site', default=None, help='folder with articles/, img/, copies/ fetched read-only from the live tracker')
    a = ap.parse_args()

    vendor = a.vendor
    if not vendor:
        cands = sorted(d for d in os.listdir(VENDOR_DEFAULT) if d.startswith('live_'))
        if not cands:
            raise SystemExit('no vendor/live_* folder')
        vendor = os.path.join(VENDOR_DEFAULT, cands[-1])
    vp = os.path.join(vendor, 'pipeline')
    legacy = a.legacy or os.path.join(vp, 'legacy_index.html')
    if not os.path.exists(legacy):
        raise SystemExit(f'legacy_index.html not found ({legacy}); pass --legacy FILE (fetched from the live tracker pipeline/)')
    for need in ('shell.html', 'sid_map.json', os.path.join('tabs', 'outlets.js'), os.path.join('insights', 'bill_timeline.js')):
        if not os.path.exists(os.path.join(vp, need)):
            raise SystemExit(f'missing vendor file {os.path.join(vp, need)}')
    out = os.path.abspath(a.out)
    stage, site = os.path.join(out, 'stage'), os.path.join(out, 'site')
    for d in (stage, site):
        shutil.rmtree(d, ignore_errors=True)
    os.makedirs(stage)
    print('staging root', stage)

    # 1. staging root = the layout the repo scripts expect (L = repo root of the old workspace)
    ign = shutil.ignore_patterns('__pycache__', '*.pyc', '_history')
    shutil.copytree(os.path.join(REPO, 'code'), os.path.join(stage, 'code'), ignore=ign)
    os.makedirs(os.path.join(stage, 'build'))
    for f in ('build.sh', 'clean_playbook.md'):
        cp(os.path.join(REPO, 'build', f), os.path.join(stage, 'build', f))
    shutil.copytree(os.path.join(REPO, 'build', 'tabs'), os.path.join(stage, 'build', 'tabs'), ignore=ign)
    # docs/ at the root: the PIPELINE map reads README.md, DECISIONS.md, CONTRACT.md, TONE_GUIDE.md from the root
    for f in ('DECISIONS.md', 'CONTRACT.md', 'TONE_GUIDE.md'):
        cp(os.path.join(REPO, 'docs', f), os.path.join(stage, f))
    cp(os.path.join(REPO, 'README.md'), os.path.join(stage, 'README.md'))
    # pieces the repo lacks, from the live tracker (vendor/)
    cp(os.path.join(vp, 'shell.html'), os.path.join(stage, 'build', 'shell', 'shell.html'))
    cp(os.path.join(vp, 'sid_map.json'), os.path.join(stage, 'work', 'sid_map.json'))
    cp(legacy, os.path.join(stage, 'work', 'index_original.html'))
    for f in ('outlets.js', 'outlets_data.py'):
        cp(os.path.join(vp, 'tabs', f), os.path.join(stage, 'build', 'tabs', f))
    for f in sorted(os.listdir(os.path.join(vp, 'insights'))):
        if f == 'bill_milestones.json':
            cp(os.path.join(vp, 'insights', f), os.path.join(stage, 'work', 'out', f))
        else:
            cp(os.path.join(vp, 'insights', f), os.path.join(stage, 'build', 'insights', f))
    xlsx = os.path.join(stage, 'work', 'coverage_current.xlsx')
    cp(a.xlsx, xlsx)
    print('workbook copy sha256', sha(xlsx))

    # 2. the repo's own steps, in the staging root
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    run([sys.executable, '-I', 'code/apply_all_patches.py', '--root', stage], stage, env, os.path.join(out, 'apply_all.log'))
    # the live pipeline folder also ships legacy_index.html (build_data's OLDHTML input; apply_all does not copy it)
    cp(legacy, os.path.join(stage, 'build', 'pub', 'pipeline', 'legacy_index.html'))
    env.update(XLSX=xlsx, BASE=os.path.join(stage, 'build', 'shell', 'shell.html'), OUT=os.path.join(stage, 'work', 'build_last'))
    txt = run(['bash', 'build/build.sh'], stage, env, os.path.join(out, 'build_sh.log'))
    print(txt.strip())

    # 3. the site folder
    os.makedirs(site)
    page = os.path.join(stage, 'work', 'build_last', 'pipe_index.html')
    cp(page, os.path.join(site, 'index.html'))
    os.makedirs(os.path.join(site, 'data'))
    with open(xlsx, 'rb') as f:   # same shape the live page reads (21_manage_badge.js): {filename, b64}
        sj = {'filename': 'AJG Coverage - NewsBank.xlsx', 'b64': base64.b64encode(f.read()).decode('ascii')}
    with open(os.path.join(site, 'data', 'sheet.json'), 'w', encoding='utf-8') as f:
        json.dump(sj, f)   # default separators = byte-identical to the live data/sheet.json
    cp(os.path.join(stage, 'build', 'pub', 'pipeline', 'release_texts.json'), os.path.join(site, 'data', 'release_texts.json'))
    if a.live_site:
        for d in ('articles', 'img', 'copies'):
            src = os.path.join(a.live_site, d)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(site, d))
    print('site', site, 'index.html', os.path.getsize(os.path.join(site, 'index.html')), 'bytes sha256', sha(os.path.join(site, 'index.html')))


if __name__ == '__main__':
    main()
