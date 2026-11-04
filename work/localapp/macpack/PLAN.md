# Mac version of the tracker (MACAPP-v1): plan for Sammy

**Recommendation: ship Python from python-build-standalone ("PBS"), both chips in one folder.** The tracker page, server, save rules, update folder and refresh files are the same code as Windows, so a Mac copy and a Windows copy swap files freely.

## The choice, in plain words
A Mac needs a Python that comes inside our folder (nothing installed, no password).
| Option | Verdict |
|---|---|
| **PBS** (public project, GitHub release 20261026, Python 3.13.18) | **Chosen.** Built to be moved anywhere. One file, `python3.13`, that uses only Apple's own system libraries (checked). Its fingerprint is pinned in our script, so a wrong or tampered download is refused. Downside: it is not signed by the Python Software Foundation the way the Windows one is. |
| python.org installer | Signed and approved by Apple, but it is an installer (asks for a password) and its Python is tied to its install folder. Could not be fetched from this build machine. Fallback only. |
| Apple's own or Homebrew Python | Needs an install. No. |
| A frozen single app (PyInstaller) | Has to be built on a Mac; harder for IT to read. No. |

**Intel or Apple chip?** PBS has one build per chip, so the folder holds both (~30 MB each) and the start file picks the right one. No question asked of Sammy. The zip is about 77 MB.

## The 10 packages
8 are the identical pure-Python files used on Windows (same fingerprints). `numpy` and `pandas` have official macOS builds on PyPI at the same versions; we pin the oldest ones (macOS 11 Apple chip, macOS 10.13 Intel), each with its fingerprint.

## What differs from Windows
- Start file: `Start Tracker.command` replaces `Start Tracker.cmd`; the browser is the default one (Safari or Chrome), not Edge.
- No patches needed: the pure-Python swaps (pdftext, no-network, photo links, fonts) are the same. The Excel-open check already looks for Excel's `~$` file, which Mac Excel also makes.
- Paths: the code already uses forward-slash-safe paths. File names with accents (Spanish, Korean outlets): Macs store them in a different form than Windows; test item.

## Security prompt ("Apple cannot check this file")
A downloaded zip is marked "from the internet". Easiest, no password: unzip in Terminal with `unzip` (it does not copy the mark), then `bash "AJG Tracker/Start Tracker.command"`. Double-click later works. Otherwise: right-click the file, Open, Open (newest macOS: System Settings, Privacy and Security, Open Anyway, which may ask for a password). The start file also removes the mark from its own folder.

## What cannot be proven here
Everything that runs a Mac program (see TEST_ON_MAC.md). ETA to a testable zip: it is built and sitting ready; I can rebuild with the final code in about 10 minutes of build time once the Windows round freezes.
