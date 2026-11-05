"""PREVIEW-v1: the PC tracker's page, made from a fresh page build without a full assembly.
python3 -I prep_page.py PAGEBUILD_DIR OUT_SITE_DIR
Applies to PAGEBUILD/site/index.html the same three page patches assemble_app.py applies to the PC page (photolink viewer patch, local fonts, TIDY-v1
layout fixes), copies the fonts folder, and the article manifest, into OUT_SITE_DIR (index.html, fonts/, articles/manifest.json)."""
import shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import assemble_app as A

pb, out = Path(sys.argv[1]), Path(sys.argv[2])
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)
idx = out / 'index.html'
A.patched_copy(pb / 'site' / 'index.html', idx, A.HERE / 'patches' / '06_tracker_js_photolink.patch')
A.patch_index_fonts(idx)
A.patch_index_tidy(idx)
shutil.copytree(A.FONTS_SRC, out / 'fonts', ignore=shutil.ignore_patterns('*.json'))
m = pb / 'site' / 'articles' / 'manifest.json'
if m.is_file():
    (out / 'articles').mkdir()
    shutil.copy2(m, out / 'articles' / 'manifest.json')
print('page ready:', idx)
