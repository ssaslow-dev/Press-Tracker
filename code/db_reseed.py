#!/usr/bin/env python3
"""db_reseed.py: turn an artifact-database export into ArtifactData `batch` payloads (agent-handoffkit, 2026-10-28; HANDOFF 0.5).

Python cannot call ArtifactData, so the export and the re-seed are done by a Claude session; this script only converts files.

Export layout (written by the session that exports, with ArtifactData list/get on the OLD artifact):
  <export>/<artifact>/<collection>/<doc_id>.json      artifact = tracker | review (any folder name works)
A file may hold
  - the document's data object itself (doc id = file name without .json), or
  - {"doc_id"|"id": ..., "data": {...}}  (one doc; its id wins over the file name), or
  - a list of such {"doc_id"|"id", "data"} objects (a saved `list` page).
Doc ids are kept unchanged. Files whose name starts with "_" (e.g. _counts.json) are skipped.

  python3 -I code/db_reseed.py EXPORT_DIR OUT_DIR [--max 50] [--artifact tracker]
writes OUT_DIR/<artifact>/batch_NNN.json, each a list of <= --max writes
  [{"op": "set", "collection": C, "doc_id": D, "data": {...}}, ...]
(the format of build/review/seed/batch_*.json), plus OUT_DIR/counts.json {artifact: {collection: n}}.
Feed each batch file to ArtifactData action "batch" against the NEW artifact url, in order.
"""
import argparse, json, os, sys


def docs_in(path, default_id):
    obj = json.load(open(path, encoding='utf-8'))
    wrapped = lambda it: isinstance(it, dict) and isinstance(it.get('data'), dict) and ('doc_id' in it or 'id' in it)
    if isinstance(obj, list):
        bad = [i for i, it in enumerate(obj) if not wrapped(it)]
        if bad:
            raise SystemExit(f'{path}: list items {bad[:5]} lack doc_id/id + data')
        return [(str(it.get('doc_id', it.get('id'))), it['data']) for it in obj]
    if wrapped(obj):
        return [(str(obj.get('doc_id', obj.get('id'))), obj['data'])]
    if isinstance(obj, dict):
        return [(default_id, obj)]
    raise SystemExit(f'{path}: not a document ({type(obj).__name__})')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('export'); ap.add_argument('out')
    ap.add_argument('--max', type=int, default=50)
    ap.add_argument('--artifact', action='append', help='only these artifact folders (default: all)')
    a = ap.parse_args()
    if a.max < 1 or a.max > 50:
        sys.exit('--max must be 1..50 (ArtifactData batch limit)')
    counts = {}
    for art in sorted(os.listdir(a.export)):
        ad = os.path.join(a.export, art)
        if not os.path.isdir(ad) or (a.artifact and art not in a.artifact):
            continue
        writes, seen = [], set()
        for coll in sorted(os.listdir(ad)):
            cd = os.path.join(ad, coll)
            if not os.path.isdir(cd):
                continue
            n = 0
            for fn in sorted(os.listdir(cd)):
                if not fn.endswith('.json') or fn.startswith('_'):
                    continue
                for did, data in docs_in(os.path.join(cd, fn), fn[:-5]):
                    if (coll, did) in seen:
                        sys.exit(f'duplicate doc {art}/{coll}/{did}')
                    seen.add((coll, did))
                    writes.append({'op': 'set', 'collection': coll, 'doc_id': did, 'data': data})
                    n += 1
            counts.setdefault(art, {})[coll] = n
        od = os.path.join(a.out, art)
        os.makedirs(od, exist_ok=True)
        for i in range(0, len(writes), a.max):
            with open(os.path.join(od, f'batch_{i // a.max:03d}.json'), 'w', encoding='utf-8') as f:
                json.dump(writes[i:i + a.max], f, ensure_ascii=False)
        print(f'{art}: {len(writes)} docs in {(len(writes) + a.max - 1) // a.max} batches -> {od}')
    os.makedirs(a.out, exist_ok=True)
    json.dump(counts, open(os.path.join(a.out, 'counts.json'), 'w'), indent=1)
    print(json.dumps(counts))


if __name__ == '__main__':
    main()
