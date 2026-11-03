"""PROQUESTPDF-v1 answer 2 (patch proposal 06, not wired in): with patches/06 applied to a copy of code/sheet_task.py and the station's data/proquest_outlets.json beside it,
norm_outlet reads a ProQuest outlet name and the sheet's NewsBank name as one outlet. Needs the `patch` program (skipped without it)."""
import os, shutil, subprocess, sys, tempfile, unittest, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))


def load(code_dir):
    spec = importlib.util.spec_from_file_location('sheet_task_pq', os.path.join(code_dir, 'sheet_task.py'))
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, code_dir)
    try:
        spec.loader.exec_module(m)
    finally:
        sys.path.remove(code_dir)
    return m


@unittest.skipUnless(shutil.which('patch'), 'the patch program is not installed')
class T(unittest.TestCase):
    def test_patch(self):
        with tempfile.TemporaryDirectory() as t:
            os.makedirs(os.path.join(t, 'code'))
            for f in ('sheet_task.py', 'outlet_rules.json'):
                shutil.copy(os.path.join(REPO, 'code', f), os.path.join(t, 'code', f))
            for f in os.listdir(os.path.join(REPO, 'code')):
                if f.endswith('.py') and f != 'sheet_task.py':
                    shutil.copy(os.path.join(REPO, 'code', f), os.path.join(t, 'code', f))
            before = load(os.path.join(t, 'code'))
            self.assertNotEqual(before.norm_outlet('The Center Square'), before.norm_outlet('Center Square California, The'))
            for p in ('01_sheet_task_nbpdf.patch', '04_sheet_task_pqpdf.patch', '06_sheet_task_pq_outlet_aliases.patch'):
                r = subprocess.run(['patch', '-p1', '-i', os.path.join(REPO, 'work', 'localapp', 'newsbank_pc', 'patches', p)], cwd=t, capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, p + r.stdout + r.stderr)
            shutil.copy(os.path.join(REPO, 'work', 'localapp', 'station', 'data', 'proquest_outlets.json'), os.path.join(t, 'code', 'proquest_outlets.json'))
            after = load(os.path.join(t, 'code'))
            n = after.norm_outlet
            self.assertEqual(n('The Center Square'), n('Center Square California, The'))
            self.assertNotEqual(n('The Center Square'), n('Center Square Texas, The'))   # keep_separate still holds
            self.assertEqual(n('Los Angeles Times'), before.norm_outlet('Los Angeles Times'))
            os.remove(os.path.join(t, 'code', 'proquest_outlets.json'))
            self.assertNotEqual(load(os.path.join(t, 'code')).norm_outlet('The Center Square'), n('Center Square California, The'))   # no data file = unchanged behaviour


if __name__ == '__main__':
    unittest.main()
