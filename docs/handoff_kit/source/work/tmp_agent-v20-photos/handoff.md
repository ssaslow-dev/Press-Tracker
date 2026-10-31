# agent-v20-photos handoff (2026-10-28)

## 1. For agent-buttonopt (sheet_task.py: Update button save step, PHOTOS-v2 F6)
Goal: every new saved copy embeds its photos at save time, in the same cache format as work/img_cache (img_embed.py).
New module `code/img_embed.py` (already copied into build/pub/pipeline/). Its `embed_page()` is the whole save-side step.

In `SheetTask.apply_pages`, after `chk = self.check_page(pid, row)` and the error/skip branches, before the library file is written:

```python
try:
    import img_embed as IE        # next to sheet_task.py (sys.path already holds the script folder for clean_html)
except Exception:
    IE = None
...
html_out = chk['html']
if IE is not None and getattr(self, 'img_cache', None):
    html_out, ist = IE.embed_page(html_out, p.get('url', '') or row.get('Publisher link', ''), self.img_cache,
                                  story_id=str(self.s.get(r, 'Story ID') or ''), aid=aid, copy_file=f'{year}/{fname}')
    info['photos'] = {'embedded': ist['embedded'] + ist['kept'], 'dropped': ist['dropped'], 'fetched': ist['fetched'],
                      'failed': ist['failed'][:10]}
# write html_out (not chk['html']) to pages_dir/<year>/<fname>; _original_html keeps chk['page'] (remote URLs as saved)
```
- New CLI arg: `--img-cache DIR` (default: `<pipeline>/img_cache` or the lib's work/img_cache). embed_page appends one record
  per fetched image to DIR/manifest.json/.csv + worklist.json (index-aligned) and stores `<sha256>.jpg` (<= 1000 px wide,
  JPEG q75; small GIF/SVG kept as is).
- Result: `result.pages[].photos`; a summary line "N photos embedded, M dropped (cloudflare/403/404 …)". No "photos waiting"
  state is needed: a photo that cannot be fetched at save time is dropped (DECISIONS 2026-10-28: drop images that still
  fail, captions kept). No workarounds: Cloudflare/401/402/403 are recorded, never retried another way.
- Release copies (RELCOPIES-v1, `save_release_copy` ~line 1118-1150): same call on `out` before it is written
  (kind='release', story_id=prid). Its existing "make /src absolute" regex can stay; img_embed resolves relative URLs too.
- gabriel.asmdc.org / a46.asmdc.org send an incomplete TLS chain: set env `JG_IMG_CA` to a bundle that adds the
  "Entrust DV TLS Issuing RSA CA 2" intermediate (scratchpad/imgfetch_ca/bundle_plus.pem) — verification stays on.
- clean_html.py (find mode) now runs `fix_imgs()` first (PHOTOS-v2 F1): placeholder/empty src -> lazy URL or largest
  srcset <= 1000w; KTLA/Mother Jones "<article URL>/<width>" src replaced the same way (or removed); relative -> absolute;
  query strings (Arc `?auth=`) kept as given. Nothing to wire: check_page already calls clean_page(mode='find').
  Root of the 47 missing `?auth=` tokens: they were absent in the saved pages themselves (pre-existing library saves and
  TinyFish text); no code of ours strips query strings (tfClean in 40_update_outlets.js passes HTML through). Nothing to
  recover for those 47 (they fail 403 and are dropped).
- Step 6 rebuild (sheet_task_prompt.md "Rebuild"): a full copies rebuild should pass
  `--img-cache <cache> --pdf-restore <cache>/pdf_restore --img-strict` to make_copies.py (build gate: exit 3 if any copy
  keeps an image that would not load). When the step only appends a saved page to articles/<year>.json, the page already
  carries data: photos from embed_page.

## 2. For the owner of code/apply_all_patches.py (coordinator / final build)
Add to PIPELINE (they are imported by make_copies.py / sheet_task.py from the script folder):
```python
'img_embed.py': 'code/img_embed.py',            # PHOTOS-v2: photo cache lookup / save-time embed (make_copies, sheet_task)
'av_display_clean.py': 'code/av_display_clean.py', 'av_rules.json': 'code/av_rules.json',   # AVPREVIEW-v1 fix A (make_copies)
```
and `'code/img_embed.py', 'code/av_display_clean.py'` to PY_CHECK. (Copied by hand into build/pub/pipeline/ for now.)

## 3. For the final build (make_copies invocation)
Add to the existing make_copies.py command:
`--img-cache work/img_cache --pdf-restore work/img_cache/pdf_restore --img-strict`
Publish the new img/100.json + img/101.json (11.9 + 8.9 MB, each < 16 MB) in place of the old img/100.json, and keep
publishing img/0..15.json (reused refs). The pdf/<code>/pN.jpg page images of the other PDF copies stay published as before
(33 local refs in the new copies). Nothing else changes in the publish list.

## 4. For DECISIONS / CONTRACT (coordinator)
- PHOTOS-v2: photos embedded at copy build (make_copies --img-cache) and at save (img_embed.embed_page); unloadable photos
  dropped with their empty wrappers, captions kept; viewer backstop (06_story_sheet.js safeImgs/hideBroken).
- ORIGIN ROOT FIX D applied in make_copies: Original's own HTML > Original's NewsBank/ProQuest text > other rows' HTML.
  240 stories switch from a reprint's page to their Original's NewsBank text (list: work/tmp_agent-v20-photos/new/report.json
  copy_order.original_text_over_reprint_html).
