# AJG Tracker on a Windows PC: the plan

Written 2026-10-30 for Sammy. Technical appendix for the builders: BUILD_NOTES.md (same folder).

## Recommendation

Build one small Python program that lives in a folder on the PC, shows the existing tracker page in Edge, saves runs to the workbook, and doubles as the Claude connector. Drop the first draft's packaged desktop shell (Tauri), bundled database and Windows build farm: a portable zip assembled on Linux does the same job with fewer things IT can block.

## What changes for you day to day

- You open "AJG Tracker" from a shortcut. The tracker (same tabs, charts, filters) opens as its own Edge window. It reads the workbook and library on the PC; nothing is uploaded.
- "Save the last run" stays a sentence in Claude Desktop, but Claude talks to the program on your PC instead of a cloud link to your Mac. You get a preview (which rows and cells would be filled), say "save", and the program backs up, writes, verifies the checksum and rebuilds the page.
- Until the app has its own Update button you keep pressing Update in the web tracker; Claude pulls that run and hands it to the PC program. The 10 MB web page is no longer republished after each save; the local page is the live one.
- Nothing scheduled, nothing paid, same rules.

## Architecture

One folder, `AJG Tracker\`, three parts:

1. **Core** (Python): the existing pipeline (`sheet_task.py`, the builders, about 50 modules) plus a thin "saver" that turns the chat steps in `sheet_task_prompt.md` into code: lock, back up, write, verify, rebuild. Runs are JSON files in `runs\`, the shape `sheet_task.py` already reads.
2. **Local web app**: a tiny server on `127.0.0.1` serving the built page and saved copies from `site\`, opened in Edge "app mode" (a window without an address bar). Edge is on every Windows PC.
3. **Connector**: the same program started by Claude Desktop as a local MCP server (MCP is the plug-in protocol Claude Desktop uses to call local tools), packed as a `.mcpb` file (double-click install), with a one-line config-file fallback if `.mcpb` is blocked. Your normal Claude plan; no API key.

Python ships inside the folder as python.org's "embeddable" distribution (a zip made for exactly this) with the needed packages vendored beside it. No installer, no admin rights, no registry.

### Why this, and where I disagree with the first draft

- **Tauri: no.** It needs a Rust toolchain, a Windows machine for the `.msi`, an installer for IT to approve, and still carries Python. WebView2 is not the obstacle (it ships with Windows 10 since 2018 and Windows 11); the extra parts are. Edge app mode gives most of the native feel; a Tauri wrapper can be added in a day if you ever want a tray icon.
- **Bundled Python: yes, but the embeddable zip, not a PyInstaller exe.** Home-made exes trip antivirus and SmartScreen; `python.exe` is signed by the Python Software Foundation. Every package we need (openpyxl, pandas, bs4, langdetect, mcp) has a Windows wheel fetchable from Linux.
- **SQLite: no.** A few hundred JSON runs that `sheet_task.py` already consumes; readable in Notepad, diffable, backed up with the library. A database adds a schema for nothing.
- **GitHub Actions: not needed.** Nothing is compiled, so the bundle is a zip the agents assemble in their Linux workspace. Actions would matter only to sign a native exe later (private repos get $12 of credit a month, about 1,200 Windows minutes, so even that is free).
- **Connector alone?** Nearly: the app is about 300 lines of server on top of the connector's core. The page is what you and colleagues look at, so it stays, cheaply.
- **Six tools: reshaped.** `propose_rows` goes: Claude must not compose workbook rows freehand; rows come out of `sheet_task.py` so "fill blanks only" is enforced by code. Added: `import_run` (how web-tracker runs reach the PC), `preview_save` (diff before writing), `lookup_reference` and `record_lookup` (reference data before the web, as tools). Contracts in BUILD_NOTES.md.
- **Portable no-install build is the only build.** Unzip, double-click.
- **Excel locking on Windows helps.** Excel holds the file open, so a write to the master fails loudly if it is open, on top of today's `~$` lock-file check.
- **Where the workbook lives matters more than the shell.** Master and library on the local disk, outside OneDrive; only the add-only `Backups\` folder inside OneDrive (write-once files sync without conflicts). A master inside OneDrive risks conflict copies, "files on demand" placeholders and AutoSave fighting our writes.

## Phases

| # | What | Model | Agent hours | Done when | Sammy / IT must |
|---|---|---|---|---|---|
| 0 | Freeze save rules and tool contracts (BUILD_NOTES); pick the inbox format | Fable | 1 | Contracts signed off by you | Answer the decisions below |
| 1 | Core: `saver.py`, `store.py`, `site.py`, config; tests on Linux against a copy of the workbook | Sonnet | 4 | Suite green; a fixture run saves into a workbook copy with the expected diff | Nothing |
| 2 | Local web app, launcher, Windows bundle script (embeddable Python, wheels, zip, checksums) | Sonnet 2, Haiku 1 | 3 | Zip opens the tracker in Edge on a clean PC | Unzip and run on the office PC, report (20 min a round, expect 3 to 4) |
| 3 | Connector: MCP server with the BUILD_NOTES tools, `.mcpb` pack, config fallback; Fable reviews save safety | Sonnet 3, Haiku 0.5, Fable 1 | 4.5 | Claude Desktop lists the tools; `preview_save` then `save_run` works on a test copy on the PC | Install Claude Desktop and the `.mcpb`; IT: confirm extensions allowed |
| 4 | Move: copy library and master from the Mac, verify every sha, first supervised live save, retire the Mac link | Haiku 1, Fable 0.5 | 1.5 | PC master sha = DECISIONS sha; first run saved and verified | Copy `Tracker library` once (drive or OneDrive); close Excel |
| Later | Update button (below) | Sonnet 5, Fable 1 | 6 | A run found on the PC saves end to end | Type the TinyFish key into settings |

About 14 agent hours to phase 4 (first draft: 9 to 14; the extra is tests and the bundle script) plus 6 for the button. Calendar: 2 to 3 weeks, set by PC test rounds and IT, not agent time.

Human bottlenecks: (1) only you can run the zip on the office PC, so phases 2 and 3 wait on you each round; (2) IT: is Claude Desktop installable (it is a per-user MSIX, but installs without admin can fail), are desktop extensions allowed, may an unzipped `python.exe` run from a user folder (AppLocker sometimes says no); (3) the one-time library copy from the Mac; (4) the workbook-location decision. Agents cannot test on Windows.

## The later Update button

Port the page's search plan (`40–43_update_*.js`) to Python in the app and keep TinyFish. New fact: since May 2026 TinyFish Search and Fetch are free with a key (30 searches/min, 150 fetches/min); only browser automation is metered. So "your key in settings" is free and within the free-sources rule. The key goes into Windows Credential Manager (via the `keyring` package), never into a file or to Claude.

1. **Your key in app settings** (recommended): the app searches and fetches itself.
2. TinyFish through Claude for blocked sites only: two code paths for little gain. No.
3. Everything through Claude: the button becomes a chat sentence tied to a window. Possible, slower.

Without an API key the app cannot classify finds with Claude (the web page uses the artifact's `sample` capability for that). So the button is two steps: press Update (search, fetch, free pre-filters, queue), then say "review the latest run" in Claude Desktop; Claude reads the finds through the connector, decides, and `save_run` writes. Same review as now, one step earlier.

## Costs

All free: Python, packages, Edge, Claude Desktop on your plan, TinyFish search/fetch, GitHub. Optional signing, only if a native exe or installer is ever added:

- Azure Artifact Signing (was Trusted Signing): $9.99/month Basic (5,000 signatures), $99.99 Premium; billing starts at account creation; open to US and Canadian individuals after identity checks.
- OV certificate: SSL.com $129/yr, GlobalSign $434/yr, DigiCert $696 to $840/yr, plus a hardware token (mandatory since June 2023; SSL.com's YubiKey $379, Sectigo ships one free).
- EV no longer buys instant SmartScreen reputation (removed in 2024); not worth the premium.

The recommended build has nothing to sign.

## Risks and handling

| Risk | Handling |
|---|---|
| IT blocks `python.exe` from a user folder | Plan B: IT installs Python (python.org or Microsoft Store); the code runs on any 3.11+ with `pip install -r requirements.txt`. Ask IT before phase 2 |
| Desktop extensions disabled | One entry in `claude_desktop_config.json` (per-user). If Claude Desktop itself is banned, the app still works; saving falls back to a file hand-off |
| Workbook in OneDrive gets conflict copies | Master local, only `Backups\` in OneDrive; the saver refuses to write if the master's sha is not the last recorded one |
| Two writers | Lock file, `~$` check, Excel's own lock, sha before and after. Any failure: no write, run stays queued |
| Web-tracker runs become unreadable after an account change | `import_run` also takes a downloaded run file; add an "Export run" download to the web page (small patch) |
| Web tracker no longer knows what was saved locally | Expected; `sheet_task.py` drops duplicates against the current workbook. Decision 4 covers refreshes |
| Successor cannot run it | One folder, one README, JSON runs, the existing suites, `.mcpb` double-click; no cloud pieces except Claude Desktop |
| Library copy incomplete | Phase 4 compares sha256 manifests on both sides before the Mac is retired |

## What stays the same

The workbook as source of truth and its column rules; the add-only library; `sheet_task.py` and every rule module, untouched; the test suites; the tracker page; backup-then-write with checksum; one writer; fill blanks only; reference data and lookup cache before any web lookup; no schedules, paywall workarounds, logins, YouTube or advocacy blogs; free sources only; the web Update button until the app has its own.

## Decisions for you

1. **Shell:** Edge app mode now, Tauri wrapper only if wanted later. Recommend yes.
2. **Workbook location:** master and library local, `Backups\` in OneDrive. Recommend yes; if IT forces everything into OneDrive, say so and we add a conflict check.
3. **Interim hand-off of web runs:** Claude reads the artifact database and calls `import_run`; downloaded file as fallback. Recommend yes.
4. **Web tracker after the move:** freeze it (Update only, no page republishes); refresh the shared read-only viewer monthly from the app's export until the button moves, then retire both. Recommend yes.
5. **Python:** embeddable bundle. Recommend yes; still ask IT question (1).
6. **Code signing:** none. Recommend yes.
7. **TinyFish for the button:** your key in settings, in Credential Manager. Recommend yes.
8. **Button review:** two steps (Update, then "review the latest run"). Recommend yes; the alternative is an API key.
9. **Mac build:** same folder with a python.org Python and a `.command` launcher, after phase 4. Recommend later, if at all.
10. **Order:** 0 to 4, then the button. Recommend yes; the button is where most of the spend is and the part you can live without longest.

## Sources

- MCPB bundles, install paths, platforms: https://claude.com/docs/connectors/building/mcpb
- Local MCP on Claude Desktop; Node bundled; secrets in Credential Manager; admin controls: https://support.claude.com/en/articles/10949351
- MCPB manifest (python, uv, binary types; `sensitive` config): https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md
- Claude Desktop Windows deployment (MSIX, per-user, admin notes): https://support.claude.com/en/articles/12622703
- Tauri v2 Windows installer and WebView2 options: https://v2.tauri.app/distribute/windows-installer/
- Python embeddable package: https://docs.python.org/3/using/windows.html
- Azure Artifact Signing prices and eligibility: https://azure.microsoft.com/en-us/pricing/details/trusted-signing/ ; https://devclass.com/2026/01/14/code-signing-windows-apps-may-be-easier-and-more-secure-with-new-azure-artifact-service/
- OV/EV certificate prices and token rule: https://codenote.net/en/posts/ov-ev-code-signing-certificate-pricing-japan-2026/
- SmartScreen behaviour, EV change, enterprise policy: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation ; https://www.todesktop.com/blog/posts/windows-apps-psa-ev-certs-do-not-grant-immediate-reputation-anymore
- GitHub Actions included credit and Windows rate: https://docs.github.com/en/billing/concepts/product-billing/github-actions
- TinyFish Search and Fetch free, limits, key: https://tinyfish.ai/blog/search-and-fetch-are-now-free-for-every-agent-everywhere
