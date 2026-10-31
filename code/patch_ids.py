#!/usr/bin/env python3
"""T23: tracker JS -> new ID scheme (Article IDs 5-digit numbers, Story IDs sNNNNN).
Usage: python3 -I patch_ids.py IN.js OUT.js     (IN = the merged tracker JS before T23, e.g. work/tmp_agent-ids/js_merged.pre_ids.js)
Every edit is anchored and must match exactly once, or the script stops.
- sidOf: legacy Story IDs jg-NNNNN (shared-store docs, localStorage, IndexedDB, saved-copy keys made before the
  migration) -> sNNNNN; idmap entries win (jg-04196 -> s01596 for removed duplicates).
- Story-id validators accept sNNNNN plus jg- temporary codes (new finds keep jg- + 6 hex until the rebuild).
- Update button placeholders: NEW-<run>-<n> (Article ID), sNEW-<run>-<n> (Story ID); the sheet task assigns the real
  numbers (next in the single 5-digit sequence; next sNNNNN). cleanRun keeps old- and new-format id maps.
- Saved copies filed under a legacy jg-NNNNN key are still found.
- Dropped files named like the library (nb00034o-s00012.pdf, ws09761.html, 00034, s00012) are matched.
"""
import sys

SRC, OUT = sys.argv[1:3]
js = open(SRC, encoding='utf-8').read()

EDITS = [
    # header comment
    ("""/* Entries are keyed by Story ID (jg-NNNNN) from the Coverage sheet. r.code is the story's old tracker code (jg-xxxxxx),""",
     """/* Entries are keyed by Story ID (sNNNNN; jg-NNNNN before the 2026-10-27 ID migration) from the Coverage sheet. r.code is the story's old tracker code (jg-xxxxxx),"""),
    ("""   The "idmap" block maps old code -> Story ID; r.aid / rep.aid are the sheet's Article IDs (nb-/pq-/ws-). */""",
     """   The "idmap" block maps old code -> Story ID; r.aid / rep.aid are the sheet's Article IDs (5-digit numbers, e.g. 00034). */"""),
    # sidOf + validators
    ("""const sidOf = k => (k && Object.prototype.hasOwnProperty.call(IDMAP, k)) ? IDMAP[k] : k;""",
     """const sidOf = k => (k && Object.prototype.hasOwnProperty.call(IDMAP, k)) ? IDMAP[k] : (typeof k === 'string' && /^jg-\\d{5}$/.test(k) ? 's' + k.slice(3) : k);
// a story id the shared store may hold: a Story ID (sNNNNN) or a jg- code (old tracker code / temporary code of a new find)
const SID_OK = id => typeof id === 'string' && /^(s\\d{5}|jg-[0-9a-z]{4,24})$/.test(id);
const SID_ANY = id => typeof id === 'string' && /^(s\\d{5}|jg-[0-9a-z]{1,24})$/.test(id);
// a saved copy filed under the Story ID it had before the ID migration
const legacyKey = id => /^s\\d{5}$/.test(id) ? 'jg-' + id.slice(1) : id;"""),
    ("""  const shard = await shardCache.get(path); return shard[fileKey(id)] ?? shard[id] ?? null;""",
     """  const shard = await shardCache.get(path); return shard[fileKey(id)] ?? shard[id] ?? shard[legacyKey(id)] ?? null;"""),
    ("""    if (inDb.has(id) || BUILTIN.has(id) || !/^jg-[0-9a-z]{4,24}$/.test(id) || !t || !TONE_OK.has(t.tone)) continue;""",
     """    if (inDb.has(id) || BUILTIN.has(id) || !SID_OK(id) || !t || !TONE_OK.has(t.tone)) continue;"""),
    ("""    if (inDb.has(id) || BUILTIN_A.has(id) || !/^jg-[0-9a-z]{4,24}$/.test(id) || !t || typeof t.author !== 'string') continue;""",
     """    if (inDb.has(id) || BUILTIN_A.has(id) || !SID_OK(id) || !t || typeof t.author !== 'string') continue;"""),
    ("""  if (!/^jg-[0-9a-z]{4,24}$/.test(id) || !d) return null;""",
     """  if (!SID_OK(id) || !d) return null;"""),
    ("""  if (!/^jg-[0-9a-z]{1,24}$/.test(story) || !outlet || !/^https?:\\/\\//i.test(link)) return null;""",
     """  if (!SID_ANY(story) || !outlet || !/^https?:\\/\\//i.test(link)) return null;"""),
    # matchFile: library names
    ("""  const bl = base.toLowerCase(), byName = byId.has(bl) ? bl : byId.has(sidOf(bl)) ? sidOf(bl) : AID_OF.get(bl); if (byName && byId.has(byName)) return byName;""",
     """  const bl = base.toLowerCase(), byName = byId.has(bl) ? bl : byId.has(sidOf(bl)) ? sidOf(bl) : AID_OF.get(bl); if (byName && byId.has(byName)) return byName;
  // library names: <nb|pq|ws><Article ID><o|r>-s<Story ID> (nb00034o-s00012.pdf), or without the Story ID part
  const lib = bl.match(/^(?:nb|pq|ws)?(\\d{5})[or]?(?:-(s\\d{5}))?$/);
  if (lib){ if (lib[2] && byId.has(lib[2])) return lib[2]; const v = AID_OF.get(lib[1]); if (v && byId.has(v)) return v; }"""),
    # Update button
    ("""'Tracker story code','Search lookup (Oct 26)','Role']""",
     """'Tracker story code','Search lookup (Oct 26)','Role','Old Article ID','Old Print Article ID']"""),
    ("""   (ws-NEW-<run>-<n>, jg-NEW-<run>-<n>) that the sheet task replaces with real ws-/jg- numbers, writing the mapping back""",
     """   (NEW-<run>-<n> for Article IDs, sNEW-<run>-<n> for Story IDs) that the sheet task replaces with real ones (the next numbers
   in the single 5-digit Article ID sequence, and the next sNNNNN), writing the mapping back"""),
    ("""  const aid = () => `ws-NEW-${run}-${++n}`;""", """  const aid = () => `NEW-${run}-${++n}`;"""),
    ("""  stories.forEach(r => sidOf.set(r.id, `jg-NEW-${run}-${++s}`));""", """  stories.forEach(r => sidOf.set(r.id, `sNEW-${run}-${++s}`));"""),
    ("""    const st = byId.get(p.story), map = covLoad().idmap;""",
     """    const st = byId.get(p.story) || byId.get(IDMAP_SID(p.story)), map = covLoad().idmap;"""),
    ("""    const sid = sidOf.get(p.story) || (/^jg-\\d{5}$/.test(p.story) ? p.story : map[p.story] || p.story);
    out.push(repRow(p, sid, st, sid === p.story && !/^jg-\\d{5}$/.test(p.story) ? p.story : ''));""",
     """    const sid = sidOf.get(p.story) || (/^s\\d{5}$/.test(IDMAP_SID(p.story)) ? IDMAP_SID(p.story) : map[p.story] || p.story);
    out.push(repRow(p, sid, st, sid === p.story && !/^s\\d{5}$/.test(p.story) ? p.story : ''));"""),
    ("""const covResolve = id => byId.has(id) ? id : (""",
     """// legacy jg-NNNNN -> sNNNNN (the page-level sidOf; proposeRows has its own local sidOf map)
const IDMAP_SID = id => sidOf(id);
const covResolve = id => byId.has(id) ? id : byId.has(IDMAP_SID(id)) ? IDMAP_SID(id) : ("""),
    # cleanRun
    ("""  const ids = v => (Array.isArray(v) ? v : []).filter(x => typeof x === 'string' && /^jg-[0-9a-z]{1,24}$/.test(x)).slice(0, 1000);""",
     """  const ids = v => (Array.isArray(v) ? v : []).filter(x => SID_ANY(x)).slice(0, 1000);"""),
    ("""    const v = d.ids[k]; if (/^(ws|jg)-NEW-[0-9a-z-]{1,40}$/.test(k) && typeof v === 'string' && /^(ws|pq|nb|jg)-\\d{5}$/.test(v)) rid[k] = v; });""",
     """    const v = d.ids[k]; if (/^(s?NEW|ws-NEW|jg-NEW)-[0-9a-z-]{1,40}$/.test(k) && typeof v === 'string' && /^(\\d{5}|s\\d{5}|(ws|pq|nb|jg)-\\d{5})$/.test(v)) rid[k] = v; });"""),
    ("""    reprints: (Array.isArray(d.reprints) ? d.reprints : []).filter(p => p && /^jg-/.test(p.story))""",
     """    reprints: (Array.isArray(d.reprints) ? d.reprints : []).filter(p => p && SID_ANY(p.story))"""),
]

for old, new in EDITS:
    n = js.count(old)
    if n != 1:
        sys.exit(f'anchor matched {n} times: {old[:90]!r}')
    js = js.replace(old, new)
open(OUT, 'w', encoding='utf-8').write(js)
print(f'{len(EDITS)} edits ->', OUT)
