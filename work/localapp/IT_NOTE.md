# Note for IT: "AJG Tracker test" (a compatibility check)

**What it is:** a small folder that checks whether a planned office tool can run on this PC. The tool would be a press-clippings tracker for Assemblymember Jesse Gabriel's office. This test does nothing else.

**What is in the zip** ("AJG Tracker test.zip", sha256 `53952af347705d20ed855da4d8fa77b41c67a632f428d764412db28ddaafd98e`):
- `python\`: CPython 3.13.16 for Windows, the official build by the Python Software Foundation, taken from its NuGet package "python". `python.exe` and its DLLs carry the PSF Authenticode signature.
- `app\probe.py`: the test script, plain readable text (about 200 lines).
- `app\site-packages\`: openpyxl 3.1.5 and et_xmlfile 2.0.0, unpacked from their official PyPI wheels.
- `Start test.cmd`: a 10-line batch file that runs `python\python.exe -I -s app\probe.py`.

**What it does:**
- It writes and removes one small file in its own folder.
- It creates one small Excel file in its own `_test_output` folder.
- It listens on 127.0.0.1 (this computer only) on a random port, and opens one local page in Edge showing the results.
- It stops when its window is closed, or after 15 minutes.

**What it does not do:**
- Install anything, or need admin rights.
- Touch the registry.
- Create services, scheduled tasks or startup entries.
- Make any internet or network connection.
- Read files outside its own folder.
- Send data anywhere.

**To remove it:** delete the folder.

**The planned tool**, if this test passes and IT approves, would work the same way:
- the same signed Python, in one folder;
- a local page on 127.0.0.1 only;
- no installs and no network connections.

It keeps the office's press-coverage workbook (public news clippings) and a library of saved public news articles. New clippings arrive as a file the user brings in by hand.

**Source:** the full source and build scripts are available on request.
