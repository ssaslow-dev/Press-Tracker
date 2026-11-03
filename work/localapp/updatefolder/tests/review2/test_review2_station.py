"""Independent review tests for the PC station layer around the update folder (REVIEW_2.md, checkpoint 3). A FAILING test is a finding.

Run:  cd work/localapp/updatefolder && python3 -I -m unittest discover -s tests/review2 -t tests/review2 -v

These tests import the station code from work/localapp/app/src/station directly (the assembled app puts the same files under app/station)."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
UF = HERE.parent.parent                                  # work/localapp/updatefolder
LOCALAPP = UF.parent
REPO = LOCALAPP.parent.parent
for p in (UF, REPO / 'work' / 'saver' / 'src', LOCALAPP / 'server', LOCALAPP / 'app' / 'src' / 'station'):
    sys.path.insert(0, str(p))

import station_cli as CLI       # noqa: E402
from layout import PCLayout     # noqa: E402


def inside(path: str, root: Path) -> bool:
    try:
        q = Path(path).resolve()
    except (OSError, TypeError):
        return False
    return q == root or root in q.parents


class ChildTempFolder(unittest.TestCase):
    """GOVIT-v1: on the office PC the program reads and writes only inside its own folder. station_cli.boot() points the station's own
    temporary files at data/tmp (tempfile.tempdir), but that setting is per process. The save program and sheet_task run as children, and
    openpyxl writes every worksheet it saves to a temporary file in the SYSTEM temp folder (openpyxl/worksheet/_writer.py
    create_temporary_file -> tempfile.NamedTemporaryFile) unless TMP / TEMP / TMPDIR say otherwise. The shim that starts those children
    sets AJG_NO_NETWORK and AJG_LINK_PHOTOS but no temp folder, so each save writes (and removes) files under %TEMP%, outside the app folder."""

    def captured_env(self, run_with):
        root = Path(tempfile.mkdtemp()) / 'AJG Tracker'
        (root / 'data' / 'tmp').mkdir(parents=True)
        lay = PCLayout(root)
        seen = {}
        real = subprocess.run

        def fake_run(cmd, *a, **kw):
            seen['env'] = kw.get('env')
            seen['cmd'] = list(cmd)

            class R:
                returncode, stdout, stderr = 0, '{}', ''
            return R()
        subprocess.run = fake_run
        try:
            run_with(lay)
        finally:
            subprocess.run = real
        return root, seen

    def test_children_started_by_the_shim_get_a_temp_folder_inside_the_app(self):
        def go(lay):
            CLI.boot(lay)
            CLI._SubprocessShim().run([sys.executable, '-I', 'x.py'], capture_output=True)
        root, seen = self.captured_env(go)
        env = seen['env'] or {}
        for k in ('TMP', 'TEMP', 'TMPDIR'):
            self.assertTrue(inside(env.get(k, ''), root), f'{k} is not set to a folder inside the app folder for the save program and sheet_task: {env.get(k)!r}')

    def test_children_started_by_py_get_a_temp_folder_inside_the_app(self):
        def go(lay):
            CLI.boot(lay)
            CLI.py(['x.py'], cwd=lay.root)
        root, seen = self.captured_env(go)
        env = seen['env'] or {}
        for k in ('TMP', 'TEMP', 'TMPDIR'):
            self.assertTrue(inside(env.get(k, ''), root), f'{k} is not set to a folder inside the app folder for build_data / assemble: {env.get(k)!r}')


if __name__ == '__main__':
    unittest.main()
