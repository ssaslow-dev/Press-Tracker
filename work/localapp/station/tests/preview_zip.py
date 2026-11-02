#!/usr/bin/env python3
"""Run a station zip through the PC side's inspect + saver preview on a COPY of the snapshot workbook, in a scratch app folder
(same set-up as the updatefolder tests ThroughSaver but on the real snapshot workbook: build_data stubbed, empty library and copies).
Nothing is saved; preview writes nothing to the workbook. Usage: python3 -I tests/preview_zip.py ZIP WORKBOOK SCRATCH TODAY"""
import json, shutil, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
UF = REPO / 'work' / 'localapp' / 'updatefolder'
sys.path.insert(0, str(UF))
import take_update as TU  # noqa: E402
from layout import PCLayout  # noqa: E402

zp, wb, scratch, today = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
SAVER = REPO / 'work' / 'saver' / 'src' / 'saver.py'
shutil.rmtree(scratch, ignore_errors=True)
app = scratch / 'app'; lay = PCLayout(app)
lay.workbook.parent.mkdir(parents=True); shutil.copy2(wb, lay.workbook)
import os
REAL = os.environ.get('PIPE_REAL')   # a folder with code/*.py,json,csv + sid_map.json + insights/ + legacy_index.html: the real build_data and relmatch run
if REAL:
    shutil.copytree(REAL, lay.pipeline)
else:
  shutil.copytree(REPO / 'code', lay.pipeline, ignore=shutil.ignore_patterns('docs', '__pycache__', '*.pyc', '_history', 'tracker', 'fetch2', 'billstatus', 'fetch_rated1'))
if not REAL:
  (lay.pipeline / 'build_data.py').write_text("import sys, os\nos.makedirs(sys.argv[3], exist_ok=True)\nfor n in ('data', 'rows', 'idmap', 'covcols'):\n    open(os.path.join(sys.argv[3], n + '.json'), 'w').write('{}')\n")
# relmatch.py stays real: reltab imports it
subprocess.run([sys.executable, '-I', str(REPO / 'work' / 'saver' / 'tools' / 'pipeline_sha.py'), str(lay.pipeline)], check=True, capture_output=True)
(lay.copies / 'articles').mkdir(parents=True); (lay.copies / 'articles' / 'manifest.json').write_text('{"articles":{}}')
lay.library.mkdir(parents=True)
r = TU.init_baseline(lay, saver=SAVER); print('init', r.get('exit_code'))
ins = TU.inspect_update(zp, lay); print('inspect proceed', ins['proceed'], ins['fingerprint']['status'], 'runs', ins['runs'], 'files', ins['files'])
pv = TU.preview(lay, ins['update_id'], saver=SAVER, today=today)
print('preview exit', pv.get('exit_code'), 'refusal', pv.get('refusal'))
print(json.dumps(pv.get('diff', {}), indent=1)[:3000])
