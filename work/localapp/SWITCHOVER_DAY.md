# Switch-over to the PC tracker: your checklist

Tick each line as you go. Nothing here changes your Mac master or library; the PC works on its own copy.

## Before you start
- [ ] Old tracker: no more Update runs or saves from now on (A10).
- [ ] IT has the updated note and the final zip's fingerprint `e7655931…3219` (A3), or you have decided to go ahead.
- [ ] On the PC, a folder that is not synced to OneDrive, with 4 GB free (e.g. `C:\Users\<you>\AJG`).

## 1. Get the library onto the PC (in one piece)
- [ ] Mac, Terminal (only if the old tracker saved since the fingerprint list was made): remake the list.
      `cd ~/Desktop/"Tracker library"` then
      `find . -type f ! -name '.DS_Store' ! -path './Backups/*' -print0 | xargs -0 shasum -a 256 | sed 's|  \./|  |' > "Tracker library manifest.sha256"`
      (moved into the library folder so the zip below carries it; if you made it on the Desktop, move it into "Tracker library" first)
- [ ] Mac, Terminal: make one zip of exactly what the tracker needs (about 1 GB).
      `cd ~/Desktop/"Tracker library"` then
      `zip -r -q ~/Desktop/TrackerLibraryForPC.zip "AJG Coverage - NewsBank.xlsx" "Tracker library manifest.sha256" [0-9][0-9][0-9][0-9] _original_html _original_pdf "Press releases" -x "*.DS_Store"`
- [ ] Upload that ONE file to your cloud folder; on the PC download it fully.
- [ ] PC: remove or rename the old incomplete "Tracker library" folder; make a new `Tracker library` folder; right-click the zip > Extract All into it.
- [ ] Check: the workbook, the manifest file and the year folders sit directly inside "Tracker library".

## 2. Set up the tracker
- [ ] Unzip the FINAL zip (`AJG_Tracker_windows_final.zip`, fingerprint `e7655931…3219`) into your AJG folder.
- [ ] Notepad: `AJG Tracker\data\role.json` -> `{"role": "keeper"}`, save.
- [ ] Double-click `Start Tracker.cmd`.
- [ ] Tracker files > Set up from the Mac library > point at "Tracker library" > **Check files**: must say all 12,682 files are here. If not, send Claude what it says.
- [ ] **Copy and set up.** The page reloads with your tracker.
- [ ] Look around: Home, Clips, a few stories, a saved copy, View original on a print story.

## 3. Switch-over changes (one time only)
- [ ] Open the Switch-over changes screen; read every preview.
- [ ] Decide row 01920 (remove, or split into its own story) and row 03486 (author Marisa Kendall).
- [ ] Wait for Claude's OK (last tests), then apply. Note anything it reports.

## 4. First real update, with Claude (A8)
- [ ] Tracker files > Make "for Update" file.
- [ ] Update station (https://claude.ai/artifact/5uGsM8yQMphjAQbKhvc5SL): load the file, press Update, download the update folder (keep it a .zip).
- [ ] Tracker files > Bring in update > drop the zip > read the preview > Save.

## 5. Colleagues (A9)
- [ ] Tracker files > Make refresh file; send it to each colleague.
- [ ] Each colleague: unzip the final zip (leave role as reader), start it, drag in the refresh file.

## Later (no rush)
- [ ] Move the Update station to the office claude.ai account (A7; work/localapp/station/MOVE_TO_OFFICE.md).
- [ ] Mac: the two upload tests (B4b) and a refresh-file swap with the PC (B5).
- [ ] Delete test folders: the Mac's "AJG Tracker" test copy, "Tracker library 2", test zips in Downloads.
