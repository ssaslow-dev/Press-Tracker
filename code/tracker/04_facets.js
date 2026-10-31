/* ---------- facets ---------- */
/* BLANKFACET-v1 (Sammy comment 4660aa70: the Format filter showed an empty option): a blank value is labelled "Not recorded"
   and listed last in every facet (its checkbox value stays blank, so it still filters to exactly those stories) */
const NR_BLANK = v => v == null || v === '';
const NR_LABEL = v => NR_BLANK(v) ? 'Not recorded' : v;
/* AVSHOW-v1: Channel and Show facets for audio/video stories, after Format */
(function avFacets(){ if (FACETS.some(f => f.key === 'channel')) return; const i = FACETS.findIndex(f => f.key === 'fmt') + 1 || FACETS.length;
  FACETS.splice(i, 0, {key:'channel', label:'Channel', search:true, limit:8, hint:'Audio and video stories: the station, network or publisher that carried them.'},
    {key:'show', label:'Show', search:true, limit:8, hint:'Audio and video stories: the program, where one is named.'},
    {key:'avrole', label:'His role on air', hint:'Audio and video stories only: guest, interviewee, soundbite, brief mention and so on, as logged on the Audio & video tab. Use it to find every time he was a guest.'});
  S.sel.channel = S.sel.channel || new Set(); S.sel.show = S.sel.show || new Set(); S.sel.avrole = S.sel.avrole || new Set(); })();
function facetCounts(key){ const c = new Map(); D.forEach(r => { if (match(r, key)) vals(r, key).forEach(v => c.set(v, (c.get(v)||0)+1)); }); return c; }
function renderFacets(){
  let html = '';
  for (const f of FACETS){
    const c = facetCounts(f.key), sel = S.sel[f.key];
    let vals = valuesOf(f.key).map(v => v == null ? '' : v).filter((v, i, a) => a.indexOf(v) === i), extra = '', more = '', stf = [];
    if (c.has(undefined) || c.has(null)){ c.set('', (c.get('') || 0) + (c.get(undefined) || 0) + (c.get(null) || 0)); if (!vals.includes('')) vals.push(''); }
    if (f.key === 'author'){ stf = vals.filter(isStaffAuthor); vals = vals.filter(v => !isStaffAuthor(v)); }
    if (f.search){
      const q = (S.fq[f.key]||'').toLowerCase(), all = valuesOf(f.key).filter(v => f.key !== 'author' || !isStaffAuthor(v)).length, noun = f.key==='pub' ? 'outlets' : f.key==='bills' ? 'bills' : f.key==='county' ? 'counties' : f.key==='channel' ? 'channels' : f.key==='show' ? 'shows' : f.key==='state' ? 'states' : f.key==='author' ? 'reporters' : String(f.label||'').toLowerCase();   /* FNOUN-v1 (Sammy 2026-10-29): State search box said "reporters" */
      if (q) vals = vals.filter(v => (v + ' ' + v.replace(' ','') + ' ' + (f.key==='bills' ? billName(v) : '')).toLowerCase().includes(q));
      vals.sort((a,b) => (c.get(b)||0)-(c.get(a)||0));
      const shown = (S.fall[f.key] || q) ? vals : vals.slice(0, f.limit);
      vals = [...sel].filter(v => !shown.includes(v) && !(f.key === 'author' && isStaffAuthor(v))).concat(shown);
      if (all > f.limit) extra = `<input class="fsearch" data-fq="${f.key}" type="search" placeholder="Find one of ${fmt(all)} ${noun}" aria-label="Find ${noun}" value="${esc(S.fq[f.key]||'')}">`;
      if (!q && all > f.limit) more = `<button class="linkbtn" data-fmore="${f.key}">${S.fall[f.key]?'Show fewer':'Show all '+fmt(all)}</button>`;
    }
    vals = vals.filter(v => !NR_BLANK(v)).concat(vals.filter(NR_BLANK));   /* BLANKFACET-v1: "Not recorded" last */
    html += `<details class="facet" data-facet="${f.key}" ${S.openFacets.has(f.key)?'open':''}><summary>${f.label}<small>${sel.size? sel.size+' on':''}</small></summary><div class="body">${f.hint?`<div class="hint">${f.hint}</div>`:''}${extra}${vals.map(v=>opt(f,v,c)).join('')}${more}${f.key === 'author' ? staffGroup(f, stf, c, sel) : ''}</div></details>`;
  }
  html += loToggle();   /* INCL-v1 */
  html += `<details class="facet" data-facet="saved" ${S.openFacets.has('saved')?'open':''}><summary>Saved copy<small>${S.saved!=='all'?'1 on':''}</small></summary><div class="body"><div class="seg" role="group" aria-label="Saved copy">${[['all','Any'],['yes','Saved'],['no','Not yet']].map(([k,l])=>`<button data-saved="${k}" aria-pressed="${S.saved===k}">${l}</button>`).join('')}</div></div></details>`;
  html += `<details class="facet" data-facet="relf" ${S.openFacets.has('relf')?'open':''}><summary>Press release<small>${REL_FLAG[S.flag]?'1 on':''}</small></summary><div class="body"><div class="hint">How the story relates to his official releases. Ran release text: a copy, near copy, or it uses or quotes the release. Related: same bill or subject around the release date. Exact copies are mostly kept out of the story list; those releases are listed above the results.</div><div class="seg" role="group" aria-label="Press release">${REL_FILTERS.map(([k,l])=>`<button data-relf="${k}" aria-pressed="${(REL_FLAG[S.flag]?S.flag:'')===k}">${l}</button>`).join('')}</div></div></details>`;   /* RELRULE-v1; RELCLIPS-v1 */
  $('#facets').innerHTML = html;
}
function opt(f, v, c){
  const n = c.get(v)||0, on = S.sel[f.key].has(v);
  const sw = f.sw ? `<span class="sw" style="background:${colorFor(f.key,v)}"></span>` : '';
  return `<label class="opt ${n||on?'':'zero'}"><input type="checkbox" data-f="${f.key}" value="${esc(v)}" ${on?'checked':''}>${sw}<span class="lab" title="${esc(f.key==='bills' && billName(v) ? v+': '+billName(v) : NR_LABEL(v))}">${esc(NR_LABEL(v))}${f.key==='bills' && billName(v) ? `<small class="bname"> ${esc(billName(v))}</small>` : ''}</span><span class="n">${fmt(n)}</span></label>`;
}
function renderChips(rows){
  const chips = [];
  if (S.q) chips.push(['q','', 'Search', `“${S.q}” (all words, any order)${FTIDX ? '' : ' (still indexing saved pages: the list may be incomplete)'}`]);
  if (S.when==='custom') chips.push(['when','', 'Dates', S.whenLabel]);
  const T5 = TONE_ORDER.slice(0,5);
  for (const f of FACETS){ const sel = S.sel[f.key];
    if (f.key==='tone' && T5.every(t=>sel.has(t))){ chips.push(['tone','__rated','Tone','Any rating']); [...sel].filter(v=>!T5.includes(v)).forEach(v=>chips.push(['tone',v,'Tone',v])); continue; }
    for (const v of sel) chips.push([f.key, v, f.label, NR_LABEL(v)]); }
  if (S.saved !== 'all') chips.push(['saved','', 'Saved copy', S.saved==='yes'?'Saved':'Not yet']);
  if (S.flag) chips.push(['flag','', FLAGS[S.flag].chip || 'Check', FLAGS[S.flag].label]);
  if (S.ranin) chips.push(['ranin','', 'Ran in', S.ranin]);
  const nf = FACETS.reduce((a,f)=>a+S.sel[f.key].size,0) + (S.saved!=='all') + !!S.flag + !!S.ranin;
  $('#openRail').innerHTML = 'Filters' + (nf ? ` <span class="fcount">${nf}</span>` : '');
  $('#clearTop').style.display = nf ? '' : 'none';  // Clear all next to Filters while any filter is on
  $('#chips').innerHTML = `<span class="result-line"><b style="color:var(--ink)">${fmt(rows.length)}</b> of ${fmt(D.length)} stories</span>` + chips.map(([k,v,l,t]) => `<span class="chip"><span class="k">${esc(l)}</span><span>${esc(t)}</span><button aria-label="Remove ${esc(l)} filter" data-rm="${esc(k)}" data-v="${esc(v)}">${IC.xs}</button></span>`).join('') + relHits();   /* RELRULE-v1 */
}

