# Testing the Mac folder (use a COPY of the workbook and library, never the real ones)
1. Unzip in Terminal: `cd ~/Desktop` then `unzip ~/Downloads/"AJG Tracker Mac.zip"` then `bash "AJG Tracker/Start Tracker.command" --selfcheck`. Expect only lines starting `ok`, no `FAIL`. Send me anything else.
2. Start for real: `bash "AJG Tracker/Start Tracker.command"`. The browser should open http://127.0.0.1:8765/ and show the tracker (or "No workbook yet" on an empty build).
3. Double-click `Start Tracker.command` in Finder. Note exactly what macOS says (and whether right-click, Open fixes it). Try once on an Intel Mac too if you have one.
4. Set `data/role.json` to `{"role": "keeper"}`, then Tracker files > Set up from the Mac library, pointing at a COPY of the library folder. Check files, copy and set up.
5. Compare the page with the Windows tracker: fonts, colours, a story's "View original" (PDF opens in the browser), a saved copy with a photo.
6. Make a "for Update" file; bring in an update zip from the station; preview only, then (on the copy) Save. Confirm the Excel-open refusal by opening the copy workbook in Excel and trying to save.
7. Make a refresh file; bring it into a Windows copy (and the reverse). Names with accents must arrive unchanged.
8. Close the Terminal window: the tracker should stop; starting again should work.
