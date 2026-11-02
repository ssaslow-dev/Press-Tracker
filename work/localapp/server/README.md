# PC tracker server (build step 4)

Serves the built tracker to the browser on this PC and stores what claude.ai's runtime stores online today (notes, saved views, edits, tones, authors, translations, and the Update-related collections). Python 3.11+, standard library only.

## Run

    python -I server.py --site <folder with index.html> --data <data folder> [--port 8765] [--verbose]

- Default port 8765. If it is taken the server stops and says so; it never picks another port, because the browser keeps its own settings (localStorage, IndexedDB) under the exact address.
- `--data` defaults to `data_local` beside the site folder.
- Tests: `cd work/localapp/server && python3 -I -m unittest discover -s tests -p "test_*.py"` (the browser test needs node + playwright; it skips if absent).

## What IT would see

One process listening on **127.0.0.1:8765 only** (never 0.0.0.0 or ::). No outbound network of any kind, no registry, no admin rights, no PowerShell, no telemetry, nothing hidden. It reads the site folder and reads/writes the data folder only.

Guards against other web pages or programs calling it:
- The Host header must be `127.0.0.1:<port>` or `localhost:<port>` (blocks DNS rebinding); a foreign `Origin` header is refused (403).
- A random token is made at each launch and injected into the served `index.html` (`window.__LOCAL_TOKEN`). Every `/_local/api/*` and `/_local/status` call must send it as `X-Local-Token`; otherwise 403. Reload the page after restarting the server.

## Site serving

Correct content types, no directory listing, dotfiles and `..` refused, symlinks that leave the site folder refused, GET/HEAD only. `index.html` is sent with `<script>window.__LOCAL_TOKEN=...</script><script src="/_local/claude_shim.js"></script>` inserted before its first `<script>`; the file on disk is not changed.

## Storage layout

    <data>/db/<collection>/<doc id>.json     the document itself (a JSON object); same layout sheet_task.load_db reads
    <data>/db/_deleted/<collection>/<doc id>.<YYYYmmdd-HHMMSS-ffffff>.json    deleted documents (moved, never removed)

Collection names `[A-Za-z0-9][A-Za-z0-9_-]{0,63}`; doc ids `[A-Za-z0-9][A-Za-z0-9._-]{0,127}` (no trailing dot, no Windows reserved names). Writes go to a temp file in the same folder, then `os.replace`. A damaged `.json` is skipped when listing.

## HTTP API (all need the token)

| Call | Result |
|---|---|
| `GET /_local/api/<c>` | `{collection, version, docs:[{id,data}]}` |
| `GET /_local/api/<c>/<id>` | `{id,data}` or 404 |
| `PUT /_local/api/<c>/<id>` (JSON object body) | replace; `{ok,version}` |
| `DELETE /_local/api/<c>/<id>` | moves to `_deleted`; `{ok,deleted}` |
| `GET /_local/api/_versions?c=a,b` | `{versions:{a:"n:mtime:k",...}}`, changes when any file in the collection is added, removed or rewritten (also by another program) |
| `GET /_local/status` | version, port, site, data dir, per-collection counts, count of `_deleted` files |
| `GET /_local/claude_shim.js` | the shim (no token needed; holds no secret) |

Change feed: the shim polls `_versions` every 1.5 s (one request for all subscribed collections) and refetches a collection whose version moved. Local writes refresh at once.

## Runtime API covered (`claude_shim.js`)

- `window.claude.use('db')` resolves to `{collection(c)}`; `collection(c).doc(id).set(obj)`, `.delete()`, `.get()`; `collection(c).get()`; `collection(c).onSnapshot(cb, errcb)` returns an unsubscribe function. `cb(snap)` gets the full collection each time: `snap.docs[]` (each `d.id`, `d.data()`), `snap.size`, `snap.empty`, `snap.forEach`. First call comes right after subscribing. `errcb` is called if the first load fails; polling then retries. Failed writes reject with an Error whose `code` is `storage_error`, `not_found` or `unavailable`.
- `use('downloads')` resolves to `{save({filename, data})}`: a normal browser download (data a Blob or string).
- `use('sample')`, `use('mcp')` (and any other name) **reject** with `code: 'not_declared'`. Every page call site does `.catch(() => null)`, so the page sees null: tone/author/translation buttons, Update and the TinyFish translation fetch see "unavailable".

Not covered: `sample`, `mcp`, `where`/`query` on collections (the page does not use them), `docChanges()` is only a stub (all docs "added"), no per-user identity, no `assets`, `ask`, `files`.

## Page call sites checked

`00_head.js:211-224` (initTone), `41_update_search.js:988-995` (initClips), `18_team_notes.js`, `16_saved_views.js`, `20_translation.js`, `43_update_log.js:63-67,85-98,182-195`, `21_manage_badge.js:55-56` (saveFile). All match.
