/* ---------- overview ---------- */
function topStory(rows){ return rows.slice().sort((a,b) => (b.role!=='Mentioned in story') - (a.role!=='Mentioned in story') || b.pick - a.pick || b.date.localeCompare(a.date))[0]; }
/* last visit: "new since" keeps the visit before today's, so reopening the page later the same day still shows the same news */
const VISIT = (() => { let v = {}; try { v = JSON.parse(localStorage.getItem('jg2-visit')||'{}') || {}; } catch(e){}
  if (v.cur !== TODAY){ v = { prev: v.cur || '', cur: TODAY }; try { localStorage.setItem('jg2-visit', JSON.stringify(v)); } catch(e){} }
  return v; })();
const NEG = r => r.tone==='Negative' || r.tone==='Very negative';
function toneMix(el, capEl, rows, scope, o){ o = o || {};  /* REORG-v1: o.bars / o.watch === false drop the bars / the negative list */
  const tr = rows.filter(rated), tc = new Map(); tr.forEach(r=>tc.set(r.tone,(tc.get(r.tone)||0)+1));
  const T5 = TONE_ORDER.slice(0,5), pos = (tc.get('Very positive')||0)+(tc.get('Positive')||0), neg = (tc.get('Negative')||0)+(tc.get('Very negative')||0);
  if (capEl) capEl.textContent = tr.length ? `${Math.round(pos/tr.length*100)}% positive and ${Math.round(neg/tr.length*100)}% negative, from ${pl(tr.length,'rated story','rated stories')}${scope||''}. Stories are rated from their saved copies.` : `No rated stories${scope||''} yet. Stories are rated from their saved copies.`;
  const watch = tr.filter(NEG).sort((a,b)=>b.date.localeCompare(a.date)).slice(0,3);
  const mx = Math.max(1, ...T5.map(k => tc.get(k)||0));
  el.innerHTML = `<div class="tm-grid"><div class="tm-a">` + (tr.length ? `<div class="mix">${T5.map(k=>tc.get(k)?`<span style="flex:${tc.get(k)};background:${colorFor('tone',k)}" title="${k}: ${tc.get(k)}"></span>`:'').join('')}</div><div class="tone-scale"><span>Positive</span><span>Negative</span></div>` : '')
    + `<div class="hbars">${T5.map(k=>`<button class="hb" data-k="tone" data-v="${k}"><span class="hb-l"><span class="sw" style="background:${colorFor('tone',k)};margin-right:6px"></span>${k}</span><span class="hb-track">${tc.get(k) ? `<span class="hb-fill" style="width:${tc.get(k)/mx*100}%;background:${colorFor('tone',k)}"></span>` : ''}</span><span class="hb-v">${fmt(tc.get(k)||0)}${tr.length?' · '+Math.round((tc.get(k)||0)/tr.length*100)+'%':''}</span></button>`).join('')}</div></div>`
    + (tr.length ? `<div class="watch"><h3>Latest negative coverage</h3>${watch.length ? `<div class="clip-list">${watch.map(r=>clipItem(r, r.twhy ? esc(r.twhy) : '')).join('')}</div>` : '<div class="note">None among the rated stories.</div>'}</div>` : '') + `</div>`;
  if (o.bars === false){ const x = el.querySelector('.tm-a .hbars'); if (x) x.remove(); }
  if (o.watch === false){ const x = el.querySelector('.watch'); if (x) x.remove(); }
  return { rated: tr.length, pos, neg };
}
function renderToday(){
  const DC = dCount();   /* INCL-v1: headline counts leave List-only out unless S.lo */
  const ly = +LAST.slice(0,4), cut = LAST.slice(5);
  const n30 = DC.filter(r => r.prec==='day' && r.date > addDays(TODAY,-30)).length;
  const p30 = DC.filter(r => r.prec==='day' && r.date > addDays(TODAY,-60) && r.date <= addDays(TODAY,-30)).length;
  const ytd = DC.filter(r => r.year===ly && (r.prec==='year' || r.date.slice(5) <= cut)).length;
  const prev = DC.filter(r => r.year===ly-1 && r.prec!=='year' && r.date.slice(5) <= cut).length;
  const namedY = DC.filter(r => r.year===ly && r.role!=='Mentioned in story').length;
  const y12 = DC.filter(r => r.prec==='day' && r.date > addDays(TODAY,-365)), top12 = y12.filter(r => hasReach(r,'National') || hasReach(r,'Statewide California')).length;
  const delta = (a,b) => b && b < 5 ? `<span class="${a>=b?'up':'down'}">${a>=b?'▲':'▼'} ${a>=b?'+':'−'}${Math.abs(a-b)}</span>` : b ? `<span class="${a>=b?'up':'down'}">${a>=b?'▲':'▼'} ${Math.abs(Math.round((a-b)/b*100))}%</span>` : '';
  const [cm, cd] = cut.split('-');
  const h = new Date().getHours();
  $('#hello').textContent = h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
  $('#helloCap').textContent = `${new Date().toLocaleDateString('en-US',{weekday:'long', month:'long', day:'numeric'})}. The log has ${fmt(D.length)} stories${nListOnly() ? (S.lo ? ` (${fmt(nListOnly())} of them list-only, counted)` : ` (${fmt(D.length - nListOnly())} counted + ${fmt(nListOnly())} list-only)`) : ''}, newest from ${dateLabel(byId.get(D.find(r=>r.date===LAST).id))}.`;
  $('#tiles').innerHTML = [
    ['30', 'Last 30 days', fmt(n30), `${delta(n30,p30)} vs. ${fmt(p30)} the 30 days before`],
    ['ytd', `${ly} so far`, fmt(ytd), prev ? `${delta(ytd,prev)} vs. ${fmt(prev)} by ${MONTHS[+cm-1]} ${+cd}, ${ly-1}` : ''],
    ['named', `Headlines in ${ly}`, fmt(namedY), 'Stories that name him in the headline, plus his op-eds'],
    ['major', 'Major outlets, 12 months', y12.length ? Math.round(top12/y12.length*100)+'%' : '–', `${fmt(top12)} of ${fmt(y12.length)} stories ran in national or statewide outlets`],
  ].map(([k,s,b,sm]) => `<button class="card tile" data-tile="${k}" title="See these clips"><span class="eyebrow">${s}</span><b>${b}</b><small>${sm}</small></button>`).join('');

  reorgHomeLine(n30, p30);  /* REORG-v1: no 'new since your last visit' / weekly items on Home; one 30-day line instead */

  // needs attention
  const A = [];
  // strongly toned coverage from the last 30 days gets its own line, newest story shown
  const toned = [[['Very negative','Negative'],'bad','negative'],[['Very positive'],'ok','very positive']].map(([t,c,l]) => [t, c, l, DC.filter(r => r.prec==='day' && r.date > addDays(TODAY,-30) && t.includes(r.tone)).sort((a,b) => b.date.localeCompare(a.date))]);  /* REORG-v1: one negative list on Home */
  if (U.found.length) A.push(['bad', `${pl(U.found.length,'new story','new stories')} found by Update database that Claude couldn’t confirm`, 'Waiting for you to check and add them.', 'Review', 'data-mgopen="upd"']);
  toned.forEach(([t, c, l, rs]) => { if (rs.length) A.push([c, `${pl(rs.length, l + ' story', l + ' stories')} in the last 30 days`, '', '', '', `<div class="clip-list attn-list">${rs.map(r => c === 'bad' ? reorgAttnItem(r) : clipItem(r)).join("")}</div>`]); });  /* REORG-v1 */
  const age = Math.round((new Date(TODAY) - new Date(LAST)) / 864e5);
  /* HOMEUPKEEP-v1: finds to review, an out-of-date log and pages waiting for tone or authors are in Manage */
  const notes = [...NOTES.keys()].filter(id => byId.has(id)).length;
  if (notes) A.push(['info', `${pl(notes,'story has','stories have')} a team note`, 'Notes the team left on stories.', 'See them', 'data-tile="notes"']);
  if (!A.some(a => a[0]==='bad' || a[0]==='warn')) A.unshift(['ok', 'Nothing urgent', 'No negative coverage among rated stories in the last 30 days.', '', '']);  /* HOMEUPKEEP-v1 */
  $('#attn').innerHTML = A.map(([c,t,d,b,attr,list]) => `<div class="attn-i"><i class="${c}"></i><div><b>${t}</b>${d ? `<span>${d}</span>` : ''}${list || ''}</div>${b ? `<button class="btn" ${attr}>${b}</button>` : '<span></span>'}</div>`).join('');

  // tone, last 90 days (falls back to all rated stories when none of the last 90 days are rated)
  const r90 = DC.filter(r => r.prec==='day' && r.date > addDays(TODAY,-90));
  if (r90.some(rated)) toneMix($('#toneMix'), $('#toneCap'), r90, ' in the last 90 days', { bars: false, watch: false });  /* REORG-v1 */
  else toneMix($('#toneMix'), $('#toneCap'), DC, ', all dates (none from the last 90 days are rated yet)', { bars: false, watch: false });
}
/* report blocks that used to live on the overview, now drawn from the report's rows */
function renderMoments(rows){
  const byMonth = new Map(); rows.forEach(r => { if (r.prec==='year') return; const k = r.date.slice(0,7); (byMonth.get(k) || byMonth.set(k, []).get(k)).push(r); });
  const moments = [...byMonth.entries()].sort((a,b)=>b[1].length-a[1].length).slice(0,5);
  $('#moments').innerHTML = moments.length ? moments.map(([k, rs]) => {
    const tc = new Map(); rs.forEach(r=>tc.set(r.topic,(tc.get(r.topic)||0)+1));
    const [lead, ln] = [...tc.entries()].sort((a,b)=>b[1]-a[1])[0];
    const t = topStory(rs.filter(r=>r.topic===lead));
    return `<button class="moment" data-month="${k}"><span class="when">${MONTHS[+k.slice(5)-1]} ${k.slice(0,4)}<small>${esc(lead.replace(/\s*\(.*\)/,''))}</small></span>
      <span><span class="mh">${esc(t.hl)}</span><span class="mi"><span class="sw" style="background:${colorFor('topic',lead)}"></span>${esc(lead)}: ${ln} of ${rs.length} stories · lead story from ${esc(t.pub)}</span></span>
      <span class="n">${rs.length}<small>stories</small></span></button>`;
  }).join('') : '<div class="note">No stories in this period.</div>';
}
function renderBillList(rows){
  S._billRows = rows;
  const bills = billGroups(rows);  /* REORG-v1: split by session */
  const bl = [...bills.entries()].sort((a,b)=>b[1].length-a[1].length), cut = S.billsAll ? bl.length : 10;
  $('#bills').innerHTML = bills.size ? bl.slice(0, cut).map(([b, rs]) => {
    const [bn, bs] = b.split('|'), name = bs ? billSesName(bn, bs) : billName(b);  /* REORG-v1 */
    const mc = new Map(); rs.forEach(r => { if (r.prec!=='year'){ const k = r.date.slice(0,7); mc.set(k,(mc.get(k)||0)+1); } });
    const peak = [...mc.entries()].sort((a,b)=>b[1]-a[1])[0];
    const last = rs.reduce((a,r)=> r.date>a.date ? r : a);
    return `<button class="billrow" data-bill="${esc(bn)}"${bs ? ` data-bses="${esc(bs)}"` : ''}><b>${bn}${bs ? ` <small>${rgSesShort(bs)}</small>` : ''}</b><span class="bt">${esc(name)}<small>${peak ? `Peak ${MONTHS[+peak[0].slice(5)-1]} ${peak[0].slice(0,4)} · ` : ''}latest ${dateLabel(last)}</small></span><span class="bn">${rs.length}</span></button>`;
  }).join('') + (bl.length > 10 ? `<button class="linkbtn billmore" data-billmore>${S.billsAll ? 'Show the top 10' : `Show all ${bl.length} bills`}</button>` : '') : '<div class="note">None of his bills drew coverage in this period.</div>';
}
document.addEventListener('click', e => { if (!e.target.closest('[data-billmore]')) return; S.billsAll = !S.billsAll; renderBillList(S._billRows || filtered().filter(countable)); });
function renderReprint(rows){
  const top = rows.filter(r => r.pick).sort((a,b)=>b.pick-a.pick || b.date.localeCompare(a.date)).slice(0,5);
  $('#reprint').innerHTML = top.length ? top.map(r => clipItem(r, esc(alsoShort(r,4)))).join('') : '<div class="note">No reprints found for stories in this period.</div>';
}
/* LINKS-v1 (agent-links): every listed link is drawn like the ProQuest one: <a><b>Label ↗</b><span>detail</span></a>.
   Listed: NewsBank / ProQuest through the CA State Library, and the publisher's own link (build_data: r.lk / rep.lk as
   [kind, url]). Records without lk (finds from the Update button, live reprints) get the same kinds from link/plink/pq. */
const LINK_KIND = { pub: ['Publisher site', ''], nb: ['NewsBank via CA State Library', 'library card login'],
  nbpa: ['NewsBank print edition via CA State Library', 'library card login'],  /* LINKUI-v1: no NewsBank print-page (nbpg) links */
  pq: ['ProQuest via CA State Library', 'library card login'], tv: ['Internet Archive (TV clip)', 'archive.org'] };  /* LINKS-v2 */
const CSL_PQ = 'https://castatelib.idm.oclc.org/login?url=', CSL_NB = 'https://infoweb-newsbank-com.castatelib.idm.oclc.org/';
/* PRINTLINK-v1 (Sammy thread 131f0b47, "apply throughout"): the NewsBank print-edition link (nbpa) is listed only when the item
   has no regular-edition link (a NewsBank article link nb or the publisher's own link pub) */
const printLinkRule = ls => ls.some(p => p[0] === 'nb' || p[0] === 'pub') ? ls.filter(p => p[0] !== 'nbpa') : ls;
function linksOf(x){
  if (!x) return [];
  if (Array.isArray(x.lk)) return printLinkRule(x.lk.filter(p => Array.isArray(p) && LINK_KIND[p[0]] && /^https?:\/\//i.test(p[1] || '')));
  const out = [], seen = new Set(), add = (k, u) => { if (u && !seen.has(u)) { seen.add(u); out.push([k, u]); } };
  [x.plink, x.link, x.pq].forEach(u => { u = String(u || '').trim(); if (!/^https?:\/\//i.test(u)) return;
    if (/^https?:\/\/castatelib\.idm\.oclc\.org\/login\?url=https?:\/\/(www\.)?proquest\.com\//i.test(u)) add('pq', u);
    else if (/^https?:\/\/(www\.)?proquest\.com\//i.test(u)) add('pq', CSL_PQ + u);
    else if (/[?&]docref=image(\/|%2F)/i.test(u)) {}  /* LINKUI-v1: a NewsBank print page is not listed */
    else if (/^https?:\/\/infoweb-newsbank-com\.castatelib\.idm\.oclc\.org\//i.test(u)) add('nb', u);
    else if (/^https?:\/\/infoweb\.newsbank\.com\//i.test(u)) add('nb', u.replace(/^https?:\/\/infoweb\.newsbank\.com\//i, CSL_NB));
    else if (/^https?:\/\/(www\.)?archive\.org\/(details|embed)\/[A-Za-z0-9-]+_\d{8}_\d{6}/i.test(u)) add('tv', u);  /* LINKS-v2 */
    else if (!/^https?:\/\/([^\/]*\.)?(archive\.org|google\.[a-z.]+|oclc\.org|newsbank\.com)(\/|$)/i.test(u)) add('pub', u); });
  return printLinkRule(out);
}
function linkA(p){ let [label, sub] = LINK_KIND[p[0]]; if (p[0] === 'pub' && /^https?:\/\/([^\/]*\.)?podcastrex\.com\//i.test(p[1])) label = 'Transcript copy (third party)';   /* REVIEW4-PAGE-v1 E12 */
  const h = (() => { try { return new URL(p[1]).hostname.replace(/^www\./,''); } catch(e){ return ''; } })();
  return `<span class="lkw">${cpBtn(p[1])}<a href="${esc(p[1])}" target="_blank" rel="noopener" data-lk="${p[0]}"><b>${label} ↗</b><span>${esc(sub || h)}</span></a></span>`; }

/* LINKUI-v1: a copy-link icon button to the LEFT of every link's text (one delegated handler below) */
const CP_ICON = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><rect x="5.5" y="5.5" width="8" height="8" rx="1.6" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M10.5 3.5v-.4A1.6 1.6 0 0 0 8.9 1.5H4.1A1.6 1.6 0 0 0 2.5 3.1v4.8a1.6 1.6 0 0 0 1.6 1.6h.4" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>';
const CP_OK = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><path d="M3 8.5l3.2 3L13 4.5" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const cpBtn = u => u ? `<button type="button" class="cpb" data-cp="${esc(u)}" title="Copy link" aria-label="Copy link">${CP_ICON}</button>` : '';
try { document.head.insertAdjacentHTML('beforeend', `<style id="linkui-css">
.cpb{border:0;background:none;color:var(--ink-3);padding:0;width:22px;height:22px;display:inline-grid;place-items:center;border-radius:5px;flex:none;cursor:pointer;vertical-align:middle;position:relative;margin-right:2px}
.cpb:hover{color:var(--accent);background:var(--panel-2)} .cpb:focus-visible{outline:2px solid var(--focus);outline-offset:1px}
.cpb.ok{color:var(--good)} .cpb svg{display:block}
.lkw{display:inline-flex;align-items:center;gap:2px;min-width:0}
.dlinks .lkw a{align-items:baseline}
.upd-item .h .cpb{margin:-2px 4px 0 -2px}
@media (pointer:coarse){.cpb::after{content:"";position:absolute;inset:-11px -3px -11px -11px}}
</style>`); } catch(e){}
document.addEventListener('click', e => { const b = e.target.closest('button[data-cp]'); if (!b) return;
  e.preventDefault(); e.stopPropagation();
  let u = b.dataset.cp; try { u = new URL(u, location.href).href; } catch(x){}
  copy(u, 'Copied the link');
  b.innerHTML = CP_OK; b.classList.add('ok'); clearTimeout(b._cpT);
  b._cpT = setTimeout(() => { b.innerHTML = CP_ICON; b.classList.remove('ok'); }, 1500); }, true);
/* /LINKUI-v1 */
function repLinks(r){ return '';  /* F7-v1: no links to reprints anywhere (Sammy 2026-10-27); links stay on the Original. The call in the story panel stays (LINKS-v1 owns it) and renders nothing. */
  const rows = (Array.isArray(r.reps) ? r.reps : []).map(p => [p, linksOf(p)]).filter(x => x[1].length);
  if (!rows.length) return '';
  return `<details class="also replinks"${rows.length <= 5 ? ' open' : ''}><summary style="cursor:pointer"><b class="t-strong">Reprint links</b> (${fmt(rows.length)})</summary>${rows.map(([p, ls]) => `<div class="dlinks" style="margin:6px 0 0"><span>${esc(p.outlet || '')}${p.date ? ' · ' + esc(p.date) : ''}</span>${ls.map(linkA).join('')}</div>`).join('')}</details>`;
}
/* /LINKS-v1 */
function storyUrl(r){ const l = linksOf(r)[0]; return l ? l[1] : ''; }  // LINKS-v1
function storyLink(r, cls){ const u = storyUrl(r), pq = r.lstat==='Search link only'; if (!u) return `<span class="story ${cls||''}">${esc(r.hl)}</span>`; return `<a class="story ${cls||''}" href="${esc(u)}" target="_blank" rel="noopener" title="${pq ? 'Open in ProQuest through the California State Library' : 'Open the article at '+esc(r.pub)}">${esc(r.hl)}<span class="ext" aria-hidden="true">↗</span></a>`; }
function clipItem(r, extra){
  return `<div class="clip" data-id="${r.id}" tabindex="0" role="button" aria-label="Story details: ${esc(r.hl)}"><span class="ct">${esc(r.hl)}</span>${r.hl_en ? `<span class="hl-en">${esc(r.hl_en)}</span>` : ''}<span class="cm">${dateLabel(r)} · ${esc(r.pub)}${r.authors.length?` · by ${r.authors.map(a => `<button type="button" class="tlink" data-author="${esc(a)}" title="Filter to stories by ${esc(a)}">${esc(a)}</button>`).join(', ')}`:''}${extra?` · ${extra}`:''} ${badges(r)}</span></div>`;
}

