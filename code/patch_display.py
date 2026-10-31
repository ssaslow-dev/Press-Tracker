"""T3 (agent-display): patch the tracker JS for the new Coverage-sheet data contract.
Usage: python3 patch_display.py <in.js> <out.js>   (in = lib/work/tracker_original.js)"""
import sys
src = open(sys.argv[1]).read()
n_ok = 0
def rep(old, new, count=1):
    global src, n_ok
    c = src.count(old)
    if c != count:
        raise SystemExit(f'anchor matched {c}x (want {count}): {old[:90]!r}')
    src = src.replace(old, new); n_ok += 1

# 1. ID helpers + reprint normalization, right after the data block is parsed
rep("""const D = JSON.parse(document.getElementById('data').textContent);
""", """const D = JSON.parse(document.getElementById('data').textContent);
/* Entries are keyed by Story ID (jg-NNNNN) from the Coverage sheet. r.code is the story's old tracker code (jg-xxxxxx),
   kept only to find its saved copy (articles/, img/, pdf/) and to carry over shared-store docs saved under it.
   The "idmap" block maps old code -> Story ID; r.aid / rep.aid are the sheet's Article IDs (nb-/pq-/ws-). */
const IDMAP = (() => { try { const el = document.getElementById('idmap'); return (el && JSON.parse(el.textContent)) || {}; } catch(e){ return {}; } })();
const sidOf = k => (k && Object.prototype.hasOwnProperty.call(IDMAP, k)) ? IDMAP[k] : k;
const CODE_OF = new Map(), AID_OF = new Map();
D.forEach(r => { delete r.conf; if (r.code) CODE_OF.set(r.id, r.code); if (r.aid) AID_OF.set(String(r.aid).toLowerCase(), r.id);
  (Array.isArray(r.reps) ? r.reps : []).forEach(p => { if (p && p.aid) AID_OF.set(String(p.aid).toLowerCase(), r.id); }); });
// the key a story's saved copy is filed under: its old code when it has one, else its Story ID
const fileKey = id => CODE_OF.get(id) || id;
// shared-store docs saved under an old code are read first, so a doc saved under the Story ID wins
const oldFirst = docs => docs.filter(d => sidOf(d.id) !== d.id).concat(docs.filter(d => sidOf(d.id) === d.id));
/* reprints = every Reprint row in the sheet with the story's Story ID (r.reps); "Reprinted in" names each outlet once,
   leaving out the story's own outlet. r.also (text) and r.rc ([outlet, county] pairs) are rebuilt from r.reps. */
function repNames(r){
  // one outlet, one name: drops "(…)", feed suffixes ("Targeted News Service: U.S. Business"), "Today's Edition" and ", The"
  const k = x => nrmName(String(x||'').replace(/\\s*\\(.*\\)\\s*$/,'').replace(/\\s*today['’]?s edition/ig,'').replace(/\\s*:.*$/,'').replace(/,\\s*the\\s*$/i,''));
  const seen = new Set([k(r.pub), k(r.outlet)].filter(Boolean)), out = [];
  (r.reps || []).forEach(p => { const n = String((p && p.outlet) || '').replace(/[;\\n]+/g, ' ').trim(), key = k(n); if (!n || !key || seen.has(key)) return; seen.add(key); out.push(n); });
  return out;
}
function syncReps(r){
  if (!Array.isArray(r.reps)) return;
  if (!r._alsoEdit) r.also = repNames(r).join('; ');
  const seen = new Set(); r.rc = [];
  r.reps.forEach(p => { if (!p || !p.county || (p.state && p.state !== 'CA')) return; const o = String(p.outlet||'').trim(), key = o + '|' + p.county; if (!o || seen.has(key)) return; seen.add(key); r.rc.push([o, p.county]); });
}
D.forEach(syncReps);
""")

# 2. reprint count / names / missing read r.reps
rep("""function reprintCount(r){ if (!r.also) return r.rep; const n = alsoNames(r).length + alsoMissing(r); return n || r.rep; }""",
"""function reprintCount(r){ if (Array.isArray(r.reps) && !r._alsoEdit) return Math.max(0, +r.rep || 0) + r.reps.filter(p => p && (p.src === 'live' || p.src === 'store')).length || repNames(r).length; if (!r.also) return r.rep; const n = alsoNames(r).length + alsoMissing(r); return n || r.rep; }""")
rep("""function alsoNames(r){
  const seen = new Set(), own = nrmName(r.pub);""", """function alsoNames(r){
  if (Array.isArray(r.reps) && !r._alsoEdit) return repNames(r);
  const seen = new Set(), own = nrmName(r.pub);""")
rep("""function alsoMissing(r){ const m""", """function alsoMissing(r){ if (Array.isArray(r.reps) && !r._alsoEdit) return 0; const m""")

# 3. live reprints (Update finds and the shared "reprints" store) join r.reps
rep("""  if (!outlet || ranIn(r, outlet, '')) return false;
  const parts = (r.also || '').split(';').map(x => x.trim()).filter(Boolean);""", """  if (!outlet || ranIn(r, outlet, '')) return false;
  if (Array.isArray(r.reps)){ r.reps.push({ aid:'', outlet, date:'', county:'', state:'', link:'', hl:'', src:'live' }); syncReps(r); r.pick = reprintCount(r); r._s = searchStr(r); return true; }
  const parts = (r.also || '').split(';').map(x => x.trim()).filter(Boolean);""")
rep("""    if (ranIn(r, p.outlet, hostOf(p.link))) return;
    const parts = (r.also || '').split(';').map(x => x.trim()).filter(Boolean);""", """    if (ranIn(r, p.outlet, hostOf(p.link))) return;
    if (Array.isArray(r.reps)){ r.reps.push({ aid:'', outlet: p.outlet, date: p.date || '', county:'', state:'', link: p.link || '', hl:'', src:'store' }); syncReps(r); r.pick = reprintCount(r); r._s = searchStr(r); n++; return; }
    const parts = (r.also || '').split(';').map(x => x.trim()).filter(Boolean);""")
rep("""  const story = VS(d.story, 30), outlet""", """  const story = sidOf(VS(d.story, 30)), outlet""")
# an edited "Reprinted in" replaces the generated list for that story
rep("""    else r[k] = v;
  });
  if (ch){ r._s = searchStr(r); r.pick = reprintCount(r); }""", """    else { r[k] = v; if (k==='also') r._alsoEdit = true; }
  });
  if (ch){ r._s = searchStr(r); r.pick = reprintCount(r); }""")

# 4. saved copies are filed under the old code
rep("""  return (await shardCache.get(path))[id] ?? null;""", """  const shard = await shardCache.get(path); return shard[fileKey(id)] ?? shard[id] ?? null;""")
rep("""if (r.ok){ const j = await r.json(); remote = j.articles || {}; } } catch(e) {} }""",
    """if (r.ok){ const j = await r.json(); remote = {}; Object.entries(j.articles || {}).forEach(([k, p]) => { const s = sidOf(k); if (!remote[s] || s === k) remote[s] = p; }); } } catch(e) {} }""")
rep("""(await IDB.all()).forEach(([k,v]) => { if (byId.has(k)) local.set(k, v); });""",
    """(await IDB.all()).forEach(([k,v]) => { const s = sidOf(k); if (byId.has(s) && (s === k || !local.has(s))) local.set(s, v); });""")
# a dropped file named by Story ID, old code or Article ID (nb-/pq-/ws-) finds its story
rep("""  if (byId.has(base.toLowerCase())) return base.toLowerCase();""",
    """  const bl = base.toLowerCase(), byName = byId.has(bl) ? bl : byId.has(sidOf(bl)) ? sidOf(bl) : AID_OF.get(bl); if (byName && byId.has(byName)) return byName;""")

# 5. shared-store docs saved under old codes apply to the Story ID
rep("""function applyTone(id, t){ const r""", """function applyTone(id, t){ id = sidOf(id); const r""")
rep("""function applyAuthor(id, t){
  const r""", """function applyAuthor(id, t){
  id = sidOf(id); const r""")
rep("""function applyTr(id, t){
  const r""", """function applyTr(id, t){
  id = sidOf(id); const r""")
rep("""      let ch = false; snap.docs.forEach(d => { const t = d.data(); if (applyTone(d.id, t)){ ch = true; lsSave(d.id, t); } });
      if (first){ first = false; pushLocalTones(new Set(snap.docs.map(d => d.id))); tReady(); }""",
"""      let ch = false; oldFirst(snap.docs).forEach(d => { const t = d.data(); if (applyTone(d.id, t)){ ch = true; lsSave(sidOf(d.id), t); } });
      if (first){ first = false; pushLocalTones(new Set(snap.docs.map(d => sidOf(d.id)))); tReady(); }""")
rep("""      let ch = false; snap.docs.forEach(d => { const t = d.data(); if (applyAuthor(d.id, t)){ ch = true; lsASave(d.id, t); } });
      if (firstA){ firstA = false; pushLocalAuthors(new Set(snap.docs.map(d => d.id))); aReady(); }""",
"""      let ch = false; oldFirst(snap.docs).forEach(d => { const t = d.data(); if (applyAuthor(d.id, t)){ ch = true; lsASave(sidOf(d.id), t); } });
      if (firstA){ firstA = false; pushLocalAuthors(new Set(snap.docs.map(d => sidOf(d.id)))); aReady(); }""")
rep("""  for (const [id, t] of Object.entries(lsTones())){
    if (inDb.has(id)""", """  for (const [k, t] of Object.entries(lsTones())){ const id = sidOf(k);
    if (inDb.has(id)""")
rep("""  for (const [id, t] of Object.entries(lsAuthors())){
    if (inDb.has(id)""", """  for (const [k, t] of Object.entries(lsAuthors())){ const id = sidOf(k);
    if (inDb.has(id)""")
rep("""  Object.entries(lsNotes()).forEach(([k,v]) => { if (byId.has(k) && v && v.text) NOTES.set(k, v); });""",
    """  Object.entries(lsNotes()).forEach(([k,v]) => { const s = sidOf(k); if (byId.has(s) && v && v.text && (s === k || !NOTES.has(s))) NOTES.set(s, v); });""")
rep("""    snap.docs.forEach(d => { const x = d.data(); if (x && typeof x.text==='string'){ if (x.text.trim()) NOTES.set(d.id, { text: x.text.slice(0,2000), at: String(x.at||'').slice(0,10) }); else NOTES.delete(d.id); } });""",
    """    oldFirst(snap.docs).forEach(d => { const x = d.data(), id = sidOf(d.id); if (x && typeof x.text==='string'){ if (x.text.trim()) NOTES.set(id, { text: x.text.slice(0,2000), at: String(x.at||'').slice(0,10) }); else NOTES.delete(id); } });""")
rep("""    let ch = false; snap.docs.forEach(d => { if (applyTr(d.id, d.data())) ch = true; });""",
    """    let ch = false; oldFirst(snap.docs).forEach(d => { if (applyTr(d.id, d.data())) ch = true; });""")
rep("""    snap.docs.forEach(d => { const e = cleanEdit(d.data()); if (!e) return; EDITS.set(d.id, e); if (applyEdit(d.id, e)) ch = true; });""",
    """    oldFirst(snap.docs).forEach(d => { const e = cleanEdit(d.data()), id = sidOf(d.id); if (!e) return; EDITS.set(id, e); if (applyEdit(id, e)) ch = true; });""")
# a clip saved under an old code is already a row in the sheet: it is in D under its Story ID
rep("""    if (!r || byId.has(r.id) || known.urls.has(normU(r.link))) return;""",
    """    if (!r || byId.has(r.id) || sidOf(r.id) !== r.id || known.urls.has(normU(r.link))) return;""")

# 7. Confirmed / Unconfirmed is dropped
rep("""pub: rankOf('pub'), conf:['Confirmed','Unconfirmed'], role:""", """pub: rankOf('pub'), role:""")
rep("""  {key:'conf', label:'Confidence', hint:'How sure we are the story mentions him. See Definitions under Manage.'},
""", "")
rep("""lang:new Set(),conf:new Set(),tone:new Set()}""", """lang:new Set(),tone:new Set()}""")
rep("""  const conf = c => D.filter(r=>r.conf===c).length;
""", "")
rep("""        <dt>Confidence</dt><dd><b>Confirmed</b> (${fmt(conf('Confirmed'))}): ${CONF_TEXT['Confirmed']}<br><b>Unconfirmed</b> (${fmt(conf('Unconfirmed'))}): ${CONF_TEXT['Unconfirmed']}</dd>
""", "")
rep("""      ${row('info', `${pl(n('unconf'),'story is','stories are')} unconfirmed`, CONF_TEXT['Unconfirmed'], 'unconf')}
""", "")
rep("""  unconf: { label:'Not confirmed', f: r => r.conf==='Unconfirmed' },
""", "")
rep("""['Reprinted in','also'],['Confidence','conf'],""", """['Reprinted in','also'],""")
rep("""How Gabriel appears\\tReprints\\tReprinted in\\tConfidence\\tTone\\tTone note\\tLink'].concat(rows.map(r=>[r.date,r.outlet,r.author,r.hl,r.topic,r.bills.join('; '),r.reach,r.media,r.role,r.pick,r.also,r.conf,rated""",
    """How Gabriel appears\\tReprints\\tReprinted in\\tTone\\tTone note\\tLink'].concat(rows.map(r=>[r.date,r.outlet,r.author,r.hl,r.topic,r.bills.join('; '),r.reach,r.media,r.role,r.pick,r.also,rated""")
rep("""  {k:'conf', label:'Confidence', opts:() => RANK.conf}, {k:'lang'""", """  {k:'lang'""")

# 8. a story with no Reach (blank in the sheet) shows an empty Reach cell instead of an empty tag
rep("""      <td class="rc"><button type="button" class="tag tlink" data-fk="reach" data-fv="${esc(r.reach)}" title="Filter to ${esc(r.reach)}"><span class="sw" style="background:${colorFor('reach',r.reach)}"></span>${esc(r.reach)}</button></td>""",
    """      <td class="rc">${r.reach ? `<button type="button" class="tag tlink" data-fk="reach" data-fv="${esc(r.reach)}" title="Filter to ${esc(r.reach)}"><span class="sw" style="background:${colorFor('reach',r.reach)}"></span>${esc(r.reach)}</button>` : ''}</td>""")

open(sys.argv[2], 'w').write(src)
print('applied', n_ok, 'edits')
