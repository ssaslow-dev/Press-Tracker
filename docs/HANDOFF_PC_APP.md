# Handoff: AJG press tracker → offline Windows app + claude.ai Update station

From the Claude that built and ran the current tracker, 2026-11-02. Sammy's plan: a self-contained Windows app on a shared office network drive (an offline PC tracker that looks like today's), plus a separate claude.ai "Update station" page holding only today's Update button, which outputs an update zip for the PC. This note is what isn't obvious from the code and docs. Tags like `NOSCHED-v1` are entries in DECISIONS.md; search by tag. DECISIONS wins over every other doc, and inside it the newest entry wins. Counts and checksums go stale after each save.

## 0. Where things are

- **Master workbook:** `~/Desktop/Tracker library/AJG Coverage - NewsBank.xlsx` on Sammy's Mac, about 7 MB. It is the single source of truth. sha256 is `bc21c9fbffe3203fc9034ca00af614f90f05e49c2363b92aceba2bf3c959b5c1` after the 2026-10-30 save. Earlier shas: ef4e7a58 → 795ef625 → 33fe26d8 → 75eb6b32 → e52815d5 → bd2d84ea → 0159ea38 → bc21c9fb.
- **Library:** `~/Desktop/Tracker library/` on the Mac, 3.4 GB in all. The part a tracker needs is about 900 MB and 12,637 files: the year folders, `Press releases/`, `_original_html/` and `_original_pdf/`. The rest is `Work archive/` (2.4 GB, add-only mirror of work products), `Backups/`, `_archive/`, `_to_delete/` and `_docs/`.
- **Live tracker** (claude.ai artifact): https://claude.ai/artifact/5wHur4aRkSbAu6FscDpTjv. Shared read-only copy: https://claude.ai/artifact/6vhKKcNXarhSKwnCMk3Bks, private until Sammy shares it. Review-queue artifact: https://claude.ai/artifact/8yp4a5q8A8PcrQFdYcXPuB.
- **Docs:** the claude.ai Project "AJG Mentions Database" has copies under `library/` (START_HERE, HANDOFF, README, CONTRACT, DECISIONS, BOARD). Those copies may lag the newest DECISIONS entries (SAVER-RULES-v1, NEWPROJECT-v1).
- **Code:** it lived in a temporary Claude workspace. Durable copies:
  - the live tracker's published `pipeline/` folder: all Python modules, `tracker.js`, `shell.html`, the reference JSON;
  - a private GitHub repo, ssaslow-dev/Press-Tracker, a separate project with a 2026-10-31 snapshot of code, docs, tests, workbook and library. Sammy treats it as separate, so ask him before using it.
- **Read first, in this order:**
  1. START_HERE.
  2. AGENT_BRIEF.
  3. DECISIONS, by tag.
  4. CONTRACT: the run-doc and proposed-row schema the save step accepts.
  5. `code/sheet_task_prompt.md`: today's save procedure.
  6. `work/update_review/REPORT.md`: Fable's review of the Update button.
- **Stale statements in the docs.** Several still say Update "fires the scheduled task" or that the task is "disabled pending approval." Both are superseded by NOSCHED-v1: there is no scheduled task. Others:
  - TONE_GUIDE's "budget chair" role is wrong;
  - HANDOFF 2.1's Press releases "46 columns / pending" is superseded;
  - HANDOFF 8.1 D1–D12 is partly stale;
  - the `.probe_w` stray is already deleted.

## 1. Things the new design has to solve (my notes, not Sammy's decisions)

- **Offline pages can't load data files.** Edge blocks `fetch`/XHR from `file://` pages. Today's tracker and its shared copy load data that way: the viewer reads `data/data.json` and `data/rows.json` by synchronous XHR, and the page reads article shards (`articles/<year>.json`), `img/<n>.json` photo shards and `data/release_texts.json`. Offline, either ship the data as `<script>` files that set globals, or serve over a local web server. A server may be blocked by IT.
- **Artifact runtime features have no offline equivalent.** The page uses:
  - the `db` capability: team notes, tone/author/translation edits, saved views, runs, pages, edits, reprints, clips;
  - `sample`: Claude calls for screening and classifying finds, and translating headlines;
  - `downloads`: CSV export and the workbook download;
  - `mcp` TinyFish.

  The offline PC page needs local replacements or must drop these. Notes, views and edits that are shared through `db` today need a file-based home on the shared drive. Browser storage on `file://` is per-browser and per-profile, so it can't be shared between colleagues.
- **Everything on the station page is browser-side.** It keeps `db`, `sample`, `mcp` TinyFish and `downloads` (a page can only hand a file to the viewer through `downloads`). The connector's display name must be exactly `TinyFish`: the `TF` constant in `41_update_search.js` and the artifact's mcp capability must match. Pages that declare mcp can't be shared with "anyone with the link."
- **The station has to know what the sheet already holds.** Today the button dedupes against build blocks baked into the tracker page:
  - `rows`: every Coverage row; Removed rows count as kind X and unverified rows as kind "";
  - `sid_map.json`/`idmap`, `covcols` (column order), `rows.next {aid, s, pr}` and `fetchrules`;
  - `searched_to` from earlier runs, `lookup_cache.json`, the outlets table, and `gabriel_bills_leginfo.json`.

  An offline PC master means the station's copy goes stale after each PC save, so something must carry state from the PC back to the station: a sync file Sammy uploads, or a republish. Without it, the station re-finds stories already saved and can't advance `searched_to`.
- **What the update zip must contain:** whatever the save step consumes. That is:
  - the run doc (`rows` proposed in `covcols` order with `NEW-<run>-<n>`/`sNEW-<run>-<n>` placeholders, `mode`, `at`, `since`, `since_manual`, `releases_new`, `lookups`, `print_pages`, `found_by`, `searched_to`);
  - the `pages` docs (`rp-`/`og-` ids, fetched HTML), plus `edits`, `tones`, `authors`, `translations` and `reprints` docs;
  - any decided review-queue items.

  The saver's input layout `--db-dir <collection>/<doc id>.json` is already a natural zip layout. A worked example is `build/tests/sheet_task/fixtures/example_db.json`. IDs are assigned only at save time by `sheet_task.py`, never by the station.
- **Saves on the PC need Python.** That's `sheet_task.py` plus about 50 rule modules, openpyxl and pandas. The modules are imported inside try blocks, so a missing file silently switches a rule off. Pin the module set by checksum. The saver work has `PIPELINE.sha256`, and a Windows git checkout with autocrlf breaks that check. IT may block `python.exe` from a user folder or network share (AppLocker), and a home-made .exe trips antivirus and SmartScreen. python.org's embeddable Python is PSF-signed. This was Fable's Windows plan finding; Sammy then said IT probably won't allow installs.
- **Two save steps use the network today, and the PC is offline:**
  - photo embedding (`img_embed.embed_page`) downloads images;
  - CHAINORIG/`origin_wanted` lookups fetch pages.

  TinyFish can't fetch image bytes, so the station page can't get photos either. Today the photos come from Claude's cloud workspace during the save. Decide where photos come from, or accept copies without photos. A build gate currently rejects unresolved images.
- **Page cleaning happens at save time, in Python.** That's `clean_html.py` plus `clean_rules.json`, with raw pages kept in `_original_html/`. The page doesn't clean anything in the browser.
- **Shared network drive risks:**
  - Excel holds an exclusive lock on Windows, and a write fails while the workbook is open;
  - two colleagues could save at once, so keep a one-writer lock file (the 30-minute stale-lock rule is approved);
  - SMB latency on a 3,000-file library;
  - antivirus scanning;
  - Windows path length.

  Fable warned against keeping the master in a OneDrive-synced folder: conflict copies, cloud-only placeholder files, and AutoSave fighting writes.
- **Today's 256 MB, 511-file artifact cap drove a lot of design:**
  - photo shards repacked by `repack_img.py`;
  - publish batches under 64 MB and 255 files;
  - article shards.

  Offline, none of that applies. Don't port the workarounds blindly, but `make_copies` and its shard numbering still feed the page.
- **The station runs from a browser on the office PC** (claude.ai opens there), so a run takes 25+ minutes with the tab open.

## 2. Sammy's standing rules and preferences

- **Writing:** lean, precise, plain words; dry humor is fine. He pushes back on overstatement, so say what was checked and what wasn't. He is not a programmer.
- **Answers:** he answers in short labels ("1 yes, 2 no"); record his answers verbatim in DECISIONS. "Do what you think is best" is his usual delegation; record the decision as your call.
- **Scope:** stay strictly inside what he asked. Anything not in DECISIONS is a question for him, asked in short labels. For expensive or ambiguous work, ask first and give a time estimate. His latest instruction wins.
- **Nothing scheduled, ever** (NOSCHED-v1). No scheduled tasks, cron jobs or background runs for Update or saves. A scheduled task once fired on every Update even while `enabled:false`, with a stale prompt aimed at the wrong workbook. It was deleted.
- **Free sources only** (FREEONLY-v1). No TVEyes, Critical Mention or paid APIs.
  - TinyFish search and fetch have been free with a key since 2026-05-04: 30 searches and 150 fetches a minute. TinyFish browser automation costs about $0.016 a step; deep research costs $2 a run, so never use it.
  - Never log in, create accounts, enter keys or credentials, or bypass paywalls or bot blocks. Blocked pages get `BLOCKED – TinyFish` and you move on.
- **No Exa.** Its two one-time exceptions are used up.
- **No YouTube or advocacy blogs** (NOBLOGS-v1), judged by the row's outlet, not the link host. A TV or radio station's own segment on YouTube is TV coverage and stays.
- **Reference data before the web** (LEARN-v1). Check `outlets.json`, `reporters.json`, `reporter_employment.csv`, `outlet_rules.json` and `lookup_cache.json` first, and save confirmed answers back. He asked for this so the tool "learns" instead of paying the web twice.
- **Fill blanks only,** unless DECISIONS records an override (list in section 4).
- **Library is add-only.** Files that must go are `mv`'d to `_to_delete/`, never deleted, unless he asks.
- **One writer at a time.** Back up first, write a uniquely named file, verify the checksum (rule 7).
- **Never put full saved article text behind a public link:** copyright, plus NewsBank/State Library terms. He chose to keep the GitHub repo private for this reason.
- **Model policy** (MODELS-v1): Haiku for search and fetch loops and bulk checks; Sonnet for building and mechanical fixes; Fable only for judgment, at checkpoints. Fable tasks have cost 170–210k tokens each. He asked to "optimize token use" and to use Fable "only when necessary." A Fable reviewer sees code, rules and test results, never the builder's notes.
- **Fix whole classes, not instances.** A change goes to the code, the Update pipeline and the sheet. Don't run the full test suite on every fix: run the tests the change touches, and the full suite once at the end. No interim publishes or interim sheet writes during a build.
- **Look:** keep the tracker looking like today's. TABKEEP-v1: tab work only tweaks existing behavior. List each change as fix, tweak, or "needs approval."
- **Comments:** answer artifact comments in their own threads; resolve one when the fix is live, and leave it open if only partly fixed.
- **Report permission denials plainly;** never route around them.
- **Docs:** keep HANDOFF, DECISIONS, CONTRACT and BOARD current with every change.

## 3. Inclusion and data rules (easy to miss)

- **Who counts.** Coverage of Jesse Gabriel the Assemblymember (AD-46) only. Pre-office coverage of the same person counts: ASUC president, lawyer, Jewish Federation. Wrong Gabriels are removed (Ugarte, Petek, San Gabriel). His name in another script counts (가브리엘, Габриэл, גבריאל, 加布里埃尔).
- **His own channels never count:** his YouTube, office posts.
- **Pure press releases** stay in the sheet with `Press release` = Yes, in a red row, but are not shown in the tracker. That covers PR wires, US Fed News, PublicNow, his office page and verbatim reposts.
- **The tracker shows Originals only.** About 3,681 stories after the 2026-10-30 save. Sammy once saw 4,500 at some point, then 3,460, asked, and accepted it.
- **Not coverage:**
  - comments, teasers and tag lists;
  - calendar listings, results tables and slate-only voter guides;
  - database, listing and sitemap pages;
  - bill-only coverage;
  - californiafiles.org.
- **Still coverage:** voter guides with a written assessment, and staff-only mentions.
- **NewsBank text missing his name is NOT grounds for removal,** because NewsBank drops captions and guest lists. A full text on file that lacks him is grounds. Photo captions count as part of the article.
- **E-paper, flipbook and page-viewer URLs are print pages, not stories.** They go to `print_pages` for clipping (Sing Tao, 2026-10-30).
- **Mention depth:** Featured, Quoted, Named, List-only, or blank.
  - List-only is strict: every sentence naming him is a roster. It's kept but left out of headline counts unless "Include list-only mentions" is on.
  - Blank depth still counts as coverage.
  - Depth and Quoted must agree (DEPTHQ-v1).
- **Quoted = Yes** only for his own words in quotation marks attributed to him. "Gabriel's office said" doesn't count, and op-eds by him stay blank. `quoted_him` misses quotes with a comma before the party tag ("said Assemblymember Jesse Gabriel, (D-Encino)"), relative clauses, and print-OCR line wraps.
- **Broadcast (REVIEW4-v1, Sammy's answers):**
  - Pacific dates;
  - air time shown as the segment time plus an offset, e.g. "about 8:35am PT, 1h 35m in";
  - he as guest = Featured, and his on-air speech = Quoted;
  - one story per broadcast, with captures folded as editions;
  - station programs = Radio, independent shows = Podcast, station video = TV.
- **A Pacific-dated row whose details still carry ET gets converted to PT twice.** Re-dating a row without rewriting the Aired time causes this.
- **Reprint rule:** runs of 25 or more identical consecutive words must cover at least 90% of BOTH texts. It is not a similarity score. Up to 120 edge words at each end may be set aside.
  - Text matches get a 90-day window; headline-only fallbacks get ±7 days.
  - Old splits are never auto-merged: the merge list goes to Sammy.
- **Set aside only known clutter** (NewsBank header and citation block, "Saved YYYY-MM-DD", ProQuest lines). Broad phrase triggers have deleted real syndicated text.
- **Same outlet, web and print, = ONE row.** Never call it a reprint or text-test it. Print data goes in Print Article ID, Print date and Page.
- **Choosing the Original (REPRINT-v2 order):**
  - never an unverified row, a release service, an aggregator or a distributor;
  - then the credited service ("appeared first on…", "(KTLA) —");
  - then the reporter's employer on that date;
  - then the originator-type outlet, then byline, then date.
  - Never a date-only swap inside one house. House names (SCNG, BANG, McClatchy, TNS) are not services.
- **Originators on blocked sites** (LA Times, Bee, Chronicle, KTLA, Politico, members-only CBM, CNS) become no-copy Original rows (NOCOPY-v2). Dedupe first.
- **Aggregators** (Yahoo, MSN, NewsBreak) never become the Original or anyone's employer (AGGORIG-v1). Blended stories, local copy wrapped around wire paragraphs, stay their own story with a "uses wire copy" note (WIREBLEND-v1).
- **`Reprint (unverified)` rows** are hidden in the tracker but kept in the button's dedupe index (HIDEUNVERIFIED-v1).
- **Translations are a Reprint** only when credited or by the same byline, within 2 days, with a matching translated headline.
- **Korean outlets** can be dated a day after US outlets; that gap doesn't decide order.
- **Dates** (DATES-v1) are the calendar date in the outlet's local zone, Pacific by default. Trust order: displayed date line, then metadata, then URL, then the NewsBank record. Never the save, lastmod or updated time.
- **Date edge cases:**
  - station video pages have no date for the main clip, so never date from sidebar videos;
  - archive.org TV is dated by Pacific air date;
  - Pasadena Now: use its "Published on" line;
  - no dates after today or before 1990 ("by June 1, 2028" is a deadline);
  - `--today` is always America/Los_Angeles.
- **Outlet names use NewsBank style** ("Sacramento Bee, The") and fold through `outlet_rules.json`.
  - Raw domains are never outlet names.
  - Shows are not outlets, except podcasts.
  - Publisher = the owner at the row's date.
  - Location = the outlet's home.
- **Reach labels:** 10 values, one retired ("Spanish-language & ethnic" is never output).
  - New rows take Reach only from the same outlet's consensus; brand-new outlets stay blank (AUTO-v1).
  - REACHFIX-v1 `reach_guard` stops a bad label spreading. A wrong "California regional & local" once spread to national and trade outlets.
  - SF Chronicle = Statewide California.
- **Authors:** split into Author 1–9 plus Author title.
  - Group bylines ("Editorial Board", "Staff") are authors; kind-of-article bylines ("Editorial", "Opinion") are not.
  - CMS account labels aren't bylines.
  - A reporter's outlets come only from their Original stories.
- **Tone:** five-point toward Gabriel, rated on Originals only, using TONE_GUIDE. Straight news is Neutral.
  - Full-text ratings overwrite excerpt ratings (an explicit override).
  - No-text stories are rated only when the headline names him.
- **Topic:** exactly one of 16 labels.
- **Bills:**
  - come only from `gabriel_bills_leginfo.json`;
  - coauthored bills count only when tied to him;
  - budget trailer bills never count;
  - never tagged before the bill's introduction date.
- **Press releases:**
  - in scope: everything on gabriel.asmdc.org, plus Jewish Caucus releases from 2020-11-18;
  - a row carries a release only if its saved text passes the reprint rule against the release, dated −1 to +30 days. With no saved text it's untestable: listed, never marked.
  - PublicNow truncated-title reposts count as copies.
  - Releases by other organizations aren't shown.

## 4. Workbook quirks

- **Tabs:** Coverage, Originals (a mirror of Coverage's Original rows; rebuild after any Coverage change), Bills, Press releases, Audio & video details, Removed, Unlinked print pages. Read columns by header name; `covcols` is the order authority. HANDOFF's "67 columns" is stale.
- **IDs:**
  - Article ID is a plain 5-digit number, with ONE sequence across Article ID and Print Article ID;
  - Story `sNNNNN`, Release `prNNNNN`;
  - Removed IDs are never reused;
  - IDs are assigned only by `sheet_task.py`, never by hand;
  - the old `jg-xxxxxx` codes live in `Tracker story code`, and 101 legacy codes in `sid_map.json` must survive rebuilds.
- **Formatting:**
  - every font black; a red whole-row font (00C00000) means the row is hidden in the tracker;
  - header navy 132A4A, white and bold; panes frozen at C2 (D2 on Press releases);
  - edit cells in place with openpyxl, and never rebuild a tab.
- **Recorded overrides of fill-blanks-only:**
  - Reach relabel;
  - full-text tone;
  - ID migration;
  - Language from text;
  - Gabriel-mention No → Yes;
  - RETRY/BLOCKED placeholders;
  - `# of reprints` (always recomputed);
  - Word count from saved text;
  - Show/program cleanup;
  - Press releases cleanup;
  - Publisher corrections;
  - the Press releases derived columns (Has copies, Copies (rows), First copy date, Related count, Related story IDs), recomputed every run.
- **Hyperlinks:** openpyxl preserves them. Removing a row once shifted every link below it up by one (65 bogus A&V links). Use `delete_rows_keep_links`.
- **Removed tab:** rows move here with From tab, Reason, Removed on and Category. It already held 3 duplicate IDs and a blank Story ID.
- **Audio & video tab:** one row per broadcast Coverage row. Channel is the carrier, and Show holds only real program names (`avtab.guard_show` enforces this). Blank means unknown; never guess.
- **Static tabs:** Bills and Press releases aren't refreshed by the save step, except the derived columns. Bills is keyed by its first four columns.
- **Unlinked print pages:** 1,443 citation-only pointers. ID readers must read this tab too.
- **Excel lock file:** `~$AJG Coverage - NewsBank.xlsx` in the library folder means the workbook is open in Excel.
- **Hand edits:** Sammy downloads the workbook, edits it in Excel and uploads it back. Accept it as the new baseline after telling him (approved, SAVER-RULES-v1 answer 2).

## 5. Saves

- **Today a save is chat-driven.** Sammy says "save the last run to the sheet," and Claude follows `code/sheet_task_prompt.md`, about 30 steps: read the db collections, stage and back up the workbook, run `sheet_task.py` (`--copies-needed`, `--release-candidates`, main pass, `build_data.py`, `relmatch.py --update`, `--after-relmatch`), commit to the Mac, write back to the db, rebuild and publish.
  - Exit codes: 0 ok, 2 verify failed, 3 nothing queued.
  - Which run: the newest with rows and no `sheet.written: true`.
- **The 2026-10-30 save of run-mvvcnrpbuuz was the first complete live save ever.** Before COLDSTART-F1, `verify()` failed every real run because of the Print Article IDs on folded web+print rows.
- **What that run had and what happened to it:**
  - 19 proposed rows: 10 accepted, 5 fixed and 6 dropped.
    - Fixed: KIIS and KFI made reprints of s02206; Marin IJ and Santa Cruz Sentinel made reprints of s00327; LA Magazine re-dated to 2020-11-18.
    - Dropped: Colion Noir and Tistory (NOBLOGS); Telegraph (a staging mirror of 01859); Cool Down (doesn't name him); Hankyung (already 08031); Sing Tao (e-paper).
  - Plus 4 stories found outside the run: Newsroom America, Organiser, Massis Post, News.am.
  - Net: 16 rows added and 24 library files. The tracker went to 3,681 stories.
  - Every problem traced to dedupe and date extraction, not Claude's judgment.
- **Bugs from that save:**
  - Article shards were copied one folder too deep (`copies/articles/articles/`), so relmatch read stale shards. pr00230 and pr00236 have a `bill` related-entry that should be `text`; the next save fixes them.
  - The Organiser page was skipped once because its name line was missed on first extraction.
- **Problems with the hand procedure** (found by Fable):
  - backups named only by mtime, under two naming styles;
  - the workbook is checked by size and mtime, never by recorded checksum;
  - the exceptions list omits the Press releases derived columns;
  - step 5 deletes db docs despite the no-delete rule;
  - the pipeline is re-fetched every save with no checksum, so a missing module silently disables a rule.
- **The master was once overwritten by a stale file** (2026-10-29) because a commit reused the master's file name. Staged files must have unique names.
- **Failure between commit and write-back:** the run gets re-applied next time, and link-less rows (no-copy originators, TV clips) can duplicate (B10, unfixed).
- **Approved save rules** (SAVER-RULES-v1, Sammy 2026-10-31):
  1. Save without a preview when there are no judgment items and no changes beyond the exceptions.
  2. Accept his own Excel edit as the new baseline.
  3. Skip and list library name collisions.
  4. A release that still needs a fetch no longer holds the run: save the rest, and that release's marks fill later.
  5. Keep only the 3 most recent backups the saver made. After the first confirmed save, older pre-saver backups go to `Backups/_to_delete/`.
  6. A lock is stale after 30 minutes.
- **When the saver refuses:**
  - the checksum isn't the last recorded one;
  - Excel has the workbook open;
  - a lock is held, or the previous save was never confirmed;
  - verify fails;
  - row counts don't add up;
  - a filled cell changes outside the exceptions;
  - a new row has an ID `sheet_task` didn't assign;
  - a tab, header, link or key row would be lost;
  - the backup's or the master's checksum doesn't match.

  On refusal nothing changes, and the run stays queued with "Not written: <why>."
- **Saver code status:** a saver program (`saver.py preview|save`) was started from these rules. Its change-checker failed Fable's review with 5 gaps:
  - hyperlink targets aren't compared;
  - no identity check on new A&V and Removed rows;
  - `removed_move` is accepted for rows already on Removed;
  - links on moved and header rows aren't checked;
  - a lock-takeover race.

  It now lives in the separate GitHub project.
- **Lookup cache:** the 2026-10-30 save produced 5 new lookups, which were merged into `lookup_cache.json` and published.

## 6. The Update button (what the station inherits)

- **The flow** lives in `code/tracker/40–43_update_*.js` and runs in the viewer's browser.
- **Buttons:** "Update database", "Refresh from files" and "Save to sheet." None fires anything; each ends by telling Sammy to ask Claude in chat. Update and Refresh first show a confirm dialog (RUNCONFIRM-v1).
- **Since date** (SINCE-v1, Sammy asked for it): an optional field in the dialog.
  - Blank means "from `searched_to`."
  - A manual date filters every search, including `site:` searches. It doesn't advance `searched_to` and turns off the older-page sweeps.
  - SINCE-v2 limits per-outlet searches to outlets with a story in the last 24 months.
  - Plan sizes: about 710 calls by default; about 500, 506 and 533 for 7, 30 and 90 days. The first version cut nothing (713 vs 710).
- **Order of work:** release check first (gabriel.asmdc.org plus Jewish Caucus Press Release items). The oldest 5 new releases are fetched and the rest wait.
- **Searches:** TinyFish keyword and `site:` searches cover his name in several scripts, recent bills, per-outlet passes, `fresh` OR-groups, release pickups (up to 8 open releases × 3 searches), and late pickups.
  - No issue-word searches and no "D-Encino" searches.
  - The YouTube pass was removed (NOBLOGS).
  - GDELT isn't wired in: marginal recall, an English index and heavy 429 rate limits. It found 2 new stories in 3 months.
- **Rate:** about 30 calls a minute. The `TF_GAP` of 2.1 s and a global gate serialize all calls, so the "two workers" never overlap. A run takes at least 25 minutes and can be over an hour.
  - Searches start 7 days before `searched_to`.
  - `searched_to` advances only when 2% or fewer of calls failed. The real run had 86 of 722 failed (12%), so it didn't advance. `U.failed` mixes search, fetch, TV and Google News failures.
- **Fetching:** TinyFish `fetch_content` in batches of 10, after free pre-filters: already in the sheet, blocked host, skip URL, no Gabriel and no bill in the snippet, cached dead link.
  - A failed batch used to drop 10 candidates silently; there's now a retry (REQ-6).
- **Hosts that block:** AP, SFGate, NPR, CNN, California Black Media, LA Times, Politico, NYT, WaPo, Bee, Center Square, Daily News, Chronicle, OC Register. Mark them `BLOCKED – TinyFish`. Blocked or paywalled finds become no-copy rows (PAYWALL-v1). The leginfo check is often bot-blocked.
- **Claude via `sample`:**
  - a quick screen: 25 finds per call, title plus 700 chars;
  - a default-tier classify: 20 per call, 1,800 chars each;
  - headline translation.

  If sampling is denied, `guessRow` rows aren't added. Without `sample`, the station can't classify.
- **The page never decides reprints by text** (BUTTONOPT-v1); `sheet_task.py` judges everything. Rows are proposed in `covcols` order with placeholders, plus `_page`/`_origin` docs.
- **Page-side dedupe** (`covHit`, `dupOf`, `covRepKnown`): headline Jaccard of at least 0.7 within 14 days against the `rows` block. A blocked find with no text needs a headline match of at least 0.8 within 7 days and one outlet house before it becomes a new Original (REQ-14).
- **Other behaviors:**
  - pages aren't cleaned in the browser, so previews right after Update show clutter;
  - removal requests are executed at save (category "5 removed in the tracker");
  - outlet-sweep finds dated more than 180 days before the since date are labelled "outlet backfill";
  - the Update panel lists "N print pages to clip," with a copy button.
- **TV and Google News:** TV comes from the archive.org TV News API via TinyFish, one clip per station per day. The Google News RSS feeds returned 0 items in the real run, so the feed URLs are suspect.
- **Persistence** (REQ-2): a heartbeat run doc at start and every 25 searches, with a `localStorage` fallback. Before this fix, a closed tab lost a whole hour's run.
- **A run closes** only when `ids` is set or `sheet.written` is true. Orphan `og-`/`rp-` page docs used to make every later run stage and write nothing; fixed (REQ-7).
- **Fable's review of the button (2026-10-30):**
  - Applied or built: REQ-1, 2, 3, 6, 7 and 9–14.
  - Skipped: REQ-15 (approval flag on the scheduled task), replaced by NOSCHED-v1.
  - Not built and not decided:
    - the weekly-watch/monthly-backfill split, estimated at about −80% calls;
    - a checkpoint "Resume";
    - a deterministic driver;
    - per-host caps;
    - stripping `_text` from run docs;
    - a `found_by` column;
    - LegiScan/OpenStates, Podcast Index, Google Alerts RSS, outlet RSS, and seeding from the Ethnic Media Services directory.
  - Unfixed bugs:
    - B7: leginfo waits;
    - B10: link-less rows can duplicate;
    - B11: workers never overlap;
    - B12: the 2% rule mixes failure types.
- **Podcast and radio search was deferred.** Untitled TV segments are a known gap.

## 7. Database (artifact `db`)

- **Tracker collections:** runs, edits, tones, authors, translations, pages, reprints, notes, clips, views. Review queue: items, decisions, applied (QUEUEAPPLY-v1 applies only decided items the sheet task created itself).
- **Run docs hold `_text`,** up to 6,000 chars per row, so they get large.
- **Migrating to any new artifact:** export every collection and re-seed with `batch` (50 writes a call, same doc ids) before anyone presses Update. Press "Save to sheet" first, so `pages` and `edits` are empty. See `code/db_reseed.py` and `db_export/EXPORT_CHECKLIST.md`.
- **Per-viewer browser storage can't move accounts:** `jg-tones`, `jg-authors`, `jg2-notes`, `jg-runs-pending` and IndexedDB `jg-archive`.

## 8. Tracker page quirks (to keep the look)

- **Tabs:** Home, Clips, Data, Reporters, Outlets, Press releases, Bills, Story travel. Routes are hash URLs, with filters in the URL. Search tabs open with filters cleared (DEFCLEAR-v1). Header Back/Forward buttons walk in-page history.
- **Home** is one line: "N stories in the last 30 days, up/down from M…; led by <issue>." No weekly tiles.
- **Data:** collapsible sections. "Include list-only mentions" must apply from first load: a bug once made the counts flip from 3,518 to 3,672 (DATABASIS-v1).
- **Clips search:** every word in any order, whole words or word starts. It reads the CLEANED library text, and the placeholder says "Indexing saved pages…" until the index is ready.
- **Links:**
  - CSL NewsBank/ProQuest links (they work and need a State Library login), the publisher link, and archive.org TV links;
  - no links on reprints, except the per-copy links on the Story travel pickup ladder;
  - a copy icon sits left of every link.
- **Corners:** the table header corner took many attempts; Sammy: "You have tried so many times to no avail."
  - The real cause, found only by testing in WebKit: the sticky header's rounded corners notch while pinned. The fix (STUCKCORNER-v1, `98_stickycorner.js`) makes them square while pinned.
  - Safari also ignores cell border-radius under `border-collapse`; fixed with `separate` (CORNERS-v3).
  - Test visual fixes in the real browser engine, which for the PC is Edge/Chromium.
- **Release dots** (RELDOTS v1–v4): on the bill "Milestones and coverage" charts, press releases are orange (`--s2`) dots on their own row just below the milestone dots, so they never overlap. Only press releases are orange. There's a "Press release" legend entry, a tooltip, and a click opens the release page. Sammy iterated on this four times.
- **Charts and maps:** no single-bar charts; Story travel spread curve only with 3+ pickups on 3+ days; one adaptive time-axis helper; one map component for CA counties and US states.
- **Release pages:** Ran the release, Related, Later coverage, Other releases on this bill, Possibly related. Rules sit behind an ⓘ tooltip. `release_related.json` is merged and never shrinks.
- **Phone layout:** the bottom tab bar was dropped (NOPHONE-v1).
- **Build:** `code/tracker/NN_*.js` → `apply_all_patches.py` → `build/js_merged.js`. Never hand-edit `js_merged.js`, which has a guard checksum.
  - The published `pipeline/` must rebuild the page byte-identically: the LIB build sha equals the PIPELINE build sha.
  - Pipeline `.py`/`.js`/`.html` files publish with contentType text/plain.
- **Media:** the sharing review refused `<video>`, `<audio>`, `<iframe>`, `<svg>` and similar in copies, so MEDIAGATE strips them, converts svg to PNG, and `make_copies.py` exits 4 on a leftover.
- **Shared copy** (VIEWER-v1): `make_viewer.py` moves data into `data/*.json`, hides Update, Refresh, Save and downloads, has no capabilities, and is titled "(Shared)." Refresh it after every tracker publish. It exists because a page that declares mcp can't be link-shared.

## 9. Library and saved copies

- **File names:** `<nb|pq|ws><NNNNN><o|r>-s<NNNNN>.<html|pdf>`. The o/r suffix appears only in file names, and some are stale after swaps.
- **Cleaning** (`clean_html.py`): remove only what clearly isn't the article. If more than 35% would go, keep it and flag it. The raw page goes to `_original_html/`.
  - A header line is removed only when the sheet has the same value; if the sheet is blank, fill it.
  - Provenance lines ("Saved 2026-10-28 (…agent-calmatters)") are meant to be stripped from all copies. Still open.
- **Error copies:** listing pages, paywall pages, 404s or the wrong article become `RETRY – TinyFish` or `BLOCKED – TinyFish` with `Saved Copy?` = No. A later good copy replaces the placeholder.
- **Which copy the viewer shows:** the Original's own HTML, then its NewsBank text, then another row's HTML. Known-wrong copies are in `wrong_copies.csv`.
- **Photos** (PHOTOS-v2) are embedded in saved copies: largest srcset up to 1,000 px, JPEG at quality about 0.75; ads and logos dropped; failed images removed with their wrappers, captions kept.
- **NewsBank print clips:** a full-page PDF plus jump pages, OCR'd, saved via the CA State Library proxy (`infoweb-newsbank-com.castatelib.idm.oclc.org`). Sammy logs in himself. Paused at 28 rows.
  - Browser quirks: the search box needs real keystrokes, and Fit to Screen needs a real click.
  - pdftotext drops the hyphen in docrefs (`%40\d{7}-HEX16`).
- **Release copies** live at `Press releases/<year>/<prid>.html`.
- **LIBCLEAN-v1** (Sammy: "whatever you think is best") deleted 282 files, 463 MB: old backups, superseded bundles and exact duplicates. Lists are in `_archive/`.
- **Known gaps:**
  - 38 stories have a "-v2" saved page that differs from the published copy;
  - 7 `Saved Copy?` = Yes stories have no file;
  - the live article shards are one `make_copies` generation behind the code.

  Publish `articles/*` as shipped; a rebuilt set is a check, not a source.
- **Never scratch inside the library.** Durable work products are mirrored add-only to `Work archive/<date>/` with a MANIFEST.sha256.

## 10. Things that went wrong (and the lesson)

- **The Mac link** (the bridge from Claude's cloud workspace to Sammy's Mac) dropped over and over. Every save depended on it, and that's the main reason to move off it. The bridge can also return a stale cached copy, so confirm checksum, size and mtime.
- **Publishing to artifacts:**
  - refused when files weren't read first in that conversation;
  - `edits` can't be combined with `files`;
  - JS pipeline files need contentType text/plain;
  - large publishes go in batches;
  - re-sending identical content once clears the conflict guard.
- **A build ran mid-edit and missed changes.** Regenerated copies lost content and had to be merged back from the live shards.
- **The scheduled task fired despite being disabled** (see section 2). That's why there's no scheduling at all.
- **The storage cap:** the artifact reached 249.6 MB of 256 and was repacked to about 203 MB.
- **Story-count drop** from about 4,500 to 3,460. Sammy questioned it and accepted it after an explanation. Expect him to watch the count.
- **Replay false positives:** a byline-stamp rule flagged 216 rows, and the first headline auto-merge had 37 false positives of 193. Both were narrowed (the merge to within one house and 2 days).
- **Hot-fixes made by hand-editing `js_merged.js`** tripped its guard. Edit the `NN_*.js` sources instead.
- **Agents often lacked the file-commit tool,** so the coordinator committed their staged files.
- **One test agent made an unrequested network request** while checking an offline guard. Tell agents explicitly when the network is off-limits.
- **Google Drive was ruled out for the workbook.** Its connector passes files through the chat as base64 (a 7 MB file is about 9 MB of text) and can't replace a file's contents.
- **The first desktop-app plans** (Tauri plus an MCP connector, then Fable's portable Python plus Claude Desktop extension) stalled because IT probably won't allow installs or extensions. The Fable plan's IT questions still apply to your design: python.exe from a user folder, `.mcpb` extensions, and Claude Desktop itself.

## 11. Unfinished work and open questions (ask Sammy; don't assume)

- **Data questions:**
  - A5 wire-blend pickups: count them everywhere or nowhere (3,168 vs 3,169)?
  - 4 unsettled F7 rows: 09721, 01734, 06948, 06949.
  - 8 medium-confidence date fixes (`work/out/web_dates_2026-10-30.csv`).
  - Add full versions of 4 thin saved copies?
  - Patch rows 00740 and 04889; Korea Daily Times.
  - The 7 existing NOBLOGS rows: list them for him before removing any.
  - The Independent story's date is blank because its page is blocked; GDELT saw it on 2026-09-30.
  - Tone and Topic are blank on Newsroom America and Organiser.
- **Update cadence:** a weekly watch plus a monthly sweep? (Fable's watch/backfill split.)
- **NewsBank alerts:** Sammy might set them up. A Gmail label could be read on request; how alerts would feed the tracker was never settled.
- **TinyFish needs re-authorizing** before web lookups.
- **Also open:**
  - 19 blank reaches;
  - 71 blank Topics;
  - 12 `# of reprints` disagreements (`work/out/repcount_not_written_2026-10-30.csv`);
  - 14 podcast Publisher-link mismatches;
  - about 380 McClatchy no-copy rows with no Publisher link;
  - review-queue origin items (13 new pairs, 93 medium, 79 low);
  - old-window merges (list for Sammy);
  - CHAINORIG medium and low tiers;
  - author nickname parentheticals;
  - Bills group subtitles;
  - the "Uses release text" tag;
  - the per-release search for pr00244 (Sepulveda);
  - a Safari corner check.
- **Handoff kit and docs:** they need a refresh after the last publishes. Sammy asked for "the handoff kit, the library refresh, and the project docs sync," and these were done once, but the 2026-10-30 save and later decisions aren't in the kit.
- **Not answered:** Fable's Windows plan's 10 decisions and the first draft's decisions. Most no longer apply, but the IT questions do.
- **Never answered in surviving notes:** whether the Update button fits within a free Claude plan's limits. If the station page is used on a lower plan, check what `sample` and the connector calls cost.
- **The shared copy** is still private; recipients need access from its Share menu.
- **Not discussed with Sammy:** the zip format, the PC import, where the PC master lives on the share, the sync from PC back to the station, photos, and how colleagues share notes and edits offline. All open.
