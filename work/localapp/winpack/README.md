# winpack: the save pipeline on a portable Windows Python (build step 5 groundwork)

Written 2026-11-02. Rules applied: LOCALAPP-v1 and GOVIT-v1 (government PC: PSF-signed CPython from NuGet, official PyPI wheels only, everything hash-pinned, fewest packages, no native helper programs, no network at run time, no PowerShell, no registry, no writes outside the app folder).
Nothing in `code/`, `build/` or `work/saver/` was changed. Every code change is a proposed patch in `patches/`.

## What is here

| File | Purpose |
|---|---|
| `requirements-win.txt` | the 10 pinned wheels (win_amd64, cp313) with sha256 |
| `fetch_wheels.py` | build-machine script: `pip download --require-hashes`, re-hash, refuse unpinned files, list native files, refuse native code outside numpy/pandas, optional `--extract` into site-packages (leaves out the packages' `tests/` folders, then precompiles `.pyc` with unchecked-hash; run on Python 3.13) |
| `selfcheck.py` | run on the PC before a save: imports, UTF-8 mode, time zone data |
| `patches/01_release_rule_pdftext.patch` + `pdftext_pypdf.py` | pdftotext replaced by pypdf (pure Python) |
| `patches/02_img_embed_offline.patch` | photo download switched off outright (`AJG_NO_NETWORK=1`), `requests` never imported |
| `patches/03_saver_steps_utf8_nonet.patch` | saver runs pipeline scripts with `-X utf8` and sets `AJG_NO_NETWORK=1` |
| `tools/pdf_compare.py` | pdftotext vs pure-Python text on library PDFs, through the release rule's own tokenising |
| `tools/run_pinned_tests.py` | runs the saver tests with only the pinned set importable |

## 1. Inventory: third-party code and external programs

"Save path" = run by `saver.py preview|save` (sheet_task.py, build_data.py, relmatch.py, then the rebuild: tabs_data.py, assemble.py; see `saver_steps.py`). "Page build" = building the tracker page.

| Item | Where (file:line) | Feature | Save path? | PC answer |
|---|---|---|---|---|
| openpyxl | `saver_diff.py:151`; `sheet_task.py:48-49,2586,4230`; `avtab.py:755,756,793`; `author_columns.py`, `shared_data.py` | read and write the workbook; the saver's cell-by-cell diff | Yes, core | pin 3.1.5 (+ et_xmlfile 2.0.0), pure Python |
| pandas | `build_data.py:12` (reads 4 sheets); `tabs_data.py:9`; `build/tabs/*_data.py`; `sheet_task.py:4381` (`verify`, after-write check); `insights_data.py:7`; `reltab.py:355`; `make_copies.py:36` | read sheets as text frames, filter, iterate rows | Yes (build_data, tabs_data, verify) and page build | pin 3.0.5. NATIVE. See "Can pandas be avoided" below |
| numpy | pandas dependency only (no direct import in our code) | | via pandas | pin 2.5.4. NATIVE |
| python-dateutil | pandas dependency only | | via pandas | pin 4.0.0 (pure; the 4.x line has no `six`) |
| tzdata | needed by `zoneinfo` on Windows: `dates_lib.py:4`, `avtab.py:71,701`, `sheet_task.py:4515`, `saver.py:96,242` (saver has a hand-made Pacific fallback, the pipeline does not); pandas also needs it on Windows | America/Los_Angeles local day | Yes | pin 2026.6, pure data |
| beautifulsoup4 (html.parser only) | `clean_html.py:37`, `reprint_rule.py:143`, `av_display_clean.py:27`, `sheet_task.py:1519` | clean saved pages, extract text for the reprint and release rules | Yes | pin 4.15.0 + soupsieve 3.0.4 + typing_extensions 4.16.0, all pure |
| pypdf | new (replaces pdftotext) | text of NewsBank/ProQuest PDF library files | Yes (release check, `sheet_task.py:2677` -> `release_rule.py:160`) | pin 6.17.0, pure, no dependencies |
| pdftotext (poppler exe) | `release_rule.py:160-162`; `extract_nb.py:148` (one-off) | PDF text | Yes | DROP the exe (GOVIT). Replaced by pypdf, patch 01 |
| requests | `img_embed.py:239` (`_session`) | photo download at save time (cache first, fetch on a miss) | Reachable on the save path, must never run | DROP. Patch 02 |
| Pillow | `img_embed.py:257,267` (normalize, fetch only); `make_copies.py:492` (page build, `_shrink`); `media_gate.py:72,98` | convert unusual data: images (avif/heic/bmp/tiff/ico) to PNG/JPEG | `media_gate.clean_html` runs inside `clean_html.py:696` on every new page, but inside try: without Pillow such an image is dropped instead of converted | DROP (native). Consequence below |
| cairosvg (+ native Cairo) | `media_gate.py:95` | SVG data: images in a saved page -> PNG | same try as above; failure = image dropped, counted as `img_dropped` | DROP. Consequence below |
| langdetect | `extract_nb.py:14` | one-off NewsBank extraction | No | DROP |
| pytest | saver tests | | tests use unittest, fine | not shipped |
| node | `apply_all_patches.py:262` (`node --check`, "node not found" is skipped); JS tests | verify only | No | not shipped |
| bash | `build/build.sh`, `build/tests/run_all.sh`, `build/tests/tabs/build_testpage.sh` | build and tests | No | not shipped; the Python page build (work/localapp/build) replaces build.sh |
| `sys.executable -X utf8 -I script` | `saver_steps.py:119` | how every pipeline script runs | Yes | patch 03 |

Searched and not found in the save/build code: `os.fork`, `shell=True`, `os.system`, `fcntl`, `signal`, `os.link`/symlinks (only `make_handoff_kit.py:256,387`, a kit tool), `expanduser`, `Path.home`, `tempfile` in `src/`. `multiprocessing.Pool` only in `shared_data.py:214` (one-off, needs a `__main__` guard on Windows). `importlib.util.spec_from_file_location` in `tabs_data.py:26`, `insights_data.py:21`, `releases_data.py`, `reporters_data.py` loads sibling files by path; fine on Windows.

## 2. Wheels (all from PyPI, win_amd64 / cp313 or py3-none-any)

| Wheel | sha256 | Native code inside |
|---|---|---|
| openpyxl 3.1.5 | 5282c12b107bffee... | none |
| et_xmlfile 2.0.0 | 7a91720bc7568435... | none |
| beautifulsoup4 4.15.0 | d6f88de62e1d4e38... | none |
| soupsieve 3.0.4 | 8412826614f9c632... | none |
| typing_extensions 4.16.0 | 481caa481374e813... | none |
| pypdf 6.17.0 | 5bd827266a21553b... | none |
| python_dateutil 4.0.0 | a5e246f79eb80475... | none |
| tzdata 2026.6 | 0a10eec6e13ef16b... | none (data files) |
| **pandas 3.0.5** | 0d298e951f23016c... | **46 files**: 45 `.pyd` (`pandas/_libs/*`, `_libs/tslibs/*`, `_libs/window/*`) + `pandas.libs/msvcp140-*.dll` |
| **numpy 2.5.4** | 8b4d2fd2d34e5f8c... | **21 files**: `.pyd` under `numpy/_core, linalg, fft, random` + `numpy.libs/libscipy_openblas64_*.dll` + `numpy.libs/msvcp140-*.dll` |

Full hashes are in `requirements-win.txt`. 10 wheels in total (the first draft survey listed 9 packages plus tools). Only pandas and numpy contain compiled code; no other wheel does, and `fetch_wheels.py` refuses any other wheel that does. IT may ask: the `.pyd`/`.dll` files in those two wheels are not Authenticode-signed by us; the wheels themselves are the PyPI releases of the pandas and numpy projects, hash-pinned. The MSVC runtime `msvcp140` is bundled in both wheels, so no Visual C++ redistributable install is needed (CPython from NuGet carries `vcruntime140`).

Dropped from the first survey list: Pillow (native), cairosvg (needs Cairo DLLs), requests (and its 4 dependencies: urllib3, idna, certifi, charset-normalizer), langdetect, pytest. That is 10 fewer wheels than a straight copy of the Mac environment.

### Can pandas be avoided on the save path?

Yes in principle, not in this round. The pandas calls are narrow: `read_excel(sheet_name=..., dtype=str).fillna('')`, boolean-mask filter (`df[df['Original or reprint']=='Reprint']`), `.iterrows()`, `pd.concat`, `pd.DataFrame(columns=...)`, `.iloc[0]` and a few `.astype(str)`, `.isin`, `.set_index`, `.str.strip/lower`, `.to_dict` in `releases_data.py` and `sheet_task.verify`. A small openpyxl-backed frame class would cover it and would remove pandas, numpy and dateutil (3 wheels, all native but tzdata stays for zoneinfo). The risk is exact text of cells: `dtype=str` turns dates, numbers and blanks into specific strings (for example `2026-10-30 00:00:00`, `nan` handled by fillna) and every tab and block must stay byte-identical. It needs a shim, then a replay of the 10-30 save and a build-vs-live comparison, about a day of Sonnet work. Recommended order: first PC test with pandas; make the shim only if IT refuses numpy/pandas.

## 3. The decisions

**pdftotext -> pypdf (pure Python).** `release_rule.file_versions` turns the PDF text into the release rule's word lists (`reprint_rule.norm_tokens`), so what matters is the word sequence, not the layout. Test (`tools/pdf_compare.py`, 400 random library PDFs of 4030, poppler 24-series `pdftotext FILE -` as baseline, compared through the real `release_rule` tokenising incl. the citation cut and excerpt version):

| Extractor | Identical word lists | Notes |
|---|---|---|
| pypdf `extract_text()` (plain) | 0 of 40 | word order of header blocks and joined words differ (about 98% similar); not usable |
| pypdf `extract_text(extraction_mode='layout')` | 398 of 400 | the 2 misses lose most of a multi-column page (577 words -> 73) |
| pypdf layout, falling back to plain when plain has more than 1.2 times the words (`patches/pdftext_pypdf.py`) | 398 of 400 | same two files differ: they now keep all words but in another order (25-word-window overlap with poppler: 87% and 13%) |
| pdfminer.six | 38 of 40 | rejected: it has a hard top-level import of `cryptography` (native, Rust) and `charset_normalizer`; two more packages and a second native one |

So not byte-identical for 2 in 400 (0.5%) multi-column pages; the other 99.5% give exactly the same word lists. Effect of a miss: that row's release verdict could differ (untestable vs. tested), and release_rule lists untestable rows for review, never marks them. Speed: about 0.35 s a file against 0.02 s for poppler; only rows in a release's date window are read. Failure behavior is unchanged (`file_versions` returns no versions); because that failure is silent, `selfcheck.py` must pass before a save. Encrypted PDFs would need `cryptography` and would return no text (none of the 400 were).
Not tried: a Windows poppler build (rejected by GOVIT: native helper program).

**requests -> off, outright.** The photo path: `sheet_task.py:1477/2646` call `IE.embed_page` only when `--img-cache` is given; `embed_page` (`img_embed.py:373`) reads the cache first, then calls `_session()` (imports `requests`) and `fetch_one` for every uncached http(s) image. Today the saver passes `--img-cache img_cache` whenever the caller gives one, and relies on a dead proxy (`saver_steps.offline_env`) for "offline": an attempt is still made and fails. Without `requests` installed and no patch, `embed_page` would raise ImportError, `sheet_task` would catch it (`info['photos'] = {'error': ...}`) and keep the remote `<img>` tags in the saved page, which is a different result from today (photo dropped). Patch 02 adds an `_OfflineSession` whose `get()` raises ConnectionError when `AJG_NO_NETWORK=1`; `fetch_one` records a `conn` failure, the photo is dropped, captions kept, exactly today's offline outcome, and `requests` is never imported. Checked here with `requests`, `PIL` and `urllib3` blocked: `embed_page` returned `dropped 1`, `failed [('conn', url)]`. Patch 03 sets `AJG_NO_NETWORK=1` in `offline_env()` (keep the dead proxy too, as a second lock). Other network code: `make_copies.py:301` (poster fetch, page build only; goes through `IE.fetch_one`, same switch). `save_fetch.py`, `fetch2`, `billstatus`, `extract_nb.py` are not shipped. Photos for new stories: only those already in the image cache folder are embedded.

**cairosvg / Pillow: drop, accept the loss.** They are used only inside `media_gate` (`clean_html.py:696` on every new page): an SVG data: image or an unusual raster data: image (avif, heic, bmp, tiff, ico) is converted to PNG/JPEG; if conversion fails (also what happens when the library is missing, the calls are in try blocks) the image is dropped and counted (`img_dropped`). History from DECISIONS (MEDIAGATE-v1): the whole library had 14 svg data: images in articles plus 20 svg photos in the photo cache, so a handful over years. A new story with such an image would lose that one image on the PC and keep it on the Mac. Pre-rendering is not possible (the images arrive inside new pages). Suggest the saver report `img_dropped` / `svg_to_png` from the media gate stats in the preview. Pillow also serves `make_copies._shrink` and `img_embed.normalize`; neither is on the offline save path.

**node, bash, langdetect:** not shipped (verify-only, build/test-only, one-off).

**Time zones:** `tzdata` wheel (pure data, 633 files). `selfcheck.py` verifies the July offset of America/Los_Angeles.

**Text encoding (new finding, patch 03).** Python's isolated mode (`-I`, used for every pipeline script) ignores `PYTHONUTF8` and `PYTHONIOENCODING`. On Windows, a child's stdout pipe and default `open()` use cp1252, so a headline with a character cp1252 lacks (Chinese, Korean, Armenian, some Latin letters) would raise UnicodeEncodeError in `print`, and files opened without `encoding=` would read wrong. Fix: pass `-X utf8` before `-I` (patch 03 for `saver_steps.run_script`; the launcher must start the saver itself with `python.exe -X utf8 -I`). Unencoded `open()` calls remain in `make_copies.py` (json, ASCII only because json.dump escapes), `sheet_task.py:3586`, `build_data.py:402`, `build/tabs/travel_data.py:44` (test tool); UTF-8 mode makes them safe.

**Where the packages come from at run time.** The probe's script added `site-packages` to `sys.path` itself. The pipeline scripts are separate processes started with `-I`, which ignores `PYTHONPATH`, so they would not find the packages. Use a `python313._pth` file beside `python.exe` listing: `python313.zip`, `.`, `Lib`, `DLLs`, `..\app\site-packages`, and `import site` (the scripts add their own folder). This is honored with `-I` and needs no registry or environment. Untested on Windows (see risks). Also add `-B`/`PYTHONDONTWRITEBYTECODE` so no `__pycache__` appears (the saver sets it for children; start the saver with `-B`).

## 4. OS-specific paths and commands

| Where | What | Patch |
|---|---|---|
| `sheet_task.py:155-157` | `MASTER_XLSX`, `MASTER_LOCK`, `BACKUPS_DIR` = `~/Desktop/Tracker library/...` | None needed. They are only printed by `--check-only` (`sheet_task.py:4738`) and never opened; the saver passes real paths. Optional cosmetic patch later. |
| `release_rule.py:160-162` | `subprocess.run(['pdftotext', ...])` | Patch 01 |
| `img_embed.py:238-247` | `/root/.ccr/ca-bundle.crt` CA path, `HTTPS_PROXY` | Never reached with patch 02 |
| `saver_steps.py:119` | no `-X utf8`; `offline_env` | Patch 03 |
| `shutil.move` / `os.replace` over a target open in Excel | `saver.py:909` (master swap) | Windows refuses (PermissionError); saver already checks `open(w,'r+b')` first (`saver.py:390`) and handles it |
| `build.sh`, `run_all.sh`, `build_testpage.sh` | bash | not shipped; Python page build instead |
| `apply_all_patches.py:262` | `node --check` | skipped when node is absent; not run on the PC |
| `multiprocessing.Pool` `shared_data.py:214` | spawn on Windows | one-off, not shipped |
| `make_handoff_kit.py:256,387` | `os.link`, `copytree(symlinks=True)` | not shipped |
| Library file names (12,699 files in the snapshot) | Windows-invalid characters, trailing dot/space, reserved names, case collisions, long paths | none found; longest path here 85 characters. The PC folder must stay short (limit 260 without long-path support). |

## 5. Test that was run here

`pip install --target` of the same ten pinned versions (Linux wheels) into a temp folder, then `tools/run_pinned_tests.py <folder> --import-pipeline`: the folder is first on `sys.path`, system site-packages are removed, imports of requests, PIL, cairosvg, langdetect, pytest, lxml, pdfminer, chardet, charset_normalizer, certifi, urllib3, idna, six, cryptography fail on purpose.

- `cd work/saver; python3 -I tools/run_pinned_tests.py ...` equivalent of `unittest discover -s tests -t tests`: **Ran 95 tests, OK (1 skipped)**, 58 s. Versions loaded: openpyxl 3.1.5, bs4 4.15.0, soupsieve 3.0.4, pypdf 6.17.0, pandas 3.0.5, numpy 2.5.4, dateutil 4.0.0, tzdata 2026.6, et_xmlfile 2.0.0, typing_extensions 4.16.0.
- Import check of 24 pipeline modules (sheet_task, relmatch, clean_html, reprint_rule, release_rule, media_gate, img_embed, av_display_clean, avtab, dates_lib, ...) with that blocked set: no failures. This works because Pillow, cairosvg and requests are imported lazily inside try or functions.
- Caveat: the saver tests use the saver's own code and stubbed pipeline scripts, so they hardly touch pandas or bs4. Extra smoke: reading three sheets of the snapshot workbook with pandas (`dtype=str`) and extracting text from 150 library pages with `reprint_rule.html_text` gives the same hash with the pinned set and with this machine's installed set (pandas 3.0.5, bs4 4.15.0).
- Patches applied to a scratch copy: patch 01 and 02 apply cleanly; with `AJG_NO_NETWORK=1` and requests/PIL blocked, `embed_page` drops the photo without error and `release_rule.file_versions` reads a library PDF through pypdf.
- Windows wheels: downloaded by `fetch_wheels.py` with `--require-hashes`, all 10 verified, extracted (path-checked) here. Not executed (no Windows).

Not done: a full build_data / tabs_data / sheet_task run on the pinned set against a real pipeline folder (no pipeline folder with PIPELINE.sha256 in this repo); the real-pipeline replay remains as in CLAUDE.md.

## 6. Open risks

1. Whether the PC lets the unzipped `python.exe` load the 45+21 `.pyd` files and 3 `.dll` files from a user folder (AppLocker/WDAC, unsigned `.pyd`). pandas and numpy are the exposure; the pure-Python set has none. A one-file PC test (import pandas, numpy, read a small xlsx) should be the next round, before more is built.
2. The `python313._pth` arrangement is untested on Windows (NuGet layout, `-I -X utf8`).
3. pypdf differs from poppler on about 0.5% of PDFs (multi-column pages); two such files are known in the sample. A sweep of all 4030 PDFs would find them all (about 25 minutes); not done.
4. Dropping Pillow/cairosvg changes the page of a new story only when it carries an SVG or unusual raster data: image; silent unless the saver reports `img_dropped`.
5. New pipeline file `pdftext_pypdf.py` must be added to the `PIPELINE` map in `apply_all_patches.py` so `PIPELINE.sha256` lists it; the saver refuses unlisted files. Patches 01 and 02 change two listed files, so the pipeline checksums change too.
6. Dependency versions are the newest PyPI had on 2026-11-02 (dateutil 4.0.0, soupsieve 3.0.4 are newer than this machine's usual 2.9.x); the tests and the smoke hashes above passed with them, but the Mac master was built with older ones. Parser output with `html.parser` is bs4's own, not soupsieve's.
7. `file_versions` swallows errors, so a missing `pypdf` would silently make rows untestable. Run `selfcheck.py` first; consider making the saver refuse when it fails.
8. Windows path length (260) and Excel holding the master open (saver already refuses).
9. Pandas avoidance (above) is available if IT objects to numpy/pandas.
10. Network share (MULTIPC-v1): first import of pandas/numpy and the five-plus script starts per save may be slow over SMB; `.pyd`/`.dll` on a UNC path may be blocked by Windows; `cmd.exe` cannot start in a UNC folder (use `pushd`); the folder must be read-mostly (`-B`, precompiled). See section 7. Not measured on a real share.

## 7. Shared network drive (MULTIPC-v1)

The app folder, Python included, sits on a mapped drive or UNC path and is opened from several PCs, one saver at a time.

- **Relative paths.** Nothing in the packages or pipeline needs an absolute path: the pipeline scripts are started by relative name with `cwd` = the working folder, the `_pth` entry is relative (`..\app\site-packages`), `selfcheck.py` prints where each package loads from. The Mac paths at `sheet_task.py:155-157` are print-only. Launchers must not rely on a UNC working directory: `cmd.exe` cannot `cd` into `\\server\share` (use `pushd "%~dp0"`, which maps a temporary drive letter, or call `python.exe` by full path and let the scripts find their folder from `__file__`).
- **No .pyc written at run time.** Start every Python with `-B` (the saver already sets `PYTHONDONTWRITEBYTECODE=1` for the pipeline scripts it starts; patch 03 keeps that). `fetch_wheels.py --extract` precompiles all packages at build time with `--invalidation-mode unchecked-hash`, so imports neither write nor re-stat sources over SMB (this also means an edited `.py` in site-packages is not picked up; the packages are never edited). The pipeline's own `.py` files and the standard library are not precompiled by it: precompile them in the same way when the folder is assembled, or accept one compile per start (in memory only, with `-B`). Precompiled files are Python 3.13 only; a different Python minor version ignores them.
- **File count.** The 10 wheels are 3,477 files; leaving out the packages' own `tests/` folders (pandas 1,122, numpy 493) gives 1,862, plus about 790 `.pyc` after precompiling. numpy and pandas are 80% of the files and cannot go into a zip (`.pyd` must be on disk). The 8 pure-Python wheels (about 800 files without tzdata's 633 zone files) could be shipped as one zip on `sys.path` (openpyxl, bs4, soupsieve, pypdf, dateutil, et_xmlfile, typing_extensions import fine from a zip); not done: it breaks `__file__`-based resource lookups some packages use and was not testable here. The CPython tree from NuGet also has hundreds of files (`Lib/`); a `python313.zip` of the standard library would cut that; the probe did not test it. Measure before deciding.
- **Import time.** Measured here on local disk, warm: numpy 0.07 s, pandas 0.27 s, openpyxl 0.19 s, bs4 0.09 s, pypdf 0.11 s, all together 0.48 s. Over SMB each import costs file opens and lookups for every module (pandas touches several hundred `.py`/`.pyc` and ~45 `.pyd`); with precompiled files and a cold share, expect several seconds for the first pandas import on a slow link, not minutes. Not measured on SMB (no share here). Each pipeline script is a new process (sheet_task, build_data, relmatch, tabs_data, assemble: five or more starts per save), so the cost repeats; the Windows file cache on each PC softens the repeats. A copy to a local temp folder per run would break the "no writes outside the app folder" rule; the launcher can instead let the user choose to run from a local copy of the folder.
- **Misbehaving on network paths.** None of the pinned packages is known to need a local disk. Cautions: (a) `.pyd`/`.dll` loaded from a UNC path may be blocked by Windows zone/security settings (Mark of the Web on files fetched from the internet and unzipped by Explorer, or "UNC path not trusted"); the same IT policy risk as in risk 1 but stronger on a share. (b) numpy and pandas memory-map nothing from the package folder, but the saver's workbook read/write are ordinary file I/O: `os.replace` over SMB is fine, Excel's `~$` lock file is how a second user is detected (`saver.py:390` tries a write open), and the saver's own lock uses `O_CREAT|O_EXCL` (`saver.py:183`), which SMB honors but only between clients of the same server; a cached/offline-files setup would defeat it. (c) Two PCs with different clocks write timestamps into ledgers and backup names; backups use unique names. (d) Python's `socket.gethostname()` is written into the lock (`saver.py:177`), which helps to see who holds it. (e) Slow `shutil.copy2` of the 893 MB library is not needed: the saver adds only new pages.
