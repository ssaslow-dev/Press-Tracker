# AVSHOW-v1 code spec: Channel vs Show (Sammy comments 69e1f457 + b8050b09)

Sheet state (master b395595a…, 2026-10-28): the "Audio & video details" tab has a new column **Channel** (col E, between "Item type" and "Show/program"). Channel = the channel/station/network/publisher that carried the item; Show/program = real program names only. 890 of 896 rows have a Channel; the 6 blanks are independent podcasts with no channel stated (09502, 09722, 09724, 09731, 09733, 09734). Change list: work/out/av_channel_show_changes.csv.

For the v20 code pass. agent-avshow did not edit code.

## 1. code/avtab.py (+ pipeline copy)
- `COLS`: insert `'Channel'` after `'Item type'`. `KEYS`: insert `'channel'` after `'type'` (same order as COLS minus Article ID). `WIDTHS['Channel'] = 22`.
- `write_tab`: no other change. It writes by header and the filter ref uses len(COLS). Note: until COLS gains Channel, the filter set by `write_tab` stops one column short. Fix it in the same change.
- New `channel_of(outlet, medium, network, url, html, text)`. Use it in `extract()` for **every** item type, including Web story. Rules, first match wins:
  1. NewsBank program record `"Show [NET]"`: the bracket (`CNN`, `NPR`, `Fox News`, `Fox Business`).
  2. Outlet names a program, not a channel. Take the network from the sheet's Network or the URL domain: `TODAY`/today.com → NBC, goodmorningamerica.com → ABC, `As It Happens` → CBC Radio, `Noticias Telemundo`/telemundo.com → Telemundo, `CBS Evening News` → CBS. Keep this as a small table in avtab.py.
  3. A known show/channel split in the outlet: `"KQED Political Breakdown"` → KQED, `"Greater LA (KCRW)"` → KCRW, `"LAist - 89.3 FM AirTalk: Audio"` → LAist. Generic patterns: `"<Show> (<CALL>)"` → CALL, and an `"<CALL> <Show>"` prefix when CALL matches `_CALL`.
  4. Podcast page evidence: Omny `"Author"`/station link (e.g. KFI AM 640, 790 KABC, KTRH), the Apple Podcasts lookup `artistName` **only when it names a station** (`/\b[KW][A-Z]{2,3}\b/`, e.g. "News 93.1 KFBK"), YouTube channel name (`ownerChannelName` / the channel header), og:site_name for publisher-hosted podcasts (Jewish Insider).
  5. Otherwise the Coverage Outlet, when it is not the show itself and not a bare domain.
  6. Else blank. Never use a host platform (podbean, Apple, Spotify, SoundCloud) as the channel.
- `show_of()`: never return a channel. Remove the Podcast fallback that returns the Outlet when the Outlet is a station/publication or a domain. Strip a channel prefix/suffix that `channel_of` found (`"KQED Political Breakdown"` → `Political Breakdown`, `"Greater LA (KCRW)"` → `Greater LA`). Read the show from page evidence:
  - podbean/Omny `<title>` `"<episode> | <show>"` or `"<episode> - <show>"`
  - Omny `"Name"` of the program
  - KQED show label
  - a series label (mitú "Series … <name>")
  - "About the <X> Podcast"
  - tvmaze `/episodes/<id>/<show-slug>-<SxE>`
- Station video pages (KTLA/FOX40/NBC/FOX 11/CBS): take the show **only** from the main clip's own description (`"This segment aired on the <Show> on <date>"`), never from the sidebar or related videos (same rule as DECISIONS 188 for dates). Otherwise blank.

## 2. build_data.py
- Nothing changes beyond KEYS: `rec.av.channel` and `reps[i].av.channel` flow through `avtab.block()` / the existing av join. The `av.json` cols gain `channel`.

## 3. Tracker (code/tracker/53_tabs.js `tbAvBox`)
- Replace `row('Show', esc(j(a.show, a.station, a.network)))` with two rows:
  - `row('Channel', esc(j(a.channel || a.station, a.channel && a.network && !a.channel.includes(a.network) ? a.network : '')))`. Fall back to station/network for old data with no `channel`.
  - `row('Show', esc(a.show || ''))`, **omitted when blank**.
- Channel is shown in **every** AV panel type: Broadcast segment, Video clip, Episode, and the untyped rows. The CNN case from comment b8050b09 (`00198`, `00742`, `05177`: Show = the program, Channel = CNN) must show both rows.
- Keep the `a.type === 'Web story'` early return as is. Web stories carry Channel in the data for facets only.

## 4. Facets and filters
- Clips: add facets **Channel** (`av.channel`, fallback `av.station`) and **Show** (`av.show`) for stories with `av`. They join the FACETS keys so `ctx.facetLink('channel'|'show', v)` works. The blank label is "Not recorded", sorted last (BLANK FACET VALUES rule).
- Outlets tab / any AV facet or search text that used the old joined "Show" string: use both fields. Search text includes channel and show.
- CSV export: separate "Channel" and "Show" columns.

## 5. Update button / sheet task (sheet_task.py `Task.apply_av`)
- Every new AV-medium row (Podcast/Radio/TV/Video, all item types) gets **Channel** from `avtab.channel_of` (outlet/URL first, then saved-page evidence) and **Show/program** from `show_of` (evidence only). Blanks only, as now. A run doc may carry `av: {placeholder: {"Channel": …, "Show/program": …}}`.
- Result key `av_rows[]` gains `channel` and `show`. Add `av_no_channel[] {aid, why}` for rows left blank, so the run's review lists them.
- `sheet_task_prompt.md`: the AV verify step fails when a new Broadcast segment / Video clip / Episode row has a blank Channel and the outlet or URL names a station or network.

## 6. Tests
- avtab unit cases:
  - `"Story Is with Elex Michaelson, The [CNN]"` → channel CNN, show "The Story Is with Elex Michaelson"
  - `"KQED Political Breakdown"` → KQED / Political Breakdown
  - `"790 KABC"` with an Omny John Phillips page → 790 KABC / The John Phillips Show
  - KTLA clip whose sidebar says "aired on the KTLA 5 Morning News" → show blank
  - podbean `"… | Pro Bono Happy Hour"` → show Pro Bono Happy Hour
- Rebuild check: the `av` block equals the sheet tab, so channel is filled on 890 rows.
