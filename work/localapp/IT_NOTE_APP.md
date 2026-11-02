# Note for IT: "AJG Tracker" (the office press-clippings tracker)

**What it is:** a folder that shows Assemblymember Jesse Gabriel's press-coverage database (an Excel workbook of public news clippings, plus a library of saved public news articles) as a page in Edge. It is the full version of the "AJG Tracker test" IT already approved, and works the same way.

**What is in the folder:**
- `python\`: CPython 3.13.16 for Windows, the official Python Software Foundation build from its NuGet package "python". The `python.exe` and its DLLs carry the PSF Authenticode signature.
- `app\site-packages\`: 10 packages from the official Python package index (PyPI), each checked against a pinned sha256:
  - openpyxl, et_xmlfile, beautifulsoup4, soupsieve, typing_extensions, pypdf, python-dateutil, tzdata, pandas, numpy;
  - pandas and numpy contain compiled code (.pyd/.dll files built by those projects; not Authenticode-signed);
  - everything else is plain Python text.
- `app\`: the tracker's own programs, as readable Python and JavaScript text.
- `data\site\fonts\`: the page's two typefaces, bundled so the page never contacts a font service: Roboto Slab (Apache 2.0) and Public Sans (SIL Open Font License 1.1), with their licence files.
- `data\`: the workbook, the article library, backups and the tracker's notes, all as ordinary files.
- `Start Tracker.cmd`: a short batch file that starts `python\python.exe` on `app\station\launcher.py`.

**What it does:**
- Listens on 127.0.0.1 port 8765 (this computer only) and opens the tracker page in Edge.
- Reads and writes only inside its own folder, plus files the user picks: an update file or a refresh file, both plain data (JSON and saved article pages; it refuses any file that contains programs).
- Writes the workbook only after backing it up and checking it, one person at a time.

**Network:**
- The program itself makes **no** internet or network connections.
- **One exception, by design:** saved articles added from now on show their photos by linking to the news site's own image address. When someone opens such an article in the tracker, Edge loads those pictures from the news site, the same as ordinary web browsing. No other data leaves the computer, and the request carries no referrer. Older saved articles have their photos built in and load nothing.

**What it does not do:**
- Install anything, or need admin rights.
- Touch the registry.
- Create services, scheduled tasks or startup entries.
- Use PowerShell.
- Send any data anywhere.

**To remove it:** close its window and delete the folder.

**Source:** full source, build scripts and checksums are available on request.
