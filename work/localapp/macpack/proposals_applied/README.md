# Mac changes to shared code: APPLIED 2026-11-04 (patches kept for the record; tests now at work/localapp/app/tests/test_mac_fixes.py)
Original text follows.

None are needed for the Mac build to work (assemble_mac.py wraps assemble_app.py without editing it). Four patch files, apply in this order from the repository root with `git apply work/localapp/macpack/proposals/<file>`; `python3 -I work/localapp/macpack/proposals/test_mac_proposals.py` applies them to a temporary copy and checks each (9 checks, all pass on Linux).

| File | What and why |
|---|---|
| `mac_a_nfc.patch` | File names are brought to one spelling for accents (NFC) where the app compares or passes on library names: refresh file making (`refresh._tree`), refresh file taking (`refresh.check_name`), and the renaming scan (`rename_files.library_index`). Why: a Mac can hand back accents as base letter plus mark (NFD); the workbook and Windows use the single-character form, so a name would not match. Already fine, no change: `setup_mac` (normalizes list and folder), the for-Update file and the page build (they work from the workbook's names, not the folder listing), and `/library/` serving (names are fixed patterns, no accents). |
| `mac_b_dotfiles.patch` (after a) | Skip `.DS_Store` and `._` files: in the renaming scan, and ignore `__MACOSX/` and `.DS_Store` entries in a refresh zip that was re-zipped in Finder. Why: Finder adds them; refresh making and `setup_mac` already skip them. |
| `mac_c_folder_hint.patch` | When what is dropped on the update or refresh box has no file extension (a folder), the message adds: Safari may have unzipped it, use the .zip, and how to turn that off. |
| `mac_d_neutral_wording.patch` | "black window" becomes "Terminal or command window" (panel.js, launcher.py); "Edge was not found, so ..." becomes "The page opened in your usual browser." Why: on a Mac there is no black window or Edge. No test checks this wording (only two code comments mention it). |
