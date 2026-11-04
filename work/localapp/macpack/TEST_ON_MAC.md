# Testing the Mac folder (use a COPY of the workbook and library, never the real ones)
1. Unzip in Terminal: `cd ~/Desktop` then `unzip ~/Downloads/"AJG Tracker Mac.zip"` then `bash "AJG Tracker/Start Tracker.command" --selfcheck`. Expect only lines starting `ok`, no `FAIL`. Send me anything else.
2. Start for real: `bash "AJG Tracker/Start Tracker.command"`. The browser should open http://127.0.0.1:8765/ and show the tracker (or "No workbook yet" on an empty build).
3. Double-click `Start Tracker.command` in Finder. Note exactly what macOS says (and whether right-click, Open fixes it). Try once on an Intel Mac too if you have one.
4. Set `data/role.json` to `{"role": "keeper"}`, then Tracker files > Set up from the Mac library, pointing at a COPY of the library folder. Check files, copy and set up.
5. Compare the page with the Windows tracker: fonts, colours, a story's "View original" (PDF opens in the browser), a saved copy with a photo.
6. Make a "for Update" file; bring in an update zip from the station; preview only, then (on the copy) Save. Confirm the Excel-open refusal by opening the copy workbook in Excel and trying to save.
7. Make a refresh file; bring it into a Windows copy (and the reverse). Names with accents must arrive unchanged.
8. Close the Terminal window: the tracker should stop; starting again should work.


---

# Part 2: the data test (with the test kit)
You need: `AJG Tracker Mac.zip` (already unzipped, part 1) and `AJG_Mac_test_kit.zip` (about 50 MB, a small made-up copy of the library: about 40 stories, 439 files, plus the real workbook copy). Nothing here touches your real workbook or library.

**1. Unzip the kit.** Open Terminal and type, one line at a time, pressing Return after each:

```
cd ~/Desktop
unzip ~/Downloads/AJG_Mac_test_kit.zip
```

A folder called `AJG test library` appears on the Desktop (a different name from your real `Tracker library`, which is never touched). Inside it is a file called `Tracker library manifest.sha256` (the fingerprint list).

**2. Make this copy the keeper copy.** (A keeper copy is the one that saves. The folder you unzipped is a reader copy until you do this.)
1. In Finder, open the `AJG Tracker` folder, then `data`.
2. Right-click `role.json`, choose Open With, then TextEdit.
3. If TextEdit shows fancy text, choose Format > Make Plain Text first.
4. Make the file say exactly this, and nothing else:
   ```
   {"role": "keeper"}
   ```
5. Save (Command-S) and close TextEdit. Check the file is still called `role.json` (not `role.json.txt`).

**3. Start the tracker** (if it is not running):

```
cd ~/Desktop
bash "AJG Tracker/Start Tracker.command"
```

Safari opens the tracker. It should say "No workbook yet".

**4. Set up from the Mac library.**
1. Click **Tracker files** (top right).
2. Open **Set up from the Mac library**.
3. In the first box type the path of the kit folder. Quick way: in Finder, hold Option, right-click the `AJG test library` folder, choose "Copy "AJG test library" as Pathname", then paste into the box (Command-V). It looks like `/Users/you/Desktop/AJG test library`.
4. Leave the second box empty. Press **Check files**.
5. Expect: "Everything checks out. Ready to copy." and "440 of them are here with the right fingerprint."
6. Press **Copy and set up**. It takes about a minute. Do not close Terminal.
7. Expect: "The tracker is set up", about 4,100 stories. The page reloads with the tracker.
8. Write down anything else it says. (A line saying some stories have a saved copy "that the tracker's article data does not hold yet" is normal for this small kit.)

**5. Look around.** Compare with the Windows tracker if you can: fonts, colours, the lists, a story's details. The kit holds the real workbook, so all the stories are there, but saved copies exist only for about 40 of them. Stories from 2026 with a "Saved copy" are the ones to open.

**6. View original.** Find a print story from 2026 (a newspaper page, look for "View original" in its details; the kit holds 6 of these, article numbers 05443, 05445, 05452, 05453, 05454, 05456). Click **View original**. The page scan should open as a PDF in Safari. Tell me if it opens, downloads or says "not found".

**7. Make a "for Update" file.** Tracker files > **Make "for Update" file**. Expect: "Made for_update_...json (8 MB, about 3,700 stories)". It lands in Downloads and in `AJG Tracker/data/for_update`.

**8. Make a refresh file.** Tracker files > **Make refresh file**. (The first one is always a full one.) Expect a zip called `refresh_full_...zip` in Downloads, about 150 MB (it carries the page data and photos too). Safari may unzip it by itself: if you see a folder instead of a .zip, turn off Safari > Settings > General > Open safe files after downloading, and download again.

**9. Send me:** what step 4 said (a photo of the panel is fine), whether step 6 opened, the names of the two files from steps 7 and 8, and anything that looked different from the Windows tracker.

**Optional, if I send an update zip:** Tracker files > **Bring in update**, drop the zip, read the preview, and stop there (do not press Save unless I say so).

**Close:** close the Terminal window. The tracker stops.

*Accented file names:* the real library has none, so the kit has none. Names with accents are covered by a Linux test of the proposals in `proposals/`.
