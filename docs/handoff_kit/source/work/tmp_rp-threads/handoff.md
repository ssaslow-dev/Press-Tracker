# rp-threads → main (files I don't own)
1. code/apply_all_patches.py PIPELINE: add `'relthread.py': 'code/relthread.py',   # RELTHREAD-v1: tab-releases thr (releases_data.py imports it)`.
   Without it the pipeline's releases_data.py finds no relthread.py and simply omits `thr` (no error).
   releases_data.py also reads pipeline/insights/bill_timeline_data.py and pipeline/release_texts.json (both already shipped).
2. Block size: tab-releases is now 151.7 KB (thr 25.3 KB), just over code/tabs_data.py's CAP = 150_000 soft warning.
   Options: raise CAP to 200_000 (owner of tabs_data.py), and/or rp-ui empties r[url][4] (co-issuer string, 11.8 KB) once
   releases.js reads people from thr.x.n / thr.pp.
