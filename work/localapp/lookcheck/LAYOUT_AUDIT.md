# Layout audit of the tracker page (report only, no code changed)

Date 2026-11-03. Asked for by Sammy: "clean up all of the headers and buttons, make sure everything is centered properly, etc. There are little gaps between where it says release and the edge. Same thing with outlets and reporters screen as well." Plus two additions: put "Tracker files" in the masthead next to Manage, and list features that could be simplified or removed.

Nothing was fixed. Every number below was measured in Chromium (what Edge is built on) with Playwright, at 1440x900 and 960x1040, light and dark.

Where the pictures are: `S/layout_audit/` with `S` the scratch folder the check ran in. Crops are in `S/layout_audit/crops/` (zoomed 2x, some 4x). Full-page screenshots are in `S/layout_audit/shots/` (`pc_` = the PC build, `live_` = the live v65 files; `d` = 1440, `n` = 960). The measuring scripts are in `S/layout_audit/tools/`, the raw numbers in `S/layout_audit/scan.json`.

What was audited:
- The PC test build `S/app_build_pcedits2/linux/AJG Tracker` (a working copy, started on port 8911).
- The live reference `S/live_v65` (static server, port 8912).

## IMPORTANT: the PC build I was given is older than live

`app_build_pcedits2` was built before the RELXLOOK-v1 fix reached it. Its release page still has the old "Later coverage" / "Possibly related" boxes (class `card pad tbe-extra rl-sec`, no `rl-xcard`), while live v65 and the newer builds (`app_build_v65`, `app_build_v65p`) have the fixed ones. The repository source (`build/tabs/releases.js:379-382`) already has the fix. So problem 1 below exists only in the PC build, and a rebuild removes it. Everything else exists in live too (the two pages are pixel-identical apart from the hidden buttons).

---

## A. The gaps Sammy named (Press releases, Outlets, Reporters)

### 1. Release page: "Later coverage" and "Possibly related" tables sit inside a padded box with no header padding (PC build only)

- Where: Press releases > open a release (for example pr00208) > Later coverage; and the "Possibly related" box under it. Selector `.card.pad.tbe-extra.rl-sec table.db.tbe-xtab`.
- What is wrong: the navy header bar is a thin strip (16.9 px high, live has 34.9) that starts 18 px inside the card and stops 18 px short of the right edge. The words DATE and REPRINTS touch the ends of the bar (header cell padding 0 px; live has 12 px). The bar's rounded ends clip the first and last word. It does not match the Related list above it, whose bar fills its card edge to edge.
- Measured: card 16 to 1424; header bar 35 to 1405 (gap 18 px + 1 px border on each side); header cell padding 0/0 (live 9/12); header height 16.9 (live 34.9).
- Live has it too: no. Live (v65) has the RELXLOOK-v1 version: `.card.rl-xcard`, header bar 17 to 1423, padding 9/12.
- Picture: `crops/later_coverage_pc.png` (PC) against `crops/later_coverage_live.png` (live).
- Likely cause: the PC build's pipeline copy of `releases.js` predates RELXLOOK-v1 (source line `build/tabs/releases.js:379-382` has it). The CSS `#tbBody table.db.tbe-xtab thead th{padding:9px 12px}` is in `code/tracker/53_tabs.js` (relui-css, about line 1285) but the old markup never reaches it.
- Fix: rebuild the PC app from the current source (`assemble_app.py`) so it carries v65. Risk: none beyond a normal rebuild; the look check must be rerun because lookcheck last ran against older files.

### 2. Pinned header: a thin pale line frames the navy bar on both sides (Press releases, Outlets, Reporters, Clips, Bills, Story travel; every table)

- Where: every list table while its header row is pinned under the masthead (and at rest, on the left, right and top). Selector `.card > .tablewrap > table.db thead th`, the card is `.card` with `border:1px solid var(--line)`.
- What is wrong: the navy header bar is 1 px smaller than the card on each side, so a 1 px light line shows to its left and right (and above it at rest). It reads as a "little gap" between the word RELEASE and the edge: the navy does not reach the edge of the card. The masthead above it runs the full window width, and while pinned the bar looks cut in by 16 px against it with a pale hairline beside it.
- Measured: card x 16 to 1424, header bar x 17 to 1423. Pixels at the left edge: page background (237,240,245), then 2 device pixels (= 1 px) of (211,218,228), then navy (19,42,74). In dark theme the line is (36,52,77) against navy (19,42,74). Same at 960 wide (card 16 to 944, bar 17 to 943).
- Live has it too: yes, identical.
- Picture: `crops/rel_pinned_both.png` (pinned, left and right ends), `crops/pin_edge_light.png`, `crops/pin_edge_dark.png`, `crops/rel_hdr_both.png` (at rest).
- Likely cause: `.tablewrap` sits inside the bordered card (`build/shell/shell.html:85` `.card{border:1px solid var(--line)}`), and `table.db th{background:var(--navy)}` (`shell.html:216`) cannot paint over the card's border. The 9 px header corner radius (`shell.html:218`) is meant to sit in the 10 px card radius.
- Fix, one line: give a card that holds a table a navy top border (`.card:has(>.tablewrap>table.db){border-top-color:var(--navy)}`) and let the pinned header overhang by the border width (`margin-inline:-1px` on `.tablewrap` for the header only). Risk: medium. The same spot has had many corner attempts (STUCKCORNER-v1, CORNERS-v3), and sticky plus overflow clip is fragile. Test in Edge/Chromium and WebKit, light and dark, pinned and at rest. An easier, safer choice is to colour the card border itself a touch darker so the line stops reading as a gap.
- Not certain this is exactly what Sammy means. If he meant the Later coverage boxes (problem 1), that one is much more visible. Ask him to point at one spot.

### 3. Outlets at 960 wide: the whole page grows to 1131 px and scrolls sideways

- Where: Outlets tab (also the outlet-page lists are fine). Selector `#view-tb .tt`, `.tt-head`, `.grid-clips`, `.card.tt-list`.
- What is wrong: the 10-column table cannot get narrower than about 1114 px, so the card, the heading, the search box and the Export button are all stretched to 1114 px. The page scrolls sideways, the long description line is cut off at the window edge ("...where the owner changed" runs off), the search box and Export run off the right side, the Top reporters column is out of sight.
- Measured: `documentElement.scrollWidth` 1131 against `clientWidth` 960; `.tt-head` right edge 1130.6; `.tt-h1` right edge 1128.6; card 16 to 1130.6. At 1440 it is fine (1440/1440). Reporters at 960 is fine (960/960).
- Live has it too: yes, identical.
- Picture: `crops/outlets_960_top.png`; full page `shots/pc_n_light_outlets.png`.
- Likely cause: `.grid-clips{display:block}` at `build/shell/shell.html:624` (the "filters live in a drawer at every width" rule) makes the grid item's minimum width the table's minimum width; `.tt` is a one-column grid (`code/tracker/53_tabs.js:239`) whose track grows to fit. `.tablewrap` uses `overflow-x:clip` (`shell.html:214`), which clips but does not scroll and does not stop the growth.
- Fix: add `min-width:0` to `.tt>.grid-clips` and `.tt>.tt-head`, and let the table drop or shrink columns (hide Publisher or Top reporters below about 1100 px, as the release list already hides a column under 760 px). Risk: medium. With `min-width:0` alone the table would be clipped, not scrollable, because the tablewrap is `overflow-x:clip` to keep the sticky header. Needs a column-hiding rule, tested on all four list tabs.

### 4. Reporters and Outlets "Top issues": commas and counts land alone on a line

- Where: Reporters > Top issues column; Outlets > Top issues column (build/tabs/reporters.js:163 and outlets.js:173). Selector `td` in `table.tt-tab`.
- What is wrong: the issues are joined with ", " as inline links, so a line can start with a comma (", Guns", ", Other / roundup,") and a long issue name wraps in the middle ("Antisemitism / Jewish community"). In Outlets the count ("18", "31") drops under its issue name onto a line of its own. The result is ragged and looks misaligned.
- Measured: at 960 the Reporters column is about 130 px wide; rows 1, 3, 6 and 7 start a line with a comma. At 1440 Outlets, rows 2 and 3: "Antisemitism / Jewish community / 18" takes 4 lines.
- Live has it too: yes.
- Picture: `crops/reporters_960_issues.png`; `shots/pc_d_light_outlets.png` (Top issues column).
- Likely cause: separator `.join(', ')` in `build/tabs/reporters.js:163`; the Outlets cell puts each issue and its count as separate inline items (`outlets.js:173`).
- Fix: make each issue a non-breaking chip (`white-space:nowrap`) laid out as a stacked list (`display:grid;gap:2px`), no comma. Risk: low to medium. Rows get taller or shorter, and a CSV or "Show the numbers" that reuses the text is not affected, but this changes the Reporters tab look (TABKEEP-v1: it is a tweak, list it for approval).

### 5. Heading block of the list tabs is indented 2 px more than the table and controls

- Where: Reporters, Outlets, Press releases, Bills, Story travel. `.tt-head` (title, description, "About this list", summary line).
- What is wrong: the title "Reporters", its description, "About this list" and the summary sentence start at x = 18, but the Filters button, the "1,393 of 1,393" count and the table card start at x = 16 (and Home's "Good evening" and the Data cards start at 16). A 2 px step that is easy to see against the straight left edge below it.
- Measured: `.tt-head` left 16, padding-left 2 px, text left edge 18; Filters button left 16; card left 16.
- Live has it too: yes.
- Picture: `crops/reporters_heading_left.png`.
- Likely cause: `code/tracker/53_tabs.js:241` `.tt-head{...padding:4px 2px 0}`.
- Fix: `padding:4px 0 0`. Risk: very low; moves the heading 2 px left on five tabs. Check the other tab heads (`.tbe-head`, release/outlet/bill pages) for the same 2 px.

---

## B. Headers (masthead and table headers)

### 6. Masthead: Back and Forward buttons are shorter than Spreadsheet and Manage

- Where: masthead row. `#navBack`, `#navFwd` (`.upd-btn.nav-hb`) against `.hdr-acts .upd-btn`.
- What is wrong: three kinds of control sit on one row with different sizes: Back/Forward 33 x 29 px, Spreadsheet 125.6 x 34.8, Manage 102.9 x 34.8. They are centred on the same line (centre y = 40), so only the heights differ (5.8 px), plus the tab bar's own buttons are 30.8 high.
- Measured as above. At 960 identical.
- Live has it too: yes.
- Picture: `crops/mast_1440.png`, `crops/mast_left_1440.png`, `crops/mast_right_1440.png`.
- Likely cause: `.nav-hb` uses padding 6px 8px against `.upd-btn` 7px 12px (`build/shell/shell.html:491`).
- Fix: give `.nav-hb` a 34.8 px height (padding 7px 8px plus a matching icon box). Risk: low; makes the left group 6 px taller, the masthead height (`--hdr` 128 px) is set by the tab row so should not move. Re-measure `--hdr`.

### 7. Masthead tab bar (found fine)

The tab bar frame runs 16 to 1424, lined up with the Back button on the left and the Manage button on the right. Tab labels are centred sideways within 0.6 px. Only their up-and-down centring is off (problem 10).

---

### 8. Table header and body columns

Measured on every list table (Clips, Reporters, Outlets, Press releases, Bills, Story travel, release page, outlet page) comparing the real text edges of header cell and body cell: left-aligned columns start at the same x (difference 0.0 px); right-aligned numbers end at the same x (difference 0.0 px); the centred Reprints columns share the same centre (within 0.5 px). The only differences are by design: Issue / Bill and Reach headers start 6 px and 15 px left of their text because a colour square sits before the text and the header lines up with the square. Found fine.

---

## C. Buttons

### 9. "Tracker files" button does not match the other buttons and covers content

- Where: bottom right of every page (`#ajgf-btn`, `work/localapp/app/src/station/web/panel.js:17`).
- What is wrong (look): it is a blue, fully rounded pill in the system font (Segoe UI/system-ui 13 px) while every other button is a rounded square (8 px) in Public Sans, with a light outline. Size 107.9 x 36 against the masthead buttons' 34.8 high. It has a drop shadow nothing else has.
- What is wrong (position): it floats over the page and hides content under it: the last column of tables (Reprints, Related, Top reporters), the pager buttons "Next", chart bars on Data, and the end of the story sheet text ("...use the links above to read it at the source").
- Measured: fixed, right 14 px, bottom 14 px, border radius 20 px, padding 9 x 14. With a classic Windows scrollbar (15 px) it sits 2 px beyond the content edge (button right 1411, content right 1409).
- The panel it opens (440 px wide) starts at y = 20 and so covers the masthead's right-hand buttons (at 1440 it covers x 986 to 1426, which includes Manage and Spreadsheet). At 960 it is 960 px high and covers the Manage panel's tab strip as well.
- Live has it too: no. The live tracker has no such button. It is the recorded exception (UPDATEFOLDER-v1, MULTIPC-v2).
- Picture: `crops/trackerfiles_btn.png`, `shots/files_d.png` (panel over the Manage panel), `shots/sheet_d.png` (button over the story sheet text), `shots/pc_d_light_data.png` (over chart bars).
- Fix: see section E below.

### 10. Text sits about 1 px above the middle in several buttons and pills

- Where: tab buttons, Filters, Compact/Export, per-page select, tone and "Saved copy" badges, bill / issue pills. Selectors `nav.tabs button`, `.btn`, `button.badge`, `.bchip`, `select`.
- What is wrong: the letters are 0.9 to 1.25 px higher than the middle of the button. Small, but together it is what makes rows of buttons look "not quite centred".
- Measured (pixel measurement of the drawn letters against the button box, 4x zoom; negative = high):

  | Control | Box (w x h) | Letters above centre |
  |---|---|---|
  | Tab "Home" | 171.5 x 30.8 | 1.25 px |
  | Per-page select | 67 x 27.4 | 1.25 px |
  | Bill / issue pill ("AB 1626") | 55.5 x 17 | 1.0 px |
  | Filters button | 65.3 x 36.8 | 0.88 px |
  | "Saved copy" badge | 84.1 x 19.9 | 0.88 px |
  | Tone badge | 66.8 x 19.9 | 0.5 px |
  | Manage (masthead) | 102.9 x 34.8 | 0.12 px (fine) |
  | Compact | 81.2 x 36.8 | 0.25 px low (fine) |
  | Tracker files | 107.9 x 36 | 0.12 px (fine) |

  Sideways, all are centred within 0.6 px. Scan of text line boxes (`scan.json`) agrees: badges -1.0, Filters -0.9, mast buttons -0.9 (line box only).
- Live has it too: yes, identical.
- Picture: `crops/tabs_1440.png`, `crops/ink_clips_tab_Home.png`, `crops/ink_clips_Filters_button.png`, `crops/ink_clips_badge_saved.png`.
- Likely cause: Public Sans' ascent is larger than its descent, so a line box that is centred puts the capitals about 1 px high; the buttons use `padding:6px 12px` with no vertical compensation (`mast2-css` in `code/tracker/53_tabs.js:577`; `.btn`/`.badge` in `shell.html`).
- Fix: add 1 px to the top padding and take 1 px off the bottom (or `padding-top:calc(var(--p) + .5px)`), per component. Risk: low but touches many components, so SAMELOOK-v2 needs sign-off (Sammy asked for it); the look check must be updated, since it compares with live pixel by pixel.

### 11. "Manage" count badge

- Where: masthead, Manage button, badge "21" (`#mgBadge`, 21.7 x 18 px, radius 9 px).
- Found fine geometrically: the number is centred in the badge and the badge is centred in the button (vertical centre 40 for both). What it means is unclear (see the simplify list).

---

## D. Centring and spacing in other places

### 12. Home: the four tiles do not line up their labels

- Where: Home, the four tiles in the top row. `button.tile` (`code/tracker/03_overview.js:40`; `shell.html:115`, `605`).
- What is wrong: "LAST 30 DAYS" and "2026 SO FAR" start 9.4 px lower than "HEADLINES IN 2026" and "MAJOR OUTLETS, 12 MONTHS". Tiles are buttons, and a button centres its content up and down, so the two tiles with a one-line note get pushed down.
- Measured: tiles all top 211.5, height 130; first label top = 242.9 (padding 31.4) in tiles 1-2, 233.5 (padding 22.0) in tiles 3-4.
- Live has it too: yes.
- Picture: `crops/home_tiles.png`.
- Fix: `button.tile{display:flex;flex-direction:column;justify-content:flex-start}`. Risk: low; the numbers in the first two tiles move up 9 px so they sit under the label in a row with the others.

### 13. Home: "Tone, last 90 days" card is mostly empty

- Where: Home, right card next to "Needs attention". The card stretches to the height of the left card (about 410 px) and holds a thin bar and two captions.
- Measured: card 727 to 1424 by 354 to 767; content ends at about y = 470, so roughly 300 px of blank card.
- Live has it too: yes. Found as a layout fact; a design choice, listed for Sammy.
- Picture: `shots/pc_d_light_home.png`.

### 14. Manage panel and "Tracker files" panel are both fixed on the right and overlap

- Where: open Manage, then Tracker files. Panels `#upd` and `#ajgf`.
- What is wrong: the Tracker files card (440 px, z-index 2147483001) sits on top of the right side of the Manage panel and covers its tab strip ("Saved copies / Data checks / Definitions") and the text beside it.
- Picture: `shots/files_d.png`.
- Fix: open Tracker files under the masthead button (section E) and close Manage when it opens, or the other way round. Risk: low.

### 15. Long text clipped by design (found fine)

Bill and issue labels in tables end in an ellipsis (`span.lab`, for example "AB 1264 Pupil nutrition: restr..."); this is deliberate, a title attribute should carry the full text. No other clipped text was found in the table cells at 1440 or 960.

---

## E. Sammy's request: put "Tracker files" in the masthead next to Manage

Measured masthead row (PC page, 1440 / 960):

| Piece | 1440 | 960 |
|---|---|---|
| `.mast-row` | x 16 to 1424 | 16 to 944 |
| Back, Forward | x 16 to 88 (72 wide) | same |
| Logo | x 104 to 349 (245 wide) | same |
| Words "PRESS COVERAGE TRACKER" | x 361 to 495 | hidden under 1180 px |
| Brand column (flexible) | 104 to 1171 (1067 wide) | 104 to 691 (587 wide) |
| Button group `.hdr-acts` | x 1187.5 to 1424 (236.5 wide): Spreadsheet 125.6, gap 8, Manage 102.9 | x 707.5 to 944 |
| Height of those buttons | 34.8, top 22.6, centre y 40 | same |

Where and how:
- Add a third `.upd-btn` into `.hdr-acts`, directly left of Manage (order: Spreadsheet, Tracker files, Manage), same class, same 34.8 px height, same 8 px radius, 13 px Public Sans 600, same white outline. Give it a small icon in the style of the Spreadsheet download icon (a folder or sheets icon). Label "Tracker files". Width about 120 px (icon 16 + gap 6 + label 78 + padding 24), so the group grows from 236.5 to about 365 px.
- At 1440: free space in the brand column is 1067 - 245 - 134 (words) = about 690 px, so it fits with room to spare, nothing else moves.
- At 960: the brand column drops from 587 to about 458 px; the logo needs 245, the words are hidden, so it still fits with 200 px spare. The layout switch comes at 920 px (`code/tracker/53_tabs.js:581`: under 920 the buttons move to their own row), and at 640 (a 2-column grid; three buttons would wrap to 2+1 there). The phone size was dropped (Sammy), so no work is needed beyond a glance.
- The "needs attention" colour (amber, `#ajgf-btn.warn`: Excel open, workbook not accepted, lock held) can become a small amber dot on the button, in the same way `#mgBadge` is drawn on Manage. Then it never competes with the other buttons.
- The floating button: remove it. The panel itself stays but opens as a card pinned under the masthead at the right (`top:132px; right:16px`, same 440 px width, max-height `calc(100vh - 148px)`), so it never covers the buttons or the masthead and the button stays visible while it is open. This also stops the overlap with the Manage panel (problem 14) and removes the covering of table columns, pager and chart bars (problem 9).
- Reader copies: show the button the same way (readers use it to bring in refresh files), same label. The panel's own text already differs ("This is a reader copy"), and the keeper-only sections hide.
- Source places to change (not changed now): `work/localapp/app/src/station/web/panel.js` (button creation at line 55 and the CSS at line 17-19; the panel position at line 19); the station server's injected hide/add rules (`HIDE_CSS`) and the look check's added-element masks `ADDED_SEL='#ajgf,#ajgf-btn,#ajgf *'` plus the fixed-position mask in `work/localapp/lookcheck/lookcheck.js`. Because the button now sits in the masthead, the masthead grid changes by about 128 px (the spacer shrinks), so the look check masks must follow the button's new place.
- Risk: low to medium. The look check compares the masthead pixel by pixel, so its rule "exceptions" must now include the new button; Spreadsheet and Manage move left by about 128 px at both sizes (they are right-aligned, so they stay put; only the spacer shrinks, as with the hidden Update buttons).

---

## F. What was checked and found fine

- Every table header: left and right text alignment against body cells, all eight list tables plus the release and outlet pages: 0.0 px differences (see problem 8).
- Header height: 34.9 px in every list table; first and last header cell reach the card's inner edge (0 px gap) in all of them at both sizes (`scan.json`, "gapL/gapR 0").
- Sticky headers when scrolled: pinned at y = 128 under the masthead (bottom 127.84) in all six list tabs at both sizes; a 2 px dark line from the masthead's bottom border separates them; no rows show through between them. Corners go square while pinned (`.hdr-stuck`); no notch seen at either end.
- Rounded corners at rest: the 9 px header corner sits correctly in the 10 px card corner on every list.
- Masthead: Back/Forward, logo, buttons and tab bar all centred on the row (centre y = 40); tabs share the width evenly (171.5 each at 1440, 111.3 at 960); the active pill is centred sideways within 0.2 px.
- Dark theme: all eight tabs screenshotted at both sizes; only the same issues as light appeared (the pale line is (36,52,77) against navy).
- 960 wide: Clips, Data, Reporters, Press releases, Bills, Story travel, release, outlet pages have no sideways scrolling (only Outlets, problem 3). The Manage panel and the story sheet fit.
- Text clipping: only the intended ellipsis (problem 15).
- Buttons in a row: Filters / search / date / Compact / Export on Clips all have the same height (36.8 / 38.3 for the search box, an intended 1.5 px difference caused by the border; the search box is centred on the same line).
- Tab text centred sideways (within 0.6 px) in every control tested.

Not tested: a real Windows Edge with ClearType and a classic scrollbar (only the 15 px scrollbar width was emulated, `shots/scrollbar_*.png`); phone widths (dropped); the Tracker files panel's reader view (read from source).

---

## G. Candidates to simplify or remove (nothing is removed; Sammy decides)

Plain words. "Who" = who would use it. These are what Sammy would see in the PC tracker.

| # | Feature | What it does | Who | Why it may confuse | Recommendation | What is lost |
|---|---|---|---|---|---|---|
| 1 | Manage > "Find & refresh" tab (first tab of the Manage panel) | Explains the old Update database / Refresh from files buttons: "about 703 TinyFish searches", reprint rules, "ask Claude in chat to save the last run to the sheet", a "Look for stories published since" date, a NewsBank reminder with "I downloaded a refresh today", "What it searches (703)". | Nobody on the PC. The buttons it talks about are hidden. | Whole tab describes things that do not exist here; says to ask Claude in chat, which is the old way. It is the first thing shown. | Hide the tab on the PC (or replace by a one-paragraph note: "New stories come from the Update station"). | Only the reading material. The NewsBank reminder date and the "downloaded today" button would go with it (the old reminder is now the station's job). |
| 2 | Manage > "Update log" | Lists every earlier update and how many stories it added; "Earlier additions" (ten items from 2026-10). | The keeper, rarely. | Says "Updates run from now on are listed here", but the PC records its own history elsewhere; says "Press Edit on any story". | Keep but rename "History", and hide the old entries; or hide. | The record of old updates. |
| 3 | Manage > "Saved copies" | Shows 3,500 of 3,681 have a saved copy; a drop zone to add saved pages or PDFs matched by file name; "Copy story code list". | The keeper if a page is missing. | Says pages added here "show only on this computer", names the Mac folder and again says ask Claude in chat. The PC's real way is the update folder. | Simplify the wording; keep the percentage; hide the drop zone and "Copy story code list" (or keep behind "More"). | Adding single pages by hand. |
| 4 | Manage > "Data checks" | Lists records worth checking: days since last clip, pages waiting for a tone rating, stories whose link is a search, outlet-name variants (782 names, 427 used once). | The keeper. | Two messages say "Press Update database" and "Press Refresh from files to have Claude rate them": those buttons are not on the PC. "Show" links open Clips filters. | Keep, but reword the two Update messages ("Run the Update station") and remove "Refresh from files". | Nothing if reworded. |
| 5 | Manage > "Definitions" | Plain definitions of issue, bills, reach, tone, author, format, reprints. | Anyone new to the tracker. | The tone line says "Claude rates tone"; the "Download the spreadsheet" link duplicates the masthead Spreadsheet button. | Keep. Light edits only. | Nothing. |
| 6 | Manage button badge ("21") | A small number on Manage. | Unclear. | A bare number with no explanation; it does not say what to do (it counts things in Data checks and notes). | Remove the number or make it a tooltip with words. | A glance at how many checks are open. |
| 7 | Manage panel: edit and remove items | "Edit details" in a story, "Manage edits" list, removals. Now saved with the next update (PCEDITS-v1). | The keeper. | Readers also see it but their edits stay in their copy only. | Keep for the keeper; for readers hide Edit and Remove (they can mislead). | Reader-side edits. |
| 8 | Tracker files panel (six numbered sections) | 1 Make "for Update" file; 2 Bring in update; 3 Save my edits; 4 Accept the workbook as it is now; 5 Make refresh file and Make FULL refresh; 6 Rebuild the tracker page. | The keeper, 1 to 3 every update. | Six steps with equal weight; two kinds of refresh; "Accept the workbook as it is now" and "Rebuild the page" are rare repair steps. | Keep 1, 2, 3 and 5 on top. Put "Accept the workbook" (rename: "I edited the workbook in Excel") and "Rebuild the page" under a closed "Repairs" fold. Rename the two refresh buttons "Refresh file for colleagues" and "Refresh file for a new person". | Nothing is lost; it is only moved. |
| 9 | Two kinds of refresh ("Make refresh file" and "Make FULL refresh") | The normal one carries the changes since last time; the FULL one carries everything for a new person. | The keeper. | Two buttons side by side with similar names and no hint of which to use. | Keep one button; make FULL a link "for a new person". | Nothing. |
| 10 | Floating "Tracker files" button | See problem 9 and section E. | Everyone | Covers text. | Move into the masthead (section E). | Nothing. |
| 11 | Clips > "Compact" (density) button | Switches row spacing. | Rarely. | A mode that changes how everything looks, with no label of what it does. | Keep, low priority (hide if Sammy never uses it). | One display preference. |
| 12 | Clips > per-page select (50) and pager | Rows per page; Previous / Next. | Anyone. | Fine. | Keep. | |
| 13 | Clips filter drawer: about 20 filters (Issue, Bills, Reach, How Gabriel appears, Mention depth, Direct quote, Medium, Format, Channel, Show, His role on air, Outlet, Reporter, County, State, Language, Tone, List-only mentions, Saved copy, Press release) | Narrows the list. | Heavy users. | Too many for most use; several overlap (Medium, Format, Channel, Show, His role on air are all about TV and radio; Reach and Outlet; County and State). | Keep the top six (Issue, Bills, Reach, Outlet, Reporter, Tone, Saved copy) open; fold the TV and radio group and the place group under one "More filters". | Nothing, they would be one click away. |
| 14 | Clips "Views" chips (Last 30 days, Headlines and op-eds, National and statewide, Negative tone, With a saved copy) and saved views | One-click filter sets; people can save their own (stored in the browser, personal). | Everyone / the keeper | Chips duplicate filters; saved views are per computer and are lost if the browser data is cleared; PC tracker starts without views (SWITCHOVER-v1). | Keep the five chips; hide "save a view" if it is not used. | Personal saved filters. |
| 15 | Tick boxes beside each clip (the "ticked" list), Export "listed or ticked stories" | Select several stories and export those. | Occasionally | The checkbox column is always shown; its purpose is not stated. | Keep; show boxes only after "Select" is pressed. | Nothing. |
| 16 | Export menu: "Copy clips list", "Copy for spreadsheet", "Download CSV" | Three ways to take the list out. | Occasionally | Three similar items with long grey explanations. | Keep CSV and "Copy for spreadsheet"; drop "Copy clips list" if unused. | One format. |
| 17 | Team note box in the story sheet vs tone note | "Team note: Anything the team should know" is shared notes; tone has its own line ("Tone: Positive. ... Rated by Claude from the saved copy" with a Change dropdown). | The keeper | On the PC notes stay on this computer (MULTIPC-v2), so "Notes are shared with everyone who opens the tracker" is wrong. Tone says "Rated by Claude" but the PC no longer rates; the Change dropdown edits the tone locally. | Fix the wording (notes are personal here); keep the notes; keep tone Change for the keeper only. | Nothing if reworded. |
| 18 | Data tab: 13 collapsible sections (Summary and The brief, Coverage by quarter, Compare two periods, Issues & bills, Biggest news moments, Outlets & reach, Reach and medium, Local coverage by county, Coverage outside California by state, Languages and Other languages, Share over time, Tone, Tone by issue quarter by quarter, More charts: Issues by year heat map and Busiest months) | Charts and tables, with "Chart options" and "Show the numbers" folds, Period select, "Copy brief". | Sammy for reports | A very long page; several charts say nearly the same thing; "Chart options" and "Show the numbers" repeat in each section; "More charts" hides two. | Keep "The brief" and "Coverage by quarter" open; leave other sections collapsed by default; consider removing "Share over time" and "Other languages" if unused. | Only if removed: those two charts. |
| 19 | Data tab > "Compare two periods" | A comparison of two date ranges. | Rarely | A tool that needs choices before it shows anything. | Keep collapsed. | Nothing. |
| 20 | Insights / "Press desk" tab | A ninth tab (`#tab-in`) is built but hidden (`data-tb-hidden`, display none). | Nobody | Dead code only; not seen by Sammy. | Leave; remove later. | Nothing visible. |
| 21 | Story travel tab | Shows how a story spread: first outlet, days to the last pickup, a map and a ladder. | Sammy | The name does not say what it is; has its own map and curve rules. | Keep; add one sentence under the title. | Nothing. |
| 22 | The "i" tips and "About this list" fold on each tab | Short explanations on every list tab and many headings. | New users | 40 or more small "i" icons; the "About this list" link is a separate line above every table. | Keep the About link; remove the "i" from headings whose meaning is obvious (for example Related stories). | Some hover text. |
| 23 | Release page: "Ran the release", "Related stories", "Later coverage", "Other releases on this bill", "Possibly related" | Five stacked blocks. | Sammy | Possibly related and Later coverage are small side lists under a long main list. | Keep; after problem 1 is fixed they at least look consistent. | |
| 24 | Update-era wording still in the page | "ask Claude in chat", "Press Update database", "Refresh from files", "Rated by Claude", "Mac (Desktop/Tracker library)" appear in Manage, Data checks, the story sheet and tooltips. | Everyone | Tells the user to press buttons that are not there. | One text pass over the PC page's strings (the station adds the replacement text). Needs a list of exact strings first. | Nothing. |
| 25 | Home: "Needs attention" list | Lists three negative stories, then one very positive, each with a link. | Sammy | Fine, the list is the useful part of Home. | Keep. | |
| 26 | Home: "Tone, last 90 days" card | A bar with two captions and a link "See rated clips"; mostly empty card. | Sammy | Large, nearly empty box. | Keep but make it only as tall as its content. | Nothing. |

Most worthwhile, in order: (1) hide or replace Manage > Find & refresh and fix the Update-era wording (items 1, 4, 24), (2) move Tracker files into the masthead and tidy its six steps (items 8, 9, 10), (3) Clips filter drawer grouping (13), (4) the Manage badge number (6).

---

## H. Order I would fix them in (when Sammy approves)

1. Rebuild the PC app from current source (clears problem 1).
2. Problems 5, 12 (two small CSS lines, very low risk).
3. Problem 6 and 10 (button heights and text centring; one pass, update the look check).
4. Tracker files into the masthead (section E; also clears 9 and 14).
5. Problem 4 (Top issues cells) and problem 3 (Outlets at 960; the riskiest).
6. Problem 2 last: after Sammy points at which line he means, since it touches the corner code that has been rewritten many times.
