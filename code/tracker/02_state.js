/* ---------- state ---------- */
const FACETS = [
  {key:'topic', label:'Issue', sw:true, open:true},
  {key:'bills', label:'Bills', search:true, limit:8, open:true, hint:'Gabriel bills the story covers. A story can cover several.'},
  {key:'reach', label:'Reach', sw:true, open:true, hint:'The kind of outlet that ran the story.'},
  {key:'role', label:'How Gabriel appears', hint:'Named in the headline, or mentioned in the story.'},
  {key:'depth', label:'Mention depth', hint:'How much of the story is about him (the "Quoted" tier here is a depth level, separate from the Direct quote filter): Featured, Quoted, Named, or List-only (named only inside a roster, co-author or endorser list). List-only stories are left out of headline counts unless "Include list-only mentions" is on.'},   /* INCL-v1 */
  {key:'quoted', label:'Direct quote', hint:'Stories that directly quote Gabriel: his own words in quotation marks, or his spoken words in a transcript. Not set for op-eds he wrote. (Not the same as Mention depth "Quoted".)'},   /* QUOTED-v1 */
  {key:'media', label:'Medium', hint:'The kind of outlet: newspaper, TV station, radio, podcast and so on.'},
  {key:'fmt', label:'Format', hint:'What this clip is: a web article, a print page, a broadcast segment, a video clip, an audio segment or a podcast episode. A TV station can have both web articles and broadcast segments.'},
  {key:'pub', label:'Outlet', search:true, limit:8},
  {key:'author', label:'Reporter', search:true, limit:8, hint:'Who wrote the story. Co-authors are listed one by one, and a co-written story counts for each of them.'},
  {key:'county', label:'County', search:true, limit:8, hint:'Home county of the local outlet that ran the story or a reprint of it. Statewide and national outlets have none.'},
  {key:'state', label:'State', search:true, limit:8, hint:'Home state of the out-of-state regional or local outlet that ran the story or a reprint of it (GEOMAP-v1). California, national outlets and wires have none.'},
  {key:'lang', label:'Language', hint:'The language the story ran in. Stories in other languages show an English headline under the original.'},
  {key:'tone', label:'Tone', sw:true, hint:'How the story portrays Gabriel. Rated from saved copies only.'},
];
const S = { qv:'issues', rel:'loyal', q:'', sel:{topic:new Set(),bills:new Set(),reach:new Set(),role:new Set(),depth:new Set(),quoted:new Set(),media:new Set(),fmt:new Set(),pub:new Set(),author:new Set(),county:new Set(),state:new Set(),lang:new Set(),tone:new Set()},
  when:'all', d0:null, d1:null, whenLabel:'', saved:'all', sort:{key:'date',dir:-1}, page:0, per:50, tab:'ov', fq:{}, fall:{}, openId:null, flag:'', ranin:'', pick:new Set(), mg:'upd', _naming:false, openFacets:new Set(FACETS.filter(f=>f.open).map(f=>f.key)) };
let YEARS, yMax, WHEN;
/* year lists are rebuilt when Update database brings in a story from a year the log didn't have yet */
function setYears(){
  YEARS = [...new Set(D.map(r=>r.year))].filter(Boolean).sort((a,b)=>a-b);   /* D3: an undated story has year 0 */
  yMax = YEARS[YEARS.length-1];
  WHEN = [
    ['all','All dates'], ['30','Last 30 days'], ['90','Last 90 days'], ['365','Last 12 months'],
    ...YEARS.slice().reverse().filter(y=>y>=2017).map(y=>['y'+y, y===yMax ? `${y} so far` : String(y)]), ['early','Before 2017']
  ];
}
setYears();
function applyWhen(v){
  S.when = v; S.whenLabel = '';
  if (v==='all'){ S.d0 = S.d1 = null; }
  else if (/^\d+$/.test(v)){ S.d0 = addDays(TODAY, -(+v - 1)); S.d1 = null;   /* REVIEW4-PAGE-v1 A1: 'Last 30 days' = today and the 29 days before it, the same window Home counts */ }
  else if (v[0]==='y'){ S.d0 = v.slice(1); S.d1 = v.slice(1)+'-99'; }
  else if (v==='early'){ S.d0 = null; S.d1 = '2016-99'; }
}
// Custom range: pick any from and to dates; the result shows as its own entry in the menu
function openRange(sel, rp){
  sel.value = S.when; document.querySelector('.range-pop')?.remove();
  const full = v => /^\d{4}-\d{2}-\d{2}$/.test(v||'') ? v : '', min = `${YEARS[0]}-01-01`;
  const pop = document.createElement('div'); pop.className = 'range-pop'; pop.setAttribute('role','dialog'); pop.setAttribute('aria-label','Custom date range');
  pop.innerHTML = `<label>From<input type="date" data-r0 min="${min}" max="${TODAY}" value="${full(S.d0)}"></label><label>To<input type="date" data-r1 min="${min}" max="${TODAY}" value="${full(S.d1) || TODAY}"></label><div class="range-err" aria-live="polite"></div><div class="range-acts"><button class="btn" data-rcancel>Cancel</button><button class="btn primary" data-rapply>Apply</button></div>`;
  document.body.appendChild(pop);
  const b = sel.getBoundingClientRect(), w = pop.offsetWidth;
  pop.style.top = Math.min(b.bottom + 6, innerHeight - pop.offsetHeight - 8) + 'px'; pop.style.left = Math.max(8, Math.min(b.left, innerWidth - w - 8)) + 'px';
  const close = () => { pop.remove(); document.removeEventListener('mousedown', out, true); document.removeEventListener('keydown', esc_, true); };
  const out = e => { if (!pop.contains(e.target)) close(); }, esc_ = e => { if (e.key==='Escape'){ e.stopPropagation(); close(); sel.focus(); } };
  setTimeout(() => { document.addEventListener('mousedown', out, true); document.addEventListener('keydown', esc_, true); }, 0);
  pop.querySelector('[data-rcancel]').onclick = close;
  const apply = () => {
    let a = pop.querySelector('[data-r0]').value, z = pop.querySelector('[data-r1]').value;
    if (!a && !z){ pop.querySelector('.range-err').textContent = 'Pick a from date, a to date, or both.'; return; }
    if (a && z && a > z) [a, z] = [z, a];
    const lb = d => dateLabel({date:d, prec:'day'});
    S.when = 'custom'; S.d0 = a || null; S.d1 = z || null;
    S.whenLabel = a && z ? (a===z ? lb(a) : `${lb(a)} – ${lb(z)}`) : a ? `Since ${lb(a)}` : `Through ${lb(z)}`;
    close(); renderWhen(); S.page = 0; if (rp){ tuneChart(); S.qv = null; } render();
  };
  pop.querySelector('[data-rapply]').onclick = apply;
  pop.addEventListener('keydown', e => { if (e.key==='Enter' && e.target.matches('input')) apply(); });
  pop.querySelector('[data-r0]').focus();
}
function setMonth(k){ S.when = 'custom'; S.d0 = k; S.d1 = k+'-99'; S.whenLabel = monthName(k); }

D.forEach(r => { r._s = searchStr(r); });
// REPCOUNT-v1: reprints = distinct outlets other than the story's own house (repNames); a story with no reps list keeps its "Reprinted in" text
function reprintCount(r){ if (Array.isArray(r.reps) && !r._alsoEdit) return repNames(r).length; if (!r.also) return r.rep; const n = alsoNames(r).length + alsoMissing(r); return n || r.rep; }
/* REVIEW4-PAGE-v1 D1: Clips search. Every word must be found (anywhere: headline, outlet, byline, saved text), in any order; a word
   matches at the start of a word (longer than 3 letters) or as a whole word (3 letters or fewer: "ICE" is not "office"); hyphens and
   spaces fold ("ultra-processed" = "ultra processed" = "ultraprocessed", "anti-semitism" = "antisemitism"). */
const Q_HY = /[-‐-―]/g;
let QKEY = null, QTOK = [];
function qTokens(q){
  if (QKEY === q) return QTOK; QKEY = q;
  QTOK = String(q || '').split(/\s+/).filter(Boolean).map(w => {
    const parts = w.split(/[-‐-―]+/).filter(Boolean), rx = t => new RegExp('(^|[^a-z0-9])' + reEsc(t) + (t.length <= 3 ? '(?![a-z0-9])' : ''));
    if (!parts.length) return [];
    return parts.length > 1 ? [[rx(parts.join(' ')), 'a'], [rx(parts.join('')), 'b']] : [[rx(parts[0]), 'a'], [rx(parts[0]), 'b']];
  }).filter(t => t.length);
  return QTOK;
}
function qNorm(cache, key, s){ let c = cache.get(key); if (!c || c.s !== s){ c = { s, a: s.replace(Q_HY, ' '), b: s }; if (Q_HY.test(s)) { Q_HY.lastIndex = 0; c.b = s.replace(Q_HY, ''); } Q_HY.lastIndex = 0; cache.set(key, c); } return c; }
const QC_S = new Map(), QC_F = new Map();
function qFind(t, c){ for (const [rx, w] of t){ const m = rx.exec(w === 'a' ? c.a : c.b); if (m) return { at: m.index + m[1].length, len: m[0].length - m[1].length, w }; } return null; }
function qHit(r){
  const toks = qTokens(S.q); if (!toks.length) return true;
  const cs = qNorm(QC_S, r.id, r._s || ''), f = FT.get(r.id), cf = f ? qNorm(QC_F, r.id, f) : null;
  return toks.every(t => qFind(t, cs) || (cf && qFind(t, cf))) || qJoined(cs, cf);
}
/* "ultra processed" also finds "ultraprocessed" / "ultra-processed": a two-word query may be one word written without the gap */
function qJoined(cs, cf){ if (QTOK.length !== 2 || QKEY.split(/\s+/).length !== 2) return false; const rx = new RegExp('(^|[^a-z0-9])' + reEsc(QKEY.replace(/\s+/g, ''))); return rx.test(cs.b) || !!(cf && rx.test(cf.b)); }
function qHitMeta(r){ const toks = qTokens(S.q), cs = qNorm(QC_S, r.id, r._s || ''); return toks.every(t => qFind(t, cs)); }
/* does a plain string (not a row) hold every word? used for the release lines in Clips */
function qHitStr(s){ const toks = qTokens(S.q); if (!toks.length) return true; const c = { a: String(s || '').replace(Q_HY, ' '), b: String(s || '').replace(Q_HY, '') }; return toks.every(t => qFind(t, c)); }
function match(r, skip){
  if (S.q){
    if (NICKS.has(S.q.trim())){ const q = S.q.trim(), rx = new RegExp('(^|[^a-z0-9])' + reEsc(q) + '($|[^a-z0-9])');
      if (!(r._nick || []).includes(q) && !rx.test(r._s) && !rx.test(FT.get(r.id) || '')) return false; }
    else if (!qHit(r)) return false;
  }
  for (const f of FACETS){ if (f.key === skip) continue; const s = S.sel[f.key]; if (s.size && !vals(r, f.key).some(v => s.has(v))) return false; }
  if (S.d0 && r.date < S.d0) return false;
  if (S.d1 && r.date > S.d1) return false;
  if (S.flag && FLAGS[S.flag] && !FLAGS[S.flag].f(r)) return false;
  if (S.ranin && !ranInName(r, S.ranin)) return false;
  if (skip !== 'saved'){ if (S.saved === 'yes' && !hasHtml(r.id)) return false; if (S.saved === 'no' && hasHtml(r.id)) return false; }
  return true;
}
const filtered = () => D.filter(r => match(r));
/* INCL-v1 (DECISIONS 2026-10-28 inclusion): List-only stories are kept and shown (badged) but every headline count leaves them out
   unless S.lo ("Include list-only mentions"); a blank depth counts (no text is not list-only) */
const countable = r => S.lo || r.depth !== 'List-only';
let DCOUNT = null;
function dCount(){ const k = (S.lo ? 1 : 0) + '|' + D.length; if (!DCOUNT || DCOUNT.k !== k) DCOUNT = { k, v: S.lo ? D : D.filter(countable) }; return DCOUNT.v; }
const nListOnly = () => D.reduce((n, r) => n + (r.depth === 'List-only'), 0);
function loToggle(){ const n = nListOnly(); return n ? `<details class="facet" data-facet="lo" ${S.openFacets.has('lo')?'open':''}><summary>List-only mentions<small>${S.lo?'1 on':''}</small></summary><div class="body"><div class="hint">Stories that name him only inside a list (roster, co-authors, endorsers). Left out of counts unless included.</div><label class="opt"><input type="checkbox" data-lo ${S.lo ? 'checked' : ''}><span class="lab">Include list-only mentions</span><span class="n">${fmt(n)}</span></label></div></details>` : ''; }   /* LOFACET-v1 (Sammy 2026-10-29): styled as a facet */
const anyFilter = () => S.q || S.d0 || S.d1 || S.saved!=='all' || S.flag || S.ranin || FACETS.some(f=>S.sel[f.key].size);

function dateLabel(r, short){
  if (!r.date) return 'Undated';   /* DATES-v1 (D3): a story with no date of its own is shown as Undated, never with a scrape / save date */
  const [y,m,d] = r.date.split('-');
  if (r.prec==='year') return y;
  if (r.prec==='month') return `${MONTHS[+m-1]} ${y}`;
  return short ? `${MONTHS[+m-1]} ${+d}` : `${MONTHS[+m-1]} ${+d}, ${y}`;
}
function alsoNames(r){
  if (Array.isArray(r.reps) && !r._alsoEdit) return repNames(r);
  const seen = new Set(), own = nrmName(r.pub);
  return (r.also||'').split(';').map(x=>x.trim()).filter(x => {
    if (!x || /not (found|identified)/.test(x)) return false;
    if (/separate ProQuest record/i.test(x) && nrmName(x).startsWith(own)) return false;
    const k = nrmName(x.replace(/\s*\(.*\)\s*$/,'')); if (seen.has(k)) return false; seen.add(k); return true;
  });
}
function nrmName(s){ return String(s||'').toLowerCase().replace(/^the\s+/,'').replace(/[^a-z0-9]+/g,''); }
function alsoMissing(r){ if (Array.isArray(r.reps) && !r._alsoEdit) return 0; const m = (r.also||'').match(/(\d+) (?:others? )?not (?:found|identified)/); return m ? +m[1] : 0; }
function alsoShort(r, n){ const a = alsoNames(r); if (!a.length) return ''; return 'Reprinted in ' + a.slice(0,n).join(', ') + (a.length>n ? ` and ${a.length-n} more` : ''); }
function badges(r, link, norel){   /* norel: entity page asks for no press-release badge (release pages: the row's evidence tag says it; rp-final) */
  // in the story panel (link) each badge is a button that opens Clips filtered to it
  const B = (cls, k, v, body, title) => link ? `<button type="button" class="badge ${cls}" data-fk="${k}" data-fv="${esc(v)}" title="See every clip like this${title ? ': '+esc(title) : ''}">${body}</button>` : `<span class="badge ${cls}"${title ? ` title="${esc(title)}"` : ''}>${body}</span>`;
  let b = '';
  if (r.role!=='Mentioned in story') b += B('named', 'role', r.role, esc(r.role));
  if (r.depth === 'List-only') b += B('listonly', 'depth', 'List-only', 'List only', 'Named only inside a list (roster, co-authors, endorsers); not in headline counts unless “Include list-only mentions” is on');   /* INCL-v1 */
  if (link && r.depth && r.depth !== 'List-only') b += B('named', 'depth', r.depth, `Depth: ${esc(r.depth)}`, 'How much of the story is about him');   /* REVIEW4-PAGE-v1 E4 */
  if (r.av && r.av.type !== 'Web story'){ const f = fmtOf(r); if (f && f !== 'Article') b += B('lang', 'fmt', f, esc(f), 'Spoken or video item, not a text page');   /* REVIEW4-PAGE-v1 D3: audio / video badge */
    if (avRole(r)) b += B('lang', 'avrole', avRole(r), `On air: ${esc(avRole(r))}`, 'His role in this audio or video item'); }
  if (r.quoted === 'Yes') b += B('lang', 'quoted', 'Yes', 'Quoted', 'Gabriel is directly quoted: his own words in quotation marks, or his spoken words in a transcript');   /* QUOTED-v1: same look as the Language / Tone tags */
  if (r.lang) b += B('lang', 'flag', 'foreign', esc(r.lang), r.hl_en ? 'English headline shown under the original' : 'Not translated yet');
  if (hasHtml(r.id)) b += B('saved', 'saved', 'yes', 'Saved copy');
  if (NOTES.has(r.id)) b += B('', 'flag', 'notes', 'Note', 'This story has a team note');
  if (rated(r)) b += B('tone', 'tone', r.tone, `<i style="background:${colorFor('tone',r.tone)}"></i>${esc(r.tone)}`, 'Tone toward Gabriel');
  if (!norel) { const a = relsOf(r.id), fr = a.filter(x => relIndex().from(x.type)), g = fr.length ? fr : a;   /* RELCLIPS-v1 (was RELEASES-v2 copies only): every release relation, From vs Related as the panel line; Related only where badges link (story panel, Clips table), not Home/tab lists */
    if (fr.length || (a.length && link)) { const tt = (fr.length ? 'The story uses the release’s words or quotes it. ' : 'Same bill or subject as a release, but not its words. ') + g.map(x => (relIndex().ev(x.type) || 'Related') + ': ' + x.rel.title).join(' · '), lab = fr.length ? 'From press release' : 'Related press release', top = g[0] && g[0].rel;
      /* RELBADGE-v1 (Sammy 7d84c4a4): where the badge links it opens the strongest release's page on the Press releases tab, no Clips filter */
      b += link && top && top.sub ? `<button type="button" class="badge rel" data-tb-go="releases" data-tb-sub="${esc(top.sub)}" title="Open the press release page: ${esc(tt)}">${lab}</button>` : B('rel', 'flag', fr.length ? 'relfrom' : 'relrel', lab, tt); } }
  return b;
}
/* a story-panel fact that opens Clips filtered to it */
const fl = (k, v, label, title) => v ? `<button class="linkbtn" data-fk="${k}" data-fv="${esc(v)}" title="${esc(title ? title + ' ' : '')}See every clip like this">${esc(label || v)}</button>` : esc(label || '');
const PUBS = new Set(D.map(r => r.pub).filter(Boolean));

