"""Run the saver test suite against the pinned package set only (Linux wheels of the same versions as requirements-win.txt).
  python3 -I run_pinned_tests.py PINNED_SITE_DIR [--import-pipeline]
PINNED_SITE_DIR is made with:  pip install --target DIR --no-deps --only-binary=:all: <the ten pins>
It goes first on sys.path, and imports of everything the PC will not have (requests, PIL, cairosvg, langdetect, pytest, lxml,
pdfminer, chardet, charset_normalizer, certifi, urllib3, idna) fail, to show nothing else is needed. Prints the packages' versions."""
import importlib, importlib.abc, os, sys, unittest

BLOCKED = {'requests', 'PIL', 'cairosvg', 'cairocffi', 'langdetect', 'pytest', 'lxml', 'pdfminer', 'chardet', 'charset_normalizer',
           'certifi', 'urllib3', 'idna', 'six', 'scipy', 'matplotlib', 'jinja2', 'cryptography', 'html5lib'}
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))


class Blocker(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name.split('.')[0] in BLOCKED:
            raise ImportError('blocked (not in the PC package set): ' + name)
        return None


def main():
    site = os.path.abspath(sys.argv[1])
    sys.path.insert(0, site)
    sys.meta_path.insert(0, Blocker())
    # drop user/system site-packages so only the pinned folder (plus stdlib) can supply third-party code
    sys.path[:] = [p for p in sys.path if 'site-packages' not in p and 'dist-packages' not in p or os.path.abspath(p) == site]
    for m in ('openpyxl', 'bs4', 'soupsieve', 'pypdf', 'pandas', 'numpy', 'dateutil', 'tzdata', 'et_xmlfile', 'typing_extensions'):
        mod = importlib.import_module(m)
        assert os.path.abspath(mod.__file__).startswith(site), (m, mod.__file__)
        print('%-18s %-12s %s' % (m, getattr(mod, '__version__', getattr(mod, 'IANA_VERSION', '')), os.path.relpath(mod.__file__, site)))
    if '--import-pipeline' in sys.argv:
        code = os.path.join(REPO, 'code')
        sys.path.insert(0, code)
        bad = []
        for n in ('sheet_task', 'build_data_NOIMPORT', 'relmatch', 'clean_html', 'reprint_rule', 'release_rule', 'media_gate', 'img_embed',
                  'av_display_clean', 'avtab', 'dates_lib', 'date_rules', 'reltab', 'relpage', 'relcopy', 'copy_check', 'shownet', 'reporters',
                  'authorsplit', 'billmatch', 'lookup_cache', 'wireblend', 'tabs_assemble', 'insights_assemble'):
            if n.endswith('_NOIMPORT'):
                continue
            try:
                importlib.import_module(n)
            except SystemExit as e:
                bad.append((n, 'SystemExit %s' % (e,)))
            except Exception as e:
                bad.append((n, repr(e)[:160]))
        print('pipeline import check: %d modules, failures: %s' % (24, bad or 'none'))
    os.chdir(os.path.join(REPO, 'work', 'saver'))
    sys.path.insert(0, os.path.join(REPO, 'work', 'saver', 'tests'))
    suite = unittest.defaultTestLoader.discover('tests', top_level_dir='tests')
    res = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
