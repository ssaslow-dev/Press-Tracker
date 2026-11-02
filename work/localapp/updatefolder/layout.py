"""The PC folder layout (FORMAT.md section 3). Everything lives inside one app folder (GOVIT-v1: read and write only inside it).

    <app>/
      pipeline/                  published pipeline files + PIPELINE.sha256 (+ insights/release_pickup_data.py, sid_map.json); never written
      saver/saver.py ...         the save program (work/saver/src); never written
      data/
        workbook/AJG Coverage - NewsBank.xlsx
        library/<year>/ ...      article library (add-only)
        backups/                 saver backups
        state/                   ledger.jsonl, logs/, saver.lock
        copies/articles/         manifest.json + year shards (read by the save)
        db/<collection>/<id>.json   the tracker's own store (notes, views, edits, runs ...)
        queue/                   review queue (items/ decisions/ applied/), optional
        for_update/              files made by make_for_update.py
        updates/staging/<id>/    an unpacked update (manifest.json + db/)
        updates/work/<id>/       saver outputs (preview-1, save-1 ...)
        updates/done/<id>/       finished updates (the zip is copied here, staging moved here)
        updates/rejected/<id>/   refused updates (kept for a look; never deleted)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_WORKBOOK = 'AJG Coverage - NewsBank.xlsx'


class OutsideAppFolder(ValueError):
    pass


@dataclass
class PCLayout:
    root: Path
    workbook_name: str = DEFAULT_WORKBOOK
    # optional overrides, relative to root (layout.json at the app root may set them)
    overrides: dict | None = None

    def __post_init__(self):
        self.root = Path(self.root).resolve()
        lj = self.root / 'layout.json'
        ov = dict(self.overrides or {})
        if lj.is_file() and not self.overrides:
            ov = json.loads(lj.read_text(encoding='utf-8'))
        self.overrides = ov
        self.workbook_name = ov.get('workbook_name', self.workbook_name)

    def _p(self, key: str, default: str) -> Path:
        rel = (self.overrides or {}).get(key, default)
        p = (self.root / rel).resolve()
        if p != self.root and self.root not in p.parents:
            raise OutsideAppFolder(f'{key} = {rel!r} points outside the app folder')
        return p

    @property
    def data(self): return self._p('data', 'data')
    @property
    def workbook(self): return self._p('workbook', f'data/workbook/{self.workbook_name}')
    @property
    def library(self): return self._p('library', 'data/library')
    @property
    def backups(self): return self._p('backups', 'data/backups')
    @property
    def state(self): return self._p('state', 'data/state')
    @property
    def pipeline(self): return self._p('pipeline', 'pipeline')
    @property
    def copies(self): return self._p('copies', 'data/copies')
    @property
    def db(self): return self._p('db', 'data/db')
    @property
    def queue(self): return self._p('queue', 'data/queue')
    @property
    def for_update(self): return self._p('for_update', 'data/for_update')
    @property
    def updates(self): return self._p('updates', 'data/updates')
    @property
    def saver(self): return self._p('saver', 'saver/saver.py')

    def inside(self, p) -> Path:
        """Resolve p and require it to be inside the app folder."""
        q = Path(p).resolve()
        if q != self.root and self.root not in q.parents:
            raise OutsideAppFolder(f'{p} is outside the app folder {self.root}')
        return q
