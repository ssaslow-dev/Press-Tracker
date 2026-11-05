# Update station: is it self-contained? (check of 2026-11-05)

**Verdict: yes.** A person on another claude.ai account can publish the same HTML as their own artifact and use it with a "for Update" file from the PC tracker. One small wording fix was made (finding 3). The two other findings are about documentation and cosmetics, not function.

Built page checked: `work/localapp/station/dist/index.html` (rebuilt twice from source; the first rebuild was byte-identical to the file that was there, sha256 `680dc5c6...`). After the one edit below, the new sha256 is `a4f6c1f2e41952b87d6cb9f2eab66a1fa6e0a9a1061a6d2d04d8b8ae087e1994`.

## What another account must do

1. **Connect TinyFish.** claude.ai, Settings, Connectors, add TinyFish (the connector's name must be exactly `TinyFish`; the page asks for that name, `TF = 'TinyFish'` at dist line 4283).
2. **Publish the page.** Open a chat (or Claude Code), give it `index.html` and ask: publish this file exactly as is, as a private artifact titled "AJG Update Station", icon "search", with these capabilities and nothing else: `db`, `downloads`, `sample` declared as `{images: true}`, and `mcp` for the connector "TinyFish" with tools `search` and `fetch_content`. Keep it private (a page that declares mcp cannot be shared by link anyway). Remixing the artifact from the existing one works the same if its owner shares it; the capabilities must stay as above.
3. **First open.** Load a "for Update" file, press Update. claude.ai asks to allow TinyFish and Claude for the page: allow both (later changes: the artifact's Permissions menu, then reload).
4. Nothing else: no database setup, no files beside the page, no other account's data.

MOVE_TO_OFFICE.md has the same steps and a sample sentence. Its sha256 line (`728e20a3...`) is stale: use the hash above, or re-run `shasum` after the next build.

## 1. Outside references

None are made by the page itself.
- Harness run with a strict policy (`default-src 'none'`, `connect-src 'none'`, `font-src data:`, `img-src data: blob:`) and every non-local request logged: **0 outside requests, 0 page errors** in all three runs (normal, TinyFish refused, Claude refused).
- Fonts: 19 `@font-face` inlined as `data:` (dist 1088 on). No `<link>`, `@import` or `<script src>` to anywhere. The built-in check in `build_station.py` (lines 109-112 and 163-171) refuses a build that has one.
- Two URLs remain in the tracker code but cannot run here: the cdnjs PDF.js loader (`loadPdfJs`, dist 2417-2422) is called only by `pdfFileToHtml` (dist 2425), which only the hidden Manage story-sheet drop reaches; the station reads PDFs with the inlined `vendor-pdfjs` (dist 10366). A `fetch(SHEET_URL)` (dist 3501) and `fetch('articles/manifest.json')` (dist 1515) are relative paths, answered by the station's `window.fetch` wrapper (station.js 162-167) or 404 harmlessly.
- Other URLs in the code (YouTube oEmbed dist 4466, Google News RSS 4565, GDELT 4773, gabriel.asmdc.org 4890, itunes) are **only fetched through the TinyFish `fetch_content` tool**, never by the page. They are about the subject, not an account.
- No links to other artifacts, the old tracker, a repository or an account id. No email addresses. "Sammy" appears only in source comments (e.g. dist 1649, 4437, 5574, 9856), not in any text a user sees. The page title is "AJG Update Station".
- Content that is specific to this office, by design: the whole thing searches for Assemblymember Jesse Gabriel; row links to NewsBank/ProQuest go through the California State Library proxy (`castatelib.idm.oclc.org`, dist 2164, 8847), which only works for people with that library login. Another office would need code changes to track someone else.

## 2. Account state

- Nothing needs data in the account's db. The tracker's own code runs against an in-memory db seeded from the file's `memory` (station.js 205-211, a Proxy window), so tones, runs, clips, edits, pages and reprints never touch the real db and are lost when the tab closes (by design, NORECOVER-v1).
- The only real db access: `collection('packed').doc(runId).set(...)` after a download (station.js 738-743), wrapped in try/catch and skipped if db is missing. It is never read back.
- Empty-db run (the harness default): load file, Update, Download works. Result: `ajg_update_20261105-2142_83614b19.zip` produced, status "Ready: 1 run: 0 new stories ...", no errors. (The stubbed TinyFish returned no results, so the zip had no stories; story packing is covered by the existing tests.) Browser storage: one per-viewer key `ajg_station_auto` (automatic mode), read inside try/catch.

## 3. Where the page gets its data

All inlined in the HTML: tracker code, fonts, PDF.js and pdf-lib (`vendor-pdfjs-worker`, `vendor-pdfjs`, `vendor-pdflib`), NewsBank/ProQuest parsers, the ProQuest outlet aliases (`PQParse.setTable`, dist 9127), `recall-default` (YouTube channels, podcasts, recall sources), the prjudge/nbtv/names code, the page templates and the Bills/Outlets/Releases tab sources.
From the "for Update" file (its keys: stories, rows, idmap, covcols, billsinfo, fetchrules, ins_release_pickup, memory, release_texts, fingerprint, notes): story list, spreadsheet rows, outlet and fetch rules, bill info, release-pickup data, release texts, run history. Nothing else is needed. Not inlined and needed: none. Note: the file is large (about 9 MB here) and carries story metadata, so it should be handled like the tracker's own data; the page never stores or uploads it.

## 4. Capabilities and calls

- `mcp`, server `TinyFish` (exact name), tools **`search`** (the ~500-700 planned queries; input built by `tfPlan`/`tfSearchInput`) and **`fetch_content`** (input `{urls, format: 'html'|'markdown', links, image_links, iframe_links, page_metadata, per_url_timeout_ms, ...}`, e.g. dist 4356, 4470, 4923). Called as `mcp.callTool('TinyFish', tool, input, {signal, cache})`.
- `sample` (Claude), declared `{images: true}`: `sample.json(prompt, {signal, modelTier: 'quick' | 'default', images})` for screening, classifying, tone, authors, translation and newspaper-page reading (dist 1612, 1838, 3373, 3406, 5291, 5306, 7892, 10524); `sample.limits()` (10619).
- `downloads`: `save({filename, data})` for the zip (dist 10126); falls back to a normal browser download if absent.
- `db`: only the `packed` write above.
- Degradation, checked in the harness:
  - TinyFish not connected (`server_not_connected`): red note "The web search did NOT finish: The TinyFish connector isn't connected for you. Add TinyFish in claude.ai Settings, Connectors ... This is not the same as 'nothing new'", download of what exists still works, no crash, no page errors (station.js 95-97, 783-785).
  - Claude not allowed or no runtime (`not_granted`): red note above step 2 "Claude is not allowed on this page. Allow it in the Permissions menu, then reload.", plus the TinyFish message; non-English stories keep the English headline only with a stated warning (station.js 403). No page errors.
  - Not tested: a runtime with no `window.claude` at all (all uses are guarded by `realClaude && realClaude.use`).

## 5. Instructions in the page

The "How it works" dialog and the step captions cover: what the page does, making the file on the PC ("Tracker files, Make for Update file"), making a new file after every save, what Update does and how long it takes (about 25 minutes, keep the tab open), Search all time, translation, NewsBank/ProQuest PDFs, Download, bringing the zip into the PC tracker ("Tracker files, Bring in update"), and the Permissions / connector fix. Gaps:
- Fixed: it pointed to a "NewsBank Download Guide" that lives outside the page. The sentence now states the steps itself.
- Not fixed (recommend): the dialog does not say the connector name must be exactly `TinyFish`, nor how to publish/copy the page. That is in this file and MOVE_TO_OFFICE.md only; it belongs outside the page, since a page that has not been published cannot be run to read it.
- Not fixed (cosmetic): the TinyFish-missing message inside the tracker's code ("Finding stories needs the tracker open in Claude with the TinyFish connector") is rewritten to station wording by station.js 783-784, so users see the station version.
- Docs drift: CLAUDE.md says the search starts "the day before the newest story"; the code and the dialog use two weeks before it (`SINCE_OVERLAP_DAYS = 14`, station.js 243). The page is consistent with itself.

## Findings by severity

1. (Low, documentation) MOVE_TO_OFFICE.md sha256 line is stale. Recommended: update after the final build.
2. (Low, instructions) Connector name and publish steps are not in the page. Recommended only.
3. (Low, fixed) Dialog referred to an outside "NewsBank Download Guide". Edited `src/station.html` line 17 (only edit); rebuilt `dist/index.html`.
4. (Info) Office-specific design (Gabriel; California State Library proxy links); the page works for another account but not for another subject.

## Edits made

- `work/localapp/station/src/station.html`, line 17: replaced "as the NewsBank Download Guide shows (State Library login, the saved search, Sort by: Oldest)" with "(log in to NewsBank through your library, run your saved search for Gabriel, choose Sort by: Oldest, download the results as PDFs)".
- Rebuilt `work/localapp/station/dist/index.html` (git-ignored) with `python3 -I work/localapp/station/build_station.py`. Nothing published, nothing committed. Test scratch files are in the session scratchpad only.

## Follow-up (2026-11-05, Sammy: implement the findings)
- Finding 1: MOVE_TO_OFFICE.md checksum updated to the published build.
- Finding 2: the How it works dialog now has "If something is blocked" (TinyFish connector name exactly "TinyFish", Claude with pictures, blocked work networks, State Library logins) and "Using this page on another claude.ai account".
- Finding 4: the State Library login note is in the dialog.
- The unreachable outside PDF.js loader (tracker code) is replaced in the station by its built-in PDF reader (newsbank.js), so no path can load anything from a public site.
- How it works rewritten to match the current behaviour (two-week window, Search all time, tracker-duplicate and old-find rules, translation at download, PC preview). Published 1793915424-f020.

## SMALLPAGE-v1 (2026-11-05)
claude.ai refused to review the 3.9 MB page for sharing ("too large or complex"). The page is now 1.2 MB: the two PDF libraries (pdf.js 4.10.38 legacy build, pdf-lib 1.17.1, the same pinned versions as vendor/PINS.json) load from cdn.jsdelivr.net the first time PDFs are added, and the fonts come from Google Fonts. Both are library sources claude.ai artifacts are allowed to use, and neither needs an account, so the page is still self-contained: no account data, no other artifact. Tests serve those files from vendor/ (tests/nb/cdn_local.js). Published 1793917597-4a73.

