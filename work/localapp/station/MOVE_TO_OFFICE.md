# Moving the Update station to the office claude.ai account

For Sammy. About ten minutes, once. Nothing here touches the old tracker.

## 1. The file

Use `work/localapp/station/dist/index.html` (about 3.7 MB). Make it fresh first with
`python3 -I work/localapp/station/build_station.py`. Check that it is the file you think it is:

    sha256  728e20a33f9f7b6c2b7e74be59e8b0f0b1597c79698a68f5fccfc64441e76331

(On the Mac: `shasum -a 256 index.html`. On Windows: `certutil -hashfile index.html SHA256`.)

It holds no stories, no links to other artifacts and no account details. Everything it needs comes from the "for Update" file you load each time.

## 2. Connect TinyFish on the office account (once)

Sign in to claude.ai with the office account. Settings, then Connectors, then add TinyFish. The connector's name must be exactly `TinyFish` (capital T, capital F, no extra words). The station asks for that name and will not find it under another one.

## 3. Publish it

Open a new chat on the office account, attach `index.html`, and paste this sentence:

> Publish the attached HTML file exactly as it is, without changing a character, as a private artifact titled "AJG Update Station" with the icon "search". Give it these capabilities and nothing else: db, downloads, sample (declared as {images: true}, so the page may send pictures to Claude), and mcp for the connector named "TinyFish" with the tools "search" and "fetch_content". Do not share it with anyone.

Claude gives you a link. Keep it private: a page that uses a connector cannot be shared "anyone with the link" anyway.
If the chat will not take a 3.7 MB attachment, do the same from Claude Code with the file in the folder and the same sentence.

## 4. First use

Open the link. Load a "for Update" file (step 1). Press Update database. The first time, claude.ai asks you to allow the page to use TinyFish and to use Claude: say yes to both. If you said no by mistake, use the page's Permissions menu and reload.

## 5. Interns

Interns open the same link from the same office account. They do not need their own copy. Each person loads the current "for Update" file, adds stories (Update, NewsBank PDFs, ProQuest PDFs), downloads the update folder in step 3 and hands it to the keeper. The page keeps nothing between uses, so it does not matter who used it last.

## If something is wrong

- "TinyFish is not connected": do step 2, reload.
- "Claude is not available on this page": allow it in the Permissions menu, reload.
- The page looks right but Update finds nothing: check the date in the Since box, and that the "for Update" file is recent (the page warns after 7 days).
