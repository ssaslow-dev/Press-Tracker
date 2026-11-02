#!/usr/bin/env python3
"""Check a zip made by the station with the PC side's own code (work/localapp/updatefolder): the reference checker, then take_update.py inspect
on a COPY of the workbook in a scratch app folder. Usage: python3 -I tests/verify_zip.py ZIP WORKBOOK_COPY SCRATCH_DIR"""
import json, shutil, subprocess, sys, zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
UF = REPO / 'work' / 'localapp' / 'updatefolder'
sys.path.insert(0, str(UF))
import formats as F  # noqa: E402

zp, wb, scratch = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
with zipfile.ZipFile(zp) as z:
    infos = F.scan_zip(z, zp.stat().st_size)
    entries, man = {}, None
    for i in infos:
        b = F.read_entry(z, i)
        if i.filename == 'manifest.json':
            man = json.loads(b)
        else:
            entries[i.filename] = b
    F.check_manifest(man, entries)
print('reference checker: ok;', len(entries), 'files;', 'runs', man['runs'], ';source', man['source']['workbook_sha256'][:8])
app = scratch / 'app'
(app / 'data' / 'workbook').mkdir(parents=True, exist_ok=True)
shutil.copy2(wb, app / 'data' / 'workbook' / wb.name)
p = subprocess.run([sys.executable, '-I', str(UF / 'take_update.py'), 'inspect', '--app-root', str(app), '--zip', str(zp)], capture_output=True, text=True)
print(p.stdout[-1500:], p.stderr[-800:], 'exit', p.returncode)
sys.exit(p.returncode)
