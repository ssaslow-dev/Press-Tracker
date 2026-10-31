#!/usr/bin/env python3
"""repack_img.py (STORAGE-v1): rebuild the img/<n>.json shards from the CURRENT article copies.

Why: a tracker version may hold 256 MB; the published set is ~249.6 MB. Old img shards still carry photos that no current
copy points at (stories since removed from the sheet, replaced copies), and shards 3, 15, 102 are partly empty.

What it does (read-only on the source tree; writes only to --out):
  1. Reads every articles/*.json except manifest.json (stories, releases.json, undated.json) and collects, in reading order
     (year files ascending, then releases/undated; entries in file order), every ref  jgimg:<shard>/<16-hex key>.
     This is the set of images some CURRENT copy needs. Anything else in img/ is dropped.
  2. Looks each key up in the source img shards (a key must appear with identical data wherever it appears).
  3. Packs the needed images, in that reading order, into new shards img/0.json, 1.json, ... of about --target-mb each
     (reading order keeps one story's photos in the same shard or two adjacent ones, so a page that opens a story fetches
     few shards).
  4. Rewrites every ref in the article files (raw text substitution, so every other byte is unchanged) to the new
     shard number.
  5. Verifies: every ref in every rewritten article resolves in the NEW shards to exactly the data the OLD ref pointed at;
     no new shard is over target by more than one image; the manifest and article ids are unchanged.
  6. Writes REPACK_REPORT.json and PUBLISH_PLAN.json (files to publish, old shard paths to remove with null) in --out.

Usage:  python3 -I code/repack_img.py [--src work/review_serve] [--out work/repack] [--target-mb 8]
Run it AFTER make_copies on the final copies; make_copies itself numbers shards from 0 (stories) and 100+ (release / large
photos), so a rebuilt copy set must be repacked again before it is published. The kit's publish/ already holds the repacked
set once it has been published. Does not publish.

Order of a publish after a repack (storage stays under the cap, see work/repack/PUBLISH_PLAN.json): see HANDOFF 4.4a.
"""
import argparse, glob, hashlib, json, os, re, sys

REF = re.compile(r'jgimg:(\d+)/([0-9a-f]{16})')


def load_json(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--src', default=os.path.join(here, 'work', 'review_serve'))
    ap.add_argument('--out', default=os.path.join(here, 'work', 'repack'))
    ap.add_argument('--target-mb', type=float, default=8.0)
    a = ap.parse_args()
    target = int(a.target_mb * 1_000_000)
    src, out = a.src, a.out
    if os.path.abspath(out) == os.path.abspath(src):
        sys.exit('--out must differ from --src')
    os.makedirs(os.path.join(out, 'img'), exist_ok=True)
    os.makedirs(os.path.join(out, 'articles'), exist_ok=True)
    for old in glob.glob(os.path.join(out, 'img', '*.json')) + glob.glob(os.path.join(out, 'articles', '*.json')):
        os.remove(old)

    # --- old shards: key -> (old shard, data)
    old_img = {}
    old_where = {}
    for p in sorted(glob.glob(os.path.join(src, 'img', '*.json')), key=lambda x: int(os.path.basename(x)[:-5])):
        n = os.path.basename(p)[:-5]
        for k, v in load_json(p).items():
            if k in old_img and old_img[k] != v:
                sys.exit('key %s differs between shards %s and %s' % (k, old_where[k], n))
            old_img.setdefault(k, v)
            old_where.setdefault(k, n)
    old_total = sum(os.path.getsize(p) for p in glob.glob(os.path.join(src, 'img', '*.json')))

    # --- article files in reading order, refs in order of first use
    man = load_json(os.path.join(src, 'articles', 'manifest.json'))
    files = [os.path.basename(p) for p in glob.glob(os.path.join(src, 'articles', '*.json'))
             if not p.endswith('manifest.json')]
    def fkey(f):
        s = f[:-5]
        return (0, int(s), '') if s.isdigit() else (1, 0, s)
    files.sort(key=fkey)
    order, seen, texts = [], set(), {}
    unresolved, refs_total = [], 0
    for f in files:
        raw = open(os.path.join(src, 'articles', f), encoding='utf-8').read()
        texts[f] = raw
        for m in REF.finditer(raw):
            refs_total += 1
            k = m.group(2)
            if k not in old_img:
                unresolved.append((f, m.group(0)))
            elif k not in seen:
                seen.add(k); order.append(k)
    # a ref whose key is in a different old shard than it names still resolves (key-only lookup); count those
    misnamed = sum(1 for f in files for m in REF.finditer(texts[f]) if m.group(2) in old_img and old_where[m.group(2)] != m.group(1))

    # --- pack
    shards, cur, curb = [], {}, 2
    for k in order:
        v = old_img[k]
        cost = len(k) + len(v) + 8   # "k": "v", with default json separators
        if cur and curb + cost > target:
            shards.append(cur); cur, curb = {}, 2
        cur[k] = v; curb += cost
    if cur:
        shards.append(cur)
    new_of = {}
    new_bytes = 0
    for i, sh in enumerate(shards):
        with open(os.path.join(out, 'img', '%d.json' % i), 'w', encoding='utf-8') as f:
            json.dump(sh, f)
        new_bytes += os.path.getsize(os.path.join(out, 'img', '%d.json' % i))
        for k in sh:
            new_of[k] = i

    # --- rewrite refs
    def sub(m):
        k = m.group(2)
        return 'jgimg:%d/%s' % (new_of[k], k) if k in new_of else m.group(0)
    art_bytes_old = art_bytes_new = 0
    for f in files:
        new = REF.sub(sub, texts[f])
        with open(os.path.join(out, 'articles', f), 'w', encoding='utf-8') as fh:
            fh.write(new)
        art_bytes_old += len(texts[f].encode('utf-8')); art_bytes_new += len(new.encode('utf-8'))
    with open(os.path.join(out, 'articles', 'manifest.json'), 'wb') as fh:
        fh.write(open(os.path.join(src, 'articles', 'manifest.json'), 'rb').read())

    # --- verify against the output tree only
    new_img = {}
    for i in range(len(shards)):
        new_img[i] = load_json(os.path.join(out, 'img', '%d.json' % i))
    bad, checked, ids = [], 0, 0
    for f in files:
        old_d, new_d = json.loads(texts[f]), load_json(os.path.join(out, 'articles', f))
        if list(old_d) != list(new_d):
            bad.append((f, 'ids differ'))
        for sid, html in new_d.items():
            ids += 1
            ohtml = old_d.get(sid, '')
            orefs, nrefs = REF.findall(ohtml), REF.findall(html)
            if len(orefs) != len(nrefs):
                bad.append((f, sid, 'ref count'))
                continue
            for (os_, ok), (ns, nk) in zip(orefs, nrefs):
                checked += 1
                if ok != nk or int(ns) not in new_img or new_img[int(ns)].get(nk) != old_img.get(ok):
                    bad.append((f, sid, ok))
            if REF.sub('', html) != REF.sub('', ohtml):
                bad.append((f, sid, 'non-ref text changed'))
    man_ids = set(man['articles'])
    all_ids = set()
    for f in files:
        all_ids |= set(load_json(os.path.join(out, 'articles', f)))
    if man_ids != all_ids:
        bad.append(('manifest', 'ids differ from article files'))
    over = [i for i, p in enumerate(sorted(glob.glob(os.path.join(out, 'img', '*.json'))))
            if os.path.getsize(os.path.join(out, 'img', '%d.json' % i)) > target + 2_000_000]

    old_paths = sorted('img/' + os.path.basename(p) for p in glob.glob(os.path.join(src, 'img', '*.json')))
    new_paths = ['img/%d.json' % i for i in range(len(shards))]
    gone = [p for p in old_paths if p not in new_paths]
    dropped = [k for k in old_img if k not in new_of]
    rep = {
        'src': src, 'out': out, 'target_bytes': target,
        'old_shards': len(old_paths), 'new_shards': len(shards),
        'old_img_bytes': old_total, 'new_img_bytes': new_bytes, 'img_saved_bytes': old_total - new_bytes,
        'article_bytes_old': art_bytes_old, 'article_bytes_new': art_bytes_new,
        'images_old': len(old_img), 'images_kept': len(new_of), 'images_dropped': len(dropped),
        'dropped_bytes': sum(len(old_img[k]) + len(k) + 8 for k in dropped),
        'refs_total': refs_total, 'refs_unresolved_in_source': len(unresolved), 'refs_naming_wrong_shard_but_resolved': misnamed,
        'refs_verified': checked, 'articles_checked': ids, 'verify_failures': len(bad), 'shards_over_target': over,
        'shard_sizes': [os.path.getsize(os.path.join(out, 'img', '%d.json' % i)) for i in range(len(shards))],
        'total_saved_bytes': (old_total - new_bytes) + (art_bytes_old - art_bytes_new),
    }
    with open(os.path.join(out, 'REPACK_REPORT.json'), 'w') as f:
        json.dump(rep | {'unresolved': unresolved[:50], 'failures': bad[:50]}, f, indent=1)
    plan = {'note': 'Publish these files (published path -> file under this folder), then remove the paths in "remove" with null. '
                    'Order and storage: HANDOFF 4.4a.',
            'replace_img': new_paths, 'replace_articles': ['articles/' + f for f in files],
            'remove': gone, 'unchanged': ['articles/manifest.json']}
    with open(os.path.join(out, 'PUBLISH_PLAN.json'), 'w') as f:
        json.dump(plan, f, indent=1)
    print(json.dumps({k: rep[k] for k in rep if k != 'shard_sizes'}, indent=1))
    sys.exit(1 if bad or unresolved else 0)


if __name__ == '__main__':
    main()
