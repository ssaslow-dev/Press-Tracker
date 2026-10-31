# AVPREVIEW-v1 — Audio & video preview cleanup (spec, draft)

Owner: agent-previewclean (draft only; no code/ or build/ edits). Trigger: Sammy comment de9c2baa on an Audio & video Episode preview ("Highlighting mentions of Gabriel 1 of 3"): "clean up previews like this there is visible back end stuff. Do it throughout". Scope change from Sammy (via coordinator): **AV previews only**. Article, press-release, NewsBank and other web-save previews are out of scope and not covered here.

The preview he commented on is **s04692** (The John Kobylt Show, 05/29). Its "1 of 3" counted two hits in our own field lines ("Gabriel role: brief mention" and the "Excerpt rule" text). Only one hit was in the transcript. After the cleanup it shows "1 of 1".

## 1. Scope and gate

- **AV preview:** the saved copy (`articles/<year>.json`, keyed by Story ID) of a story whose Original row has a row in the workbook's "Audio & video details" tab with Item type **Episode**, **Broadcast segment** or **Video clip**.
- **Live count:** 86 stories (Podcast Episode 22, Radio Episode 5, Radio Broadcast segment 1, TV Broadcast segment 41, TV Video clip 4, Video clip 13). 80 of them have a copy and were audited. The 6 without a copy are s01777, s01795, s01796, s04667, s04676 and s04687; they have nothing to clean.
- **Not in scope:** AV-tab rows with Item type "Web story" (station or radio *articles*, 375 Originals). Their previews are article web-saves.

## 2. Audit (live tracker version 1793153876-e0f4, rendered like 06_story_sheet.js: srcdoc, links stripped, Playwright innerText)

| Leak a reader shouldn't see | Copies | Hits | Examples | Where it enters |
|---|---|---|---|---|
| Capture header: "Outlet · date", page URL, "Saved 2026-10-27" | 41 | 41 | s02864 "Saved 2026-10-27"; s01110 "CBS News · 2023-02-21 / https://www.cbsnews.com/… / Saved 2026-10-18"; s02211, s02525, s03947 | Saved file (library header `<div>`, written by sheet_task.page_html / chrome-save / caption builders; clean_html keeps "Saved …" lines by design) |
| Our own analyst fields: Platform URL(s) (exa.ai + podtrac mp3 URLs), Exa library ID, "Source: Exa podcast library transcript", "Excerpt rule: …", "Gabriel role: …", "Transcript: Excerpts", "Note: …" | 13 | 91 | all 13 Exa-built podcast pages s04688–s04700 | Saved file (archived builder archive/2026-10-28/work/tmp_agent-podcasts/build.py). The same facts are kept in the AV tab (Notes, Transcript kind, His role, links). |
| Raw time codes: ms speaker-turn ranges "23:01.092–24:07.712", "Duration: 35:31.000", "(published 2026-05-30T01:16:25+00:00)", ISO "2024-08-21T19:11:47Z" | 14 | 400 | s04692; s02921 | Saved file (Exa builder; SoundCloud text) |
| Caption/transcript time markers and cue junk: lines that are only "8:35 am" / "00:05", "[15:00:32]", "Start: 15:00 End: 15:59", caption "ú" debris ("úyeah", "byúthe") | 8 | 179 | s03120, s03206, s02875 (KTVU/KRON), s03092 (mitú, 120 lines), s00052/s00207/s01619 (CNN) | Saved file (caption pages; NewsBank/ProQuest transcript text) |
| File names and capture captions: "Text of the NewsBank PDF (NewsBank Multiple Articles - 2026-10-25T205047.834.pdf, item 7)", "Text of the ProQuest PDF (12 pages)", "· 7403 words", NewsBank APA citation with infoweb URL | 6 | 16 | s00207, s01094, s01096, s01426, s01548, s01619 | make_copies.nb_page (the captions and citation); ProQuest text copy header |
| Transcript-vendor boilerplate: "Return to Transcripts main page", "THIS IS A RUSH TRANSCRIPT…", "END Content and Programming Copyright … VIQ Media Transcription …", NPR footer (copyright / "Accuracy and availability…" / "NPR does not offer…") | 5 | 7 | s00052, s00207, s01094, s01096, s00486 | Saved file |
| Player, app and nav UI text: "podcast playback", "Show transcript", "Use Left/Right to seek…", "Skip to main content", "Or, listen on Spotify", "WATCH NOW!", "CBS News App Open Chrome Safari Continue", "Add CBS News on Google", "Tweets by AsmGabriel", mitú footer, Commune membership/about footer, sponsor reads, Substack paid-subscriber pitch, KPCC archive notice | 12 | 25 | s01797, s02570, s04002, s01784, s01110, s04061, s03092, s02212, s02211, s03947 | Saved file |
| CMS shortcode / tags: `[fusebox_track_player_latest social_twitter=…]`, "Genre News & Politics" | 2 | 2 | s01797, s02921 | Saved file |
| Our own label in the title and source line: "(segment on Gabriel bill to put Planned Parenthood hotline on student IDs; Internet Archive TV News)", "Closed-caption transcript of the segment (Internet Archive TV News Archive)" | 1 | 2 | s04100 | Saved file (IA caption builder) |
| Layout debris: empty "From" / "By" / "Series" / "." labels, lone "(" ")" photo-credit lines, jammed "November 8, 20244:31 AM ET" and "March 14, 202400:34", consecutive duplicate lines (og description repeated), og title+description line, bare URL in front of a copyright line | 12 | 33 | s00486, s03107, s03568, s02781, s03764, s04178, s03947, s04059, s01426 | Saved file |
| **Total** | **75 of 80** | | | Tracker preview renderer adds nothing. It only strips `<a>`/`<area>`. |

Full per-copy list with every removed fragment: `test_report.json`. Rendered text before and after the cleanup: `before/<sid>.txt` and `after/<sid>.txt`.

### Found but not fixable by a cleaner (listed for the coordinator; no rule written)

1. **Listing or wrong pages saved as the copy:**
   - s01819 (FOX40 video page = a list of other stations' teasers plus site nav; only line 1 is the story)
   - s03489 (Valley Beth Shalom Gala 2023 sponsor list)
   - s03780 (VBS video-archive listing)
   - s04178 (podbean show listing)

   DECISIONS treats listing pages as error copies (RETRY – TinyFish). Route them to that queue rather than to this cleaner.
2. **Empty NewsBank copies:** s01426 and s01548 (AirTalk) have no body text, only a URL and a copyright line. After the cleanup they show the headline, byline and outlet/date only. They look like duplicates of s03947 and s04061 (the same AirTalk episodes as full LAist pages), so they belong in the regroup/duplicate queue.
3. **ProQuest text with fused words:** s01619 ("andthank", "FredrickaWhitfield", "Take alook"). The PDF line joins dropped the spaces. This needs a re-extraction from the PDF text layer, not a regex.
4. **AV box Notes:** the story panel's AV box (53_tabs.js tbAvBox, `a.notes`) shows the AV tab Notes verbatim, for example "Exa podcast library: https://exa.ai/…; audio: https://…mp3; finder note: Exa library ID …". This is the same kind of leak, but in the panel, not the preview. A follow-up should show only the reader part, or hide the notes.
5. **Kept on purpose:** program titles in the form "KRON 4 News at 630pm (MyNetworkTV - San Francisco (KRON))"; transcript stage directions ("(COMMERCIAL BREAK)", "(BEGIN VIDEO CLIP)", "[VIDEO CLIP PLAYS]"); KQED's "This is a computer-generated transcript…" notice; speaker names and mm:ss start times on turns.

## 3. The cleaner

`work/tmp_agent-previewclean/av_display_clean.py` with rule data in `av_rules.json` (standalone; BeautifulSoup, same dependency as clean_html.py). It exposes `clean(html, lang) -> (html, report)`. It never touches library files.

The rules run in this order (exact patterns are in av_rules.json):

1. **header:** remove the first `<div>` before the `<h1>` when its lines all match `Saved YYYY-MM-DD…`, a bare URL, or `<outlet> · <date>`. If other lines are mixed in, only the matching lines go.
2. **pdfcap:** remove `p.pdf-cap` lines that start "Text of the NewsBank/ProQuest PDF" or contain "Available from NewsBank". Remove "· N words" from the meta caption.
3. **fields:** on `<p><b>Label:</b> …</p>` lines:
   - Drop the labels Platform URL(s), Exa library ID, Source, Excerpt rule, Note, Gabriel role and Transcript.
   - Rewrite Date (drop "(published …)") and Duration (drop milliseconds).
4. **strip** (inside text nodes; never `<title>`/`<script>`/`<style>`):
   - leading URL before ©
   - ms turn range → start mm:ss
   - `[hh:mm:ss]`
   - "Start: … End: …"
   - lowercase `[x_y …]` shortcodes (case-sensitive, so "[VIDEO CLIP PLAYS]" stays)
   - VIQ copyright tail
   - ISO timestamp → date
   - "Genre …" tag
   - jammed year+time → "year · time"
   - the IA title label and IA source line
   - caption "ú": English rows only, and only on pages with the TV-caption signature
5. **kill:** remove a whole block whose text fully matches a pattern:
   - time-only line
   - "Return to Transcripts main page"
   - rush-transcript line
   - empty labels
   - lone parentheses
   - player UI
   - app banner
   - "Tweets by …"
   - NPR footer lines
   - KPCC archive notice
   - Substack paid pitch

   A block of 40 or more words is kept unless its rule is marked allow_long (NPR / KPCC / Substack only).
6. **tail:** remove the mitú footer, the Commune "Try Membership…" footer and the Commune "About the Commune Podcast" section, plus every block after them.
7. **section:** remove "This show is made possible by:" and the sponsor-read lines after it (lines with "use code", ".com/", "Go to", "% off").
8. **dedupe:** remove a block identical to the block before it. Also remove a top block that equals "<h1> + <a later block>" (og title + description).
9. **note:** on the Exa pages, add one reader line under "Transcript excerpts" in place of the dropped field lines: "Machine-generated transcript, excerpted: each passage that mentions him, with surrounding context. […] marks omitted stretches." It says "him", not "Gabriel", so the mention highlighter doesn't count the note.

**Safety guard:** if kill rules would remove more than 25% of a page's words, the page is returned unchanged and flagged. This fired 0 times on the live set.

## 4. Where each fix goes (no live code changed; for the code owner after agent-backendclean2's fold)

| Fix | File / function | Change |
|---|---|---|
| A. Clean every AV preview at copy-build time | `code/make_copies.py`, rebuild mode (`--clean`), at both places that set `pages[sid]` (from_clean and nb_page) | Wrap the page with `av_clean(sid, page)` (snippet below). Add `av_display_clean.py` and `av_rules.json` next to make_copies in `code/` and `build/pub/pipeline/` (apply_all copies list + publish list). |
| B. New saves from the Update button / sheet task | `code/sheet_task.py`, where a find's cleaned page is written to `pages/<year>/<file>` and AVTAB `apply_av` gives the row its Item type | For AV Item types, also write `pages/_display/<sid>.html` = `AVC.clean(page, Language)[0]` and list it in `result.pages[].display`. The library file stays as clean_html made it (raw page in `_original_html`). |
| B2. Sheet-task prompt, step 6 "Rebuild" | `code/sheet_task_prompt.md` step 6 | "Add each saved (cleaned) page to articles/<year>.json …": use `pages/_display/<sid>.html` when the result lists one (AVPREVIEW-v1). Step 4 commits do not change (display copies are never committed to the Mac library). |
| C. Future transcript pages (if the podcast or IA builders are revived) | builders under archive/ (archived; not live) | Write the analyst fields to the AV tab only, not into the page. The display rules stay as the backstop. |
| D. Tracker JS | `cleanLocal` in 40_update_outlets.js is a stub (DECISIONS 2026-10-27 cut: no in-browser cleaner) | No change. A preview opened from IndexedDB right after an Update can show the raw header until the sheet-task rebuild. Same as articles today. |
| E. Panel (follow-up, not a preview) | 53_tabs.js `tbAvBox` notes row | Separate item; see section 2, list item 4. |

Snippet for A (make_copies.py, after `rows_by_story` is built; `-I` drops the script directory, so add it to sys.path as sheet_task.py does):

```python
# AVPREVIEW-v1 make_copies: Audio & video previews get the display cleanup (av_display_clean.py + av_rules.json here)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import av_display_clean as AVC
    _AVT = pd.read_excel(a.cov, sheet_name='Audio & video details', dtype=str).fillna('')
    AV_ITEM = {r['Story ID'] for r in _AVT.to_dict('records')
               if r['Item type'] in ('Episode', 'Broadcast segment', 'Video clip') and r['Story ID'] in O.index
               and r['Article ID'] == O.loc[r['Story ID'], 'Article ID']}
except Exception as _e:
    AVC, AV_ITEM = None, set(); rep['avpreview_error'] = repr(_e)
rep['avpreview'] = {'copies': 0, 'changed': 0, 'removed_words': 0, 'flags': {}}

def av_clean(sid, page):
    if not AVC or sid not in AV_ITEM:
        return page
    out, r = AVC.clean(page, str(O.loc[sid].get('Language', '') or 'English'))
    rep['avpreview']['copies'] += 1
    if r['removed'] or r['rewritten']:
        rep['avpreview']['changed'] += 1; rep['avpreview']['removed_words'] += sum(x[2] for x in r['removed'])
    if r['flags']:
        rep['avpreview']['flags'][sid] = r['flags']
    return out
# ... pages[sid] = av_clean(sid, drop_blobs(externalize(...), sid))      (from_clean)
# ... pages[sid] = av_clean(sid, nb_page(NBT[aid], ...))                  (NewsBank text)
```

Order matters: run `av_clean` after `externalize` and `drop_blobs`. The cleaner leaves `jgimg:` srcs untouched (it only edits text nodes and drops text blocks; a `<figure>` with an image is never a text block).

## 5. Originals and regeneration

- Raw originals are untouched: `Tracker library/_original_html/…`, the library files in `Tracker library/<year>/` and `work/html_clean/` all stay as they are.
- The cleaned versions exist only as **display copies**, inside the tracker's `articles/*.json`.
- No Mac files move and nothing is deleted.
- To apply, rebuild the copies with fix A (full copies rebuild: make_copies `--clean`), then publish `articles/*.json` and the manifest through the normal build. Only the 75 AV shards' entries change. Article copies are byte-identical, because the gate skips them.

## 6. Test (story-text check)

`python3 -I test_av_clean.py <LIB>` runs the cleaner over **all 80 AV copies** of the live tracker. For each copy it renders before and after the way the viewer does, then checks three things:

- **Word balance:** words after = words before − words removed by rules + words of the inserted note (within 2%).
- **Mentions:** every Gabriel mention that disappears sits inside a removed back-end fragment.
- **Block size:** no removed block of 40 or more words, apart from header/caption/field/strip/dedupe/tail rules and the three allow_long boilerplate lines.

Result (2026-10-28):

| Measure | Result |
|---|---|
| Copies checked | 80 |
| Copies changed | 75 |
| Failures | 0 |
| Safety flags | 0 |
| Words | 99,737 → 94,949 (4,880 removed by rules; the inserted note adds a few) |
| Gabriel mentions | 162 → 126 |

The 36 mentions that go are:
- 13 "Gabriel role" lines
- 13 "Excerpt rule" lines
- 5 "Note" lines
- 1 internal IA title label
- 1 "Tweets by AsmGabriel" widget
- 3 duplicated og-description lines (the same sentence still shows once)

No transcript or story mention is lost.

**Before/after samples** for every AV preview type (Exa podcast excerpts, full podcast transcript, TV caption transcript, IA caption with our label, NewsBank network transcript, empty NewsBank radio copy, NPR transcript page, station video page, mitú timed transcript, podcast episode page, sponsor reads, repeated description) are in `before_after_samples.md`. Two condensed examples:

s04692 (the commented preview):
```
BEFORE  Date: 2026-05-29 (published 2026-05-30T01:16:25+00:00)
        Platform URL(s): https://exa.ai/library/podcast/vzx8r8hs9b5/episode/sfn3v7yx4wg | https://podtrac.com/pts/redirect.mp3/…
        Exa library ID: sfn3v7yx4wg / Gabriel role: brief mention / Transcript: Excerpts / Duration: 35:31.000
        Source: Exa podcast library transcript (machine-generated) / Excerpt rule: Every passage naming Gabriel … / Note: Same NBC4 report as John Phillips 05/29.
        Eric Leonard · 23:01.092–24:07.712
AFTER   Date: 2026-05-29 / Duration: 35:31 / Hosts: John Kobylt / Guests: David Tangipaa
        Transcript excerpts
        Machine-generated transcript, excerpted: each passage that mentions him, with surrounding context. […] marks omitted stretches.
        Eric Leonard · 23:01
```
s03120 (KTVU caption):
```
BEFORE  Saved 2026-10-27 / … / 8:35 am / úyeah it's a great question, so a lot of these dyes were first approved byúthe fda …
AFTER   KTVU Mornings on 2 (FOX - San Francisco (KTVU)) / … / yeah it's a great question, so a lot of these dyes were first approved by the fda …
```

## 7. Risk to story text

- **Low, and measured on every live AV copy.** Rules are exact-line or anchored patterns, scoped to the 86 AV stories by the gate.
- **Time-only lines:** the time_marker kill removes a line that is only a time ("8:35 am", "00:05"). A transcript line that is a spoken time on its own would also go. None appeared in the 80 copies.
- **Caption "ú" rule:** gated to English rows with the TV-caption signature, so Spanish "aún" and "Jesús" are never touched.
- **Dedupe:** removes only consecutive identical blocks of 3 or more words.
- **New AV sources:** these may bring boilerplate the rules don't know about. It would stay visible (fail-safe) until a rule is added.
