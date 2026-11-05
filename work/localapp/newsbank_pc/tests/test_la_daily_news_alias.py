"""N17: "Daily News of Los Angeles" (how NewsBank spells it; the station already maps it) is one outlet with "Los Angeles Daily News" in the save's outlet rules
(code/outlet_rules.json aliases). Runs the real sheet_task.norm_outlet on a copy of code/."""
import importlib.util, os, shutil, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))


class T(unittest.TestCase):
    def test_alias(self):
        with tempfile.TemporaryDirectory() as t:
            for f in os.listdir(os.path.join(REPO, 'code')):
                p = os.path.join(REPO, 'code', f)
                if os.path.isfile(p) and f.endswith(('.py', '.json', '.csv')):
                    shutil.copy(p, os.path.join(t, f))
            spec = importlib.util.spec_from_file_location('sheet_task_alias', os.path.join(t, 'sheet_task.py'))
            m = importlib.util.module_from_spec(spec)
            sys.path.insert(0, t)
            try:
                spec.loader.exec_module(m)
            finally:
                sys.path.remove(t)
            a, b = m.norm_outlet('Daily News of Los Angeles'), m.norm_outlet('Los Angeles Daily News')
            self.assertEqual(a, b)
            self.assertEqual(b, 'los angeles daily news')
            self.assertEqual(m.norm_outlet('Daily News of Los Angeles', 'Los Angeles'), b)
            self.assertNotEqual(m.norm_outlet('Daily News'), 'x')       # an unrelated generic name is not touched
            self.assertNotEqual(m.norm_outlet('New York Daily News'), b)


if __name__ == '__main__':
    unittest.main()
