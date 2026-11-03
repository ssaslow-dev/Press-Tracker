/* ---------- TABS-v1 (agent-tabs, 2026-10-27): the Press desk tools become main tabs ----------
   Menu: Home · Clips · Data · Reporters · Outlets · Press releases · Bills · Story travel (Press desk goes away; old
   #insights / #press-desk / view-id links redirect). Each tab is a module (build/tabs/<id>.js, contract build/tabs_contract.md)
   that calls AJGTabs.register({...}); the framework draws it with two shared components:
   - the search tab (search box, filter rail with counts, chips, sortable list, show more, export, URL state, phone drawer);
   - the entity page (#<tab>/<slug>: header block + a Clips-style list of that entity's stories with its own search,
     filters, sort, pager, export and the story panel; back link to the list).
   Installed by code/patch_tabs.py before the boot section, after REORG-v1 (whose INS views stay registered and are
   reused through ctx.embed). Clips, Home and Data code is not changed (only Data's two "Press desk ›" link labels). */
const TB = { mods: new Map(), cur: null, sub: '', params: {}, last: {}, lists: {}, drawn: new Map(), pend: null, booted: false, memo: new Map(), open: new Map(), ft: new Map() };
try { Object.assign(TB.lists, JSON.parse(sessionStorage.getItem('jg2-tb-lists') || '{}')); } catch(e){}
const TB_MENU = [['reporters', 'Reporters', 'reporters'], ['outlets', 'Outlets', 'outlets'], ['releases', 'Press releases', 'press-releases'],
  ['bills', 'Bills', 'bills'], ['travel', 'Story travel', 'story-travel']];
/* old Press desk / Insights view ids and slugs -> tab ids */
const TB_OLD = { reporters: 'reporters', pitch: 'reporters', release_pickup: 'releases', releases: 'releases', bill_timeline: 'bills', bills: 'bills',
  story_travel: 'travel', 'story-travel': 'travel' };
const TB_PTS = { 'Very positive': 2, 'Positive': 1, 'Neutral': 0, 'Negative': -1, 'Very negative': -2 };
const tbFold = s => String(s == null ? '' : s).normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[‘’]/g, "'").replace(/[“”]/g, '"').replace(/\s+/g, ' ').trim();
const tbQ = q => tbFold(String(q == null ? '' : q).replace(/["“”]/g, ' '));   /* C3: quote marks are not searched */
const tbSlug = s => tbFold(s).replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'x';
const tbPhone = () => (window.innerWidth || 1400) <= 640;
const tbSlugOf = id => { const m = TB.mods.get(id); return (m && m.slug) || (TB_MENU.find(x => x[0] === id) || [])[2] || id; };

/* ---- shared helpers (also on ctx) ---- */
/* tone average over RATED stories only, on the tracker's tone scale (Very negative -2 ... Very positive +2) */
/* TONELABEL-v1 (Sammy comment 5dd6bf68): a tone average reads "<Label> <signed value>", e.g. "Neutral +0.1"; the label is the
   tone-scale band of the shown (one-decimal) value, banded at the midpoints between scale values (|v| < 0.5 Neutral,
   0.5-1.4 Positive/Negative, >= 1.5 Very positive/Very negative); the count of rated stories goes to the tooltip (title) */
const TB_TBANDS = ['Very negative', 'Negative', 'Neutral', 'Positive', 'Very positive'];
function tbToneLabel(avg){ if (avg == null || isNaN(avg)) return ''; const r1 = Math.round(avg * 10) / 10, a = Math.abs(r1);
  return TB_TBANDS[2 + (a < 0.5 ? 0 : a < 1.5 ? 1 : 2) * (r1 < 0 ? -1 : 1)]; }
function tbToneNum(avg){ if (avg == null || isNaN(avg)) return ''; const r1 = Math.round(avg * 10) / 10; return (r1 > 0 ? '+' : r1 < 0 ? '−' : '') + Math.abs(r1).toFixed(1); }
function tbToneText(avg, n){ if (avg == null || isNaN(avg) || n === 0) return ''; return tbToneLabel(avg) + ' ' + tbToneNum(avg); }
function tbToneTitle(n){ return n ? `Average over ${n} rated ${n === 1 ? 'story' : 'stories'} (−2 very negative … +2 very positive)` : ''; }
/* the cell / fact form: the label and value, the count in a tooltip; '' when no rated story */
/* TONEMUTED-v1 (Sammy 2026-10-28: "make this grey and smaller"): the signed number is secondary text (.tb-tone-n); t.text, sort and CSV unchanged */
function tbToneHtml(t){ return t && t.n ? `<span class="tb-tone-v" title="${esc(tbToneTitle(t.n))}">${esc(t.label || tbToneLabel(t.avg))} <span class="tb-tone-n">${esc(t.num || tbToneNum(t.avg))}</span></span>` : ''; }
function tbTone(rows){
  let s = 0, n = 0; (rows || []).forEach(r => { if (r && Object.prototype.hasOwnProperty.call(TB_PTS, r.tone)){ s += TB_PTS[r.tone]; n++; } });
  if (!n) return { avg: null, n: 0, text: '', label: '', num: '', title: '', csv: '' };
  const avg = s / n;
  return { avg, n, text: tbToneText(avg, n), label: tbToneLabel(avg), num: tbToneNum(avg), title: tbToneTitle(n), csv: (Math.round(avg * 100) / 100).toFixed(2) };
}
/* AFFIL-v1 (Sammy 2026-10-28: "reporters are affiliated only with outlets where they have Original stories; reprint outlets never
   appear as their employer anywhere"): tracker entries are Original rows only, so reprint outlets never count. A few Original rows
   are another outlet's edited run of the reporter's own story (e.g. a CalMatters story re-edited by The Davis Enterprise, split
   off by the 90% text rule): (a) the same person's story at an outlet where they have fewer stories, dated 0-7 days after (or the
   day before) a story of theirs at their main outlet with a similar headline; (b) for a person writing for a wire/originating
   service, their stories at a smaller non-wire outlet inside their service tenure. Such a story counts for the person under
   their own outlet, never under the outlet that re-ran it. tbAffOf(r, authorName) -> canonical outlet for that
   person on that story; tbAffOutlets(r) -> the set over the story's people. Cached per data version. */
const TB_AFF = { v: null, m: null };
/* the originating services of code/reprint_rule.py WIRE (originals order: wire / originating service first) */
const TB_WIRE = /calmatters|associated press|^ap$|center square|\bupi\b|religion news service|edsource|kff health news|kaiser health news|cronkite news|jewish telegraphic agency|\bjta\b|city news service|bay city news|yonhap|newsis|china news service|armenpress|mynewsla|jewish news syndicate|^jns\b|capital (?:&|and) main|states newsroom|stateline|^cnn wire|cnn newsource|zenger|cbm newswire|california black media|tribune content agency/i;   /* v23-REPAFF: + auditor's distributors */
const TB_HLSTOP = new Set(['the', 'and', 'for', 'with', 'from', 'that', 'this', 'what', 'will', 'into', 'over', 'after', 'about', 'their', 'here', 'have', 'says', 'said', 'more', 'than', 'they', 'are', 'how', 'why', 'new']);
const tbHlWords = t => new Set(tbFold(t).replace(/[^a-z0-9 ]+/g, ' ').split(' ').filter(w => w.length >= 3 && !TB_HLSTOP.has(w)));
function tbAffMap(){
  const v = D.length; if (TB_AFF.v === v && TB_AFF.d === D && Date.now() - TB_AFF.t < 60000) return TB_AFF.m;
  const byP = new Map();   // person key -> [{ r, o, d }]
  D.forEach(r => { if (!r || !r.date) return; const o = tbOutlet(r.outlet, r.aid); if (!o) return;
    const seen = new Set(); (r.authors || []).forEach(a => { const k = authorKey(a); if (!k || seen.has(k)) return; seen.add(k);
      (byP.get(k) || byP.set(k, []).get(k)).push({ r, o, d: Date.parse(String(r.date).slice(0, 10) + 'T12:00:00Z') || 0 }); }); });
  const m = new Map();     // person key + '|' + story id -> affiliated outlet (only where it differs from the story's outlet)
  byP.forEach((es, k) => {
    const n = new Map(); es.forEach(e => n.set(e.o, (n.get(e.o) || 0) + 1)); if (n.size < 2) return;
    es.forEach(e => { let best = null;
      es.forEach(f => { if (f.o === e.o) return; const gap = (e.d - f.d) / 864e5; if (gap < -1 || gap > 14) return;   /* v23-REPAFF: 7 -> 14 days */
        const nf = n.get(f.o), ne = n.get(e.o); if (!(nf > ne || (nf === ne && f.d < e.d))) return;
        const a = tbHlWords(e.r.hl), b = tbHlWords(f.r.hl); let o = 0; a.forEach(w => { if (b.has(w)) o++; });
        if (o < 2 || o / Math.max(1, Math.min(a.size, b.size)) < 0.4) return;
        if (!best || nf > n.get(best.o) || (nf === n.get(best.o) && f.d < best.d)) best = f; });
      if (best) m.set(k + '|' + e.r.id, best.o); });
    /* (b) the originals order: a person who writes for a wire / originating service (reprint_rule.WIRE) and has fewer stories at
       another (non-wire) outlet dated inside their service tenure (first to last service story, +-14 days): those stories are
       the service's copy run by that outlet, so they count under the service */
    const wires = [...n.keys()].filter(o => TB_WIRE.test(o)).sort((a, b) => n.get(b) - n.get(a));
    if (wires.length){ const w = wires[0], ds = es.filter(e => e.o === w).map(e => e.d), d0 = Math.min(...ds) - 14 * 864e5, d1 = Math.max(...ds) + 14 * 864e5;
      es.forEach(e => { if (TB_WIRE.test(e.o) || n.get(e.o) >= n.get(w) || e.d < d0 || e.d > d1) return; if (!m.has(k + '|' + e.r.id)) m.set(k + '|' + e.r.id, w); }); }
  });
  TB_AFF.v = v; TB_AFF.d = D; TB_AFF.t = Date.now(); TB_AFF.m = m; return m;
}
/* REPAFF-v1 (v23, DECISIONS V23Q): ONE affiliation engine. The build runs code/reporter_record.py (the rules reporters.py and the
   Update button use) and writes its answers into the tab-reporters block: aff = {story id: {person key: outlet}} where the
   person's outlet differs from the story's; p = {person key: {also, ran, c}}. The page reads them; the in-page rules above are
   only the fallback for a page built without the block. */
function tbAffOf(r, name){ if (!r) return ''; const o = tbOutlet(r.outlet, r.aid), b = tbBlock('reporters');
  if (b && b.aff && tbRepIds().has(String(r.id) + ':' + String(r.aid || ''))){ const m = b.aff[r.id]; return (m && m[authorKey(name)]) || o; }
  const x = tbAffMap().get(authorKey(name) + '|' + r.id); return x || o; }
let TB_REPIDS = null;
function tbRepIds(){ if (TB_REPIDS) return TB_REPIDS; const b = tbBlock('reporters'); TB_REPIDS = new Set(b && b.ids ? String(b.ids).split(',').map(x => /^\d/.test(x) ? 's' + x : x) : (b && b.aff ? D.map(r => String(r.id) + ':' + String(r.aid || '')) : [])); return TB_REPIDS; }
const tbRepInfo = key => { const b = tbBlock('reporters'); return (b && b.p && b.p[key]) || null; };
function tbAffOutlets(r){ const s = new Set(); (r && r.authors || []).forEach(a => { if (authorKey(a)) s.add(tbAffOf(r, a)); }); if (!s.size && r) s.add(tbOutlet(r.outlet, r.aid)); return s; }
/* HEADER-v2 value helpers: a list of values with even gaps, long ones collapsed to "first N + more" (the button reveals the rest);
   lines = one value per line (e.g. a publisher's dated spans) */
function tbHList(items, n){ items = (items || []).filter(x => x != null && x !== ''); if (!items.length) return ''; n = n || 6;
  const it = (x, i) => `<span class="tbh-i"${i >= n ? ' hidden' : ''}>${x}</span>`;
  return `<span class="tbh-list">${items.map(it).join('')}${items.length > n ? `<button type="button" class="linkbtn tbh-more" data-tbhmore>+ ${items.length - n} more</button>` : ''}</span>`; }
function tbLines(items){ items = (items || []).filter(x => x != null && x !== ''); return items.length ? `<span class="tbh-lines">${items.map(x => `<span class="tbh-ln">${x}</span>`).join('')}</span>` : ''; }
document.addEventListener('click', e => { const b = e.target.closest && e.target.closest('[data-tbhmore]'); if (!b) return; e.stopPropagation();
  const l = b.closest('.tbh-list'); l.querySelectorAll('.tbh-i[hidden]').forEach(x => { x.hidden = false; }); b.remove(); }, true);
/* the framework's shared data block (build/tabs/_common_data.py -> the JSON block with id tab-common): cleaned outlet names
   (n: raw -> canonical; a: Article ID -> canonical where the name depends on the row's publisher) and the sheet's
   Publisher column per canonical outlet as dated spans (p: canonical -> [[publisher, first date, last date, rows]]) */
const tbBlock = (() => { const c = new Map(); return name => { if (c.has(name)) return c.get(name); let v = null;
  try { const el = document.getElementById('tab-' + name); if (el) v = JSON.parse(el.textContent); } catch(e){ v = null; } c.set(name, v); return v; }; })();
const tbCommon = () => tbBlock('common') || { n: {}, a: {}, p: {} };
function tbOutlet(name, aid){ const c = tbCommon(), a = aid != null ? String(aid) : '';
  if (a && c.a && c.a[a]) return c.a[a]; const n = String(name || '').trim(); return (c.n && c.n[n]) || n; }
function tbPublishers(outlet){ const c = tbCommon(); return ((c.p && c.p[outlet]) || []).map(x => ({ name: x[0], d0: x[1], d1: x[2], n: x[3] })); }
/* the owner on a date: the span covering it (most rows on a tie), else the last owner before it, else the first after it;
   without a date the owner with the most rows (same rule as the Outlets tab) */
function tbPublisherOf(outlet, date){ const ps = tbPublishers(outlet); if (!ps.length) return '';
  if (date){ const d = String(date).slice(0, 10), dated = ps.filter(p => p.d0), hit = dated.filter(p => p.d0.slice(0, d.length) <= d && d <= (p.d1 || '9999'));
    if (hit.length) return hit.sort((a, b) => b.n - a.n)[0].name;
    const before = dated.filter(p => (p.d1 || p.d0) < d).sort((a, b) => (a.d1 || a.d0).localeCompare(b.d1 || b.d0)).pop(); if (before) return before.name;
    const after = dated.slice().sort((a, b) => a.d0.localeCompare(b.d0))[0]; if (after) return after.name; }
  return ps.slice().sort((a, b) => b.n - a.n)[0].name; }
/* a link drawn exactly like the story links (Clips' linkA look: bold label ↗ + host or sub), copy icon on its left */
const tbLink = (url, label, sub) => { if (!url) return ''; let host = ''; try { host = new URL(url).hostname.replace(/^www\./, ''); } catch(e){}
  return `<span class="dlinks tb-lk"><span class="lkw">${cpBtn(url)}<a href="${esc(url)}" target="_blank" rel="noopener"><b>${label ? esc(label) : esc(host || url)} ↗</b><span>${esc(sub || host)}</span></a></span></span>`; };
/* a bill number linking to its Bills page (bills module's billSlug: the session the date falls in); plain text when the
   Bills tab has no page for it */
function tbBillLink(bill, o){ const m = TB.mods.get('bills'), d = (o && o.date) || ''; let sl = '';
  try { sl = m && m.billSlug ? m.billSlug(bill, { date: d }, tbCtx('bills')) : ''; } catch(e){ sl = ''; }
  return sl ? `<button type="button" class="linkbtn tb-bill" data-bill="${esc(bill)}" data-date="${esc(String(d).slice(0, 10))}" title="Open the ${esc(bill)} page (Bills tab)">${esc(bill)}</button>` : esc(bill); }   /* routed to the page by the in-tab [data-bill] handler */
/* LINKRULES-v1 (Sammy, preview comments): bills -> bill page, authors -> reporter page, outlets -> outlet page, issues ->
   Clips filtered by that issue (the one allowed jump to Clips). Inside Clips every click keeps filtering Clips. */
const TB_AU = new Map();
function tbAuthorSub(name){ name = String(name || '').trim(); if (!name) return ''; if (TB_AU.has(name)) return TB_AU.get(name);
  const m = TB.mods.get('reporters'); let sub = '';
  try { if (m && m.legacy){ const x = m.legacy({ author: name }, tbCtx('reporters')) || {}; sub = x.sub || ''; } } catch(e){ sub = ''; }
  TB_AU.set(name, sub); return sub; }
/* a reporter's name linking to their page (people and the staff/board/wire/organisation bylines the Reporters tab lists);
   plain text when the Reporters tab has no entry for it */
function tbAuthorLink(name){ const sub = tbAuthorSub(name);
  return sub ? `<button type="button" class="linkbtn tb-au" data-tb-go="reporters" data-tb-sub="${esc(sub)}" title="${esc(name)} in Reporters">${esc(name)}</button>` : esc(name); }
/* LINKSCOPE-v1 (Sammy 2026-10-28, link rules): attributes (issue, reach, format, language, county) open Clips filtered by
   that value. On an entity page the link carries the page's scope (page.scope(entity, ctx) -> { sel: {pub|author|bills: [..]},
   when: [from, to, label]?, ranin?, label }): Politico's page -> "Food safety" opens Clips on Food safety AND Politico.
   Elsewhere (no scope) the attribute alone. Values Clips has no filter for stay plain text (since GEOMAP-v1 a state is filterable). */
function tbFacetLink(field, value, scope){
  value = String(value == null ? '' : value).trim(); if (!value) return '';
  if (!FACETS.some(f => f.key === field)) return esc(value);
  const sel = { [field]: [value] };
  if (scope && scope.sel) Object.entries(scope.sel).forEach(([k, vs]) => { if (k !== field && FACETS.some(f => f.key === k) && vs && vs.length) sel[k] = vs.slice(); });
  if (scope && scope.when) sel.__when = scope.when;
  if (scope && scope.ranin && !(scope.sel && scope.sel.pub && scope.sel.pub.length)) sel.__ranin = scope.ranin;
  return `<button type="button" class="linkbtn tb-fl" data-tbclip="${esc(JSON.stringify(sel))}" title="See the ${esc(value)} stories${scope && scope.label ? ' of ' + esc(scope.label) : ''} in Clips">${esc(value)}</button>`;
}
const tbIssueLink = (t, scope) => t ? tbFacetLink('topic', t, scope) : '';
/* a [data-tbclip] link: Clips with exactly those filters (capture phase: nothing else acts on the click) */
document.addEventListener('click', e => { const b = e.target.closest && e.target.closest('[data-tbclip]'); if (!b) return; e.preventDefault(); e.stopPropagation();
  let sel = {}; try { sel = JSON.parse(b.dataset.tbclip) || {}; } catch(x){ sel = {}; }
  closeAuthorSheet(); clearAll(); const parts = [];
  Object.entries(sel).forEach(([k, vs]) => { if (k.startsWith('__') || !S.sel[k]) return; (vs || []).forEach(v => S.sel[k].add(k === 'author' ? (canonAuthors([v])[0] || v) : v)); parts.push(vs.length > 2 ? `${vs[0]} (+${vs.length - 1})` : vs.join(' or ')); });
  if (sel.__ranin){ S.ranin = sel.__ranin; parts.push('ran in ' + sel.__ranin); }
  if (Array.isArray(sel.__when) && (sel.__when[0] || sel.__when[1])){ S.when = 'custom'; S.d0 = sel.__when[0] || null; S.d1 = sel.__when[1] || null; S.whenLabel = sel.__when[2] || `${sel.__when[0] || ''} – ${sel.__when[1] || ''}`; parts.push(S.whenLabel); renderWhen(); }
  render(); go('db'); toast(`Showing ${parts.join(' · ')}`); }, true);
/* an outlet's page in the Outlets tab (the module's own slug, via its legacy hook); '' when it has none */
const TB_OL = new Map();
function tbOutletSub(name, aid){ const c = tbOutlet(name, aid); if (!c) return ''; if (TB_OL.has(c)) return TB_OL.get(c);
  const m = TB.mods.get('outlets'); let sub = '';
  try { if (m && m.legacy){ const x = m.legacy({ outlet: c }, tbCtx('outlets')) || {}; sub = x.sub || ''; } } catch(e){ sub = ''; }
  TB_OL.set(c, sub); return sub; }
const tbBillSlug = (bill, date) => { const m = TB.mods.get('bills'); try { return m && m.billSlug ? m.billSlug(bill, { date: date || '' }, tbCtx('bills')) : ''; } catch(e){ return ''; } };
/* saved copies: a tracker story, or a sheet row that is not one (a press-release copy). The latter opens in the same story
   panel through a stand-in record (not in D: no counts, lists or exports see it) */
const tbHasSaved = id => hasHtml(id);
/* RELUI-v1 (rp-ui): tbOpenSaved(id, meta, list) — list = [[id, meta], ...] opens the viewer with "1 of N" over all of them
   (a release and its copies); meta.kind 'release' = the official release (link labelled "Official release") */
function tbStandIn(id, meta){
  if (!byId.has(id)){ const m = meta || {}, d = String(m.date || '');
    byId.set(id, { id, code: '', aid: m.aid || '', date: d, prec: d.length >= 10 ? 'day' : d.length >= 7 ? 'month' : 'year', year: +d.slice(0, 4) || 0, outlet: m.outlet || '', pub: '',
      hl: m.hl || '', hl_en: '', authors: [], akinds: [], atitle: '', bills: [], reps: [], also: '', rc: [], topic: '', issue: '', reach: '', media: '', county: '', role: 'Mentioned in story',
      lang: '', tone: 'Not rated', twhy: '', tauto: false, link: m.link || '', plink: m.plink || '', pq: m.pq || '', lstat: '', rep: 0, pick: 0, src: '', added: '', _s: '', _copy: true, _rel: m.kind === 'release' }); }
}
function tbOpenSaved(id, meta, list){
  tbStandIn(id, meta);
  const order = (list || []).filter(x => x && x[0]).map(x => { tbStandIn(x[0], x[1]); return x[0]; });
  openViewer(id, order.includes(id) ? order : [id]);
}
/* RELUI-v1 (UI review #2): a stand-in record (a release or a release copy, not a tracker story) shows only the kicker, title,
   one link row and the text: no reprint line, Edit details, tone, team note or story-only boxes */
function tbCopySheet(id){
  const sh = document.getElementById('sheet'), r = byId.get(id); if (!sh || !r) return;
  sh.classList.toggle('sheet-copy', !!r._copy); if (!r._copy) return;
  const meta = sh.querySelector('.sheet-meta'); if (!meta) return;
  meta.querySelectorAll('.factline,.sh-badges,.also,.in-entry,.relline,.tonebox,.notebox,.tb-av,[data-editstory]').forEach(x => x.remove());
  meta.querySelectorAll('.note').forEach(x => { if (!x.closest('.dlinks')) x.remove(); });
  if (r._rel && r.plink) meta.querySelectorAll('.dlinks a[href]').forEach(a => { if (a.getAttribute('href') === r.plink){ const b = a.querySelector('b'); if (b) b.textContent = 'Official release ↗'; } });
}
/* a link to another tab's entity page (cross-links: reporter page -> outlet pages, outlet page -> reporter pages) */
const tbPageLink = (tab, sub, label, title) => `<button type="button" class="linkbtn" data-tb-go="${esc(tab)}" data-tb-sub="${esc(sub)}"${title ? ` title="${esc(title)}"` : ''}>${esc(label)}</button>`;
const tbStoryLinks = r => { const ls = linksOf(r); return ls.length ? `<div class="dlinks">${ls.map(linkA).join('')}</div>` : ''; };
/* a tracker story as the Clips lists draw it (clickable: opens the story panel), with its links (copy icon left of each) */
const tbClip = (r, extra, o) => clipItem(r, extra) + ((o && o.links === false) ? '' : tbStoryLinks(r));
/* ROWLIST-v1: custom lists on entity pages (ladder, release copies, follow-ups, a bill's releases) drawn like Clips rows:
   line 1 the title (+ badges), line 2 muted facts joined by " · ", links on the right (copy icon left), optional quiet rank */
function tbRow(o){
  const meta = (o.meta || []).filter(Boolean), rk = o.rank != null;
  return `<div class="clip static tb-ri${rk ? ' rk' : ''}${o.cls ? ' ' + o.cls : ''}"${o.attrs || ''}${o.hidden ? ' hidden' : ''}>${rk ? `<span class="tb-ri-rk" aria-hidden="true">${o.rank}</span>` : ''}<div class="tb-ri-b"><div class="ct tb-ri-t">${o.title}${o.badges ? `<span class="tb-ri-bd">${o.badges}</span>` : ''}</div>${meta.length ? `<div class="cm tb-ri-m">${meta.map(x => `<span>${x}</span>`).join('<span class="tb-ri-sep" aria-hidden="true">·</span>')}</div>` : ''}${o.note ? `<div class="tb-ri-n">${o.note}</div>` : ''}</div>${o.right ? `<div class="tb-ri-r">${o.right}</div>` : ''}</div>`;
}
function tbCsvText(rows, cols){ return insCsv(rows, cols); }
function tbCut(months){ const d = new Date(TODAY + 'T12:00:00Z'); d.setUTCMonth(d.getUTCMonth() - months); return d.toISOString().slice(0, 10); }
/* date presets for type:'date' facets; ids are what the URL carries */
const TB_DATES = [['30d', 'Last 30 days', () => addDays(TODAY, -29)], ['3m', 'Last 3 months', () => tbCut(3)], ['6m', 'Last 6 months', () => tbCut(6)],
  ['12m', 'Last 12 months', () => tbCut(12)], ['24m', 'Last 24 months', () => tbCut(24)], ['5y', 'Last 5 years', () => tbCut(60)]];
/* render an old Insights view (INS) into el with a sandboxed ctx: its params never touch the URL */
function tbEmbed(viewId, el, params){
  const v = INS.views.get(viewId); if (!v || !el) return false;
  const c = insCtx(viewId); let p = Object.assign({}, params || {});
  Object.defineProperty(c, 'params', { get: () => Object.assign({}, p), set: x => { p = Object.assign({}, x || {}); }, configurable: true });
  c.setParams = x => { p = Object.assign({}, x || {}); }; c.refresh = () => tbEmbed(viewId, el, p);
  try { const r = v.render(el, c); if (r && r.catch) r.catch(e => console.error(e)); } catch(e){ console.error(e); el.innerHTML = `<div class="empty">This panel could not be drawn: ${esc(e && e.message || e)}</div>`; }
  return true;
}

/* ---- GEOMAP-v1 (agent-v20-maps): every map (CA counties and US states: Data, Outlets, Story travel) is the one component in
   14_county_map.js (geoMap; hover, pin, keyboard, Esc, legend, Top list) with the state rules in 52_us_map.js. The former
   MAPFIX-v1 tbMapLift, the insDrawCountyMap wrapper, the #caMap handlers and USMAP-v1 tbUsMap/tbDataUs are folded into it. ---- */
/* ---- mounting: menu buttons, the view section, CSS ---- */
/* CORNER-v2: tables' sticky header sits under the masthead: --hdr follows the masthead's real height (it was measured once at boot,
   before the tab bar and buttons settled, so a stuck header hid behind the masthead) */
(function tbHdr(){ const mh = document.querySelector('header.mast'); if (!mh) return;
  const set = () => { const h = mh.offsetHeight; if (h) document.documentElement.style.setProperty('--hdr', h + 'px'); };
  try { new ResizeObserver(set).observe(mh); } catch(e){} addEventListener('load', set); setTimeout(set, 0); })();
(function tbMount(){
  const nav = document.querySelector('nav.tabs'), an = $('#tab-an');
  if (nav && !document.querySelector('[data-tb]')){
    const html = TB_MENU.map(([id, label]) => `<button role="tab" id="tab-tb-${id}" data-tab="tb" data-tb="${id}" aria-selected="false" hidden>${esc(label)}</button>`).join('');
    if (an) an.insertAdjacentHTML('afterend', html); else nav.insertAdjacentHTML('beforeend', html);
  }
  const ti = $('#tab-in'); if (ti){ ti.hidden = true; ti.dataset.tbHidden = '1'; }
  if (!$('#view-tb')) $('main.wrap').insertAdjacentHTML('beforeend', '<section id="view-tb" hidden><div id="tbBody"></div></section>');
  document.head.insertAdjacentHTML('beforeend', `<style id="tabs-css">
nav.tabs button{white-space:nowrap}
@media (max-width:640px){nav.tabs{max-width:100%;min-width:0;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}
nav.tabs::-webkit-scrollbar{display:none}nav.tabs button{flex:none;padding:6px 10px}}
#tab-in[data-tb-hidden]{display:none!important}
#tbBody>.tb-view{display:grid;gap:12px}.tt,.tbe{display:grid;gap:12px;min-width:0}.tbe-chart .tbe-cnote{margin:0}#tbBody>.tb-view[hidden]{display:none}
.tt-head{display:grid;gap:4px;padding:4px 2px 0}.tt-h1{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 14px}.tt-h1 h2.sec{margin:0}.tt-head .cap{margin:0}
.tt-about>summary{cursor:pointer;font-size:var(--fs-md);color:var(--accent);font-weight:600;list-style:none}.tt-about>summary::-webkit-details-marker{display:none}.tt-about .cap{margin-top:4px;max-width:90ch}
.tt-head .tt-ans{font-size:var(--fs-lg);font-weight:600;color:var(--ink-2);margin:2px 0 0;max-width:100ch}
.tt .pane{gap:10px}.tt .toolbar .search{flex:1 1 300px}
.tt .tt-sort{display:none}.tt.tt-rowlist .tt-sort{display:block;max-width:240px}
.tt table.db td{font-size:var(--fs-md)}.tt table.db td.num,.tt table.db th.num button{text-align:right;font-variant-numeric:tabular-nums}
.tt table.db td.nw{white-space:nowrap}.tt .sub,.tbe .sub{color:var(--ink-3);font-size:var(--fs-sm)}
.tt table.db td .linkbtn{text-align:left}.tt td.tt-name .linkbtn{text-decoration:none;font-weight:600;color:var(--ink)}
.tt td.tt-name .linkbtn:hover{color:var(--accent);text-decoration:underline}
.tt tr.tt-on>td{background:var(--sel)}.tt tr.tt-det>td{background:var(--panel-2);cursor:default;padding:12px}
.tt tr.tt-det:hover{background:none}.tt .tt-detail{display:grid;gap:10px;min-width:0}
.tt .tt-rows{display:grid;padding:4px 14px}.tt .tt-r{border-top:1px solid var(--line-2);padding:2px 0}.tt .tt-r:first-child{border-top:0}
.tt .tt-r.tt-on{background:var(--sel);margin:0 -14px;padding:2px 14px}.tt .tt-r .clip{border-top:0}
.tt .tt-r>.tt-detail{padding:4px 0 12px}.tt .tt-more{display:flex;justify-content:center;gap:10px;padding:12px 0}
.tt .tt-empty,.tbe .tt-empty{padding:18px 14px}
.tt details.facet .tt-cust{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-top:6px;font-size:var(--fs-sm)}
.tt details.facet .tt-cust input{font-size:var(--fs-sm);padding:3px 4px;border:1px solid var(--line);border-radius:5px;background:var(--panel);color:var(--ink);max-width:132px}
.tt .tt-scrim,.tbe .tt-scrim{z-index:44}
.tbe .tbe-back{font-size:var(--fs-md)}.tbe .tbe-back .linkbtn{font-weight:600}
.tbe-sub{color:var(--ink-2);font-size:var(--fs-md)}
.clip.tb-ri{display:grid;grid-template-columns:minmax(0,1fr) auto;column-gap:18px;row-gap:0;padding:10px 0;align-items:start;cursor:default}
.clip.tb-ri.rk{grid-template-columns:2em minmax(0,1fr) auto;column-gap:12px}
.clip-list>.clip.tb-ri:first-child{padding-top:10px;border-top:0}
.tb-ri-rk{font:var(--fs-sm)/21px var(--f-mono);color:var(--ink-3);text-align:right;font-variant-numeric:tabular-nums}
.clip .tb-ri-t{font:600 var(--fs-h3)/1.4 var(--f-display);color:var(--ink);display:flex;flex-wrap:wrap;gap:2px 10px;align-items:baseline}
.clip.static:hover .tb-ri-t{color:var(--ink)}
.tb-ri-t>.linkbtn,.tb-ri-t>a{font:inherit;color:inherit;text-align:left;text-decoration:none}
.tb-ri-t>.linkbtn:hover,.tb-ri-t>a:hover{color:var(--accent);text-decoration:underline}
.tb-ri-bd{display:inline-flex;flex-wrap:wrap;gap:4px;font:400 var(--fs-sm) var(--f-body)}
.clip .tb-ri-m{font-size:var(--fs-sm);color:var(--ink-3);margin-top:4px;display:flex;gap:6px;flex-wrap:wrap;align-items:baseline}
.tb-ri-m .linkbtn{font-size:var(--fs-sm)}
.tb-ri-sep{color:var(--ink-3);opacity:.7}
.tb-ri-n{font-size:var(--fs-md);color:var(--ink-2);margin-top:4px}
.tb-ri-r{display:grid;gap:4px;justify-items:end;text-align:right;padding-top:1px}
.tb-ri-r .dlinks{margin:0;flex-direction:column;align-items:flex-end;gap:4px}
.tb-ri-r .note{font-size:var(--fs-sm)}
@media (max-width:640px){.clip.tb-ri{grid-template-columns:minmax(0,1fr)}.clip.tb-ri.rk{grid-template-columns:1.7em minmax(0,1fr);column-gap:8px}
.tb-ri-r{justify-items:start;text-align:left;margin-top:6px;padding-top:0}.clip.tb-ri.rk .tb-ri-r{grid-column:2}
.tb-ri-r .dlinks{flex-direction:row;flex-wrap:wrap;align-items:baseline;gap:4px 16px}}
.tbe .pane{gap:10px}
.tt table.db th button:focus:not(:focus-visible),.tbe table.db th button:focus:not(:focus-visible){outline:none}
/* HEADCORNER-v1 (Sammy, preview: "fix the corner of this"): the sort buttons have no box of their own; the header row follows the card's
   rounded corner (the first and last buttons take the cell's radius, so a hover or focus ring never squares it off) */
.tt table.db th button,.tbe table.db th button{border:0;border-radius:0;box-shadow:none;background:none}
/* CORNER-v4 (rp-final 2026-10-28, Sammy comments ab7c842d + 9eb75f10: "still an issue"; reuse the Clips table's code): every list
   table is the Clips table: table.db inside .card > .tablewrap, with the shell's own header / sticky / corner rules (header cells take
   the card's radius: table.db thead th:first-child / :last-child 9px). The separate tab-table corner CSS (CORNER-v2 overflow:clip,
   CORNER-v3 clip-path, the radius-0 overrides) is removed: it matched the tab cards by class but the Clips card only through :has(),
   so engines without :has() drew the two differently. */
.tt table.db th button:focus-visible,.tbe table.db th button:focus-visible{outline:2px solid currentColor;outline-offset:-4px}
.tbe-emb{display:grid;gap:8px;min-width:0}.tb-mini{gap:8px}.tb-mini-h{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px 14px;padding:4px 2px 0}
.tb-mini-h h2.sec{margin:0}.tb-mini-n{color:var(--ink-3);font-weight:600;font-size:var(--fs-xs);font-variant-numeric:tabular-nums;margin-left:4px}.tb-mini-q{flex:0 1 280px;min-width:0}
.tb-pgo{border:0;background:none;padding:0 2px;margin-left:4px;font:600 var(--fs-xs)/1 var(--f-body);color:var(--ink-3);cursor:pointer;white-space:nowrap;vertical-align:baseline}
.tb-pgo:hover,.tb-pgo:focus-visible{color:var(--accent);text-decoration:underline}
.clip .ct>.tv-hl{font:inherit;color:inherit;text-align:left;text-decoration:none;padding:0}.clip .ct>.tv-hl:hover{color:var(--accent);text-decoration:underline}
.tt .tv-go{font-size:var(--fs-md);font-weight:600;margin-top:2px}
.tb-lk{margin:0;display:inline-flex;max-width:100%}.tb-lk a{flex-wrap:wrap;gap:0 6px;min-width:0}.tb-lk a b,.tb-lk a span{white-space:nowrap}.tb-lk a span{overflow:hidden;text-overflow:ellipsis;max-width:100%}
.tb-av{border:1px solid var(--line);border-radius:8px;padding:10px 12px;display:grid;gap:6px;font-size:var(--fs-md)}.tb-av h4{margin:0;font-size:var(--fs-md);font-weight:700;color:var(--ink)}
.tb-av dl{display:grid;grid-template-columns:auto minmax(0,1fr);gap:3px 12px;margin:0}.tb-av dt{color:var(--ink-3);font-size:var(--fs-sm)}.tb-av dd{margin:0;color:var(--ink);overflow-wrap:anywhere}
.tb-av ul{margin:2px 0 0;padding-left:18px;color:var(--ink-2)}.tb-av-l{display:flex;flex-wrap:wrap;gap:4px 16px}
.tb-sec{margin-top:14px;display:grid;gap:6px}.tb-sec>h3{margin:0;font-size:var(--fs-md);font-weight:700;color:var(--ink)}
.clip.static{cursor:default}.clip.static:hover .ct{color:var(--ink)}
.tb-us{margin-top:14px;display:grid;gap:6px}.tb-us-h{margin:0;font-size:var(--fs-md);font-weight:700;color:var(--ink)}
.tb-usmap{width:100%;height:auto;max-height:420px}
.in-cmap path,.tb-usmap path,#caMap path{vector-effect:non-scaling-stroke;stroke-linejoin:round;stroke-linecap:round}
.in-cmap path,.tb-usmap path{stroke:var(--map-edge);stroke-width:.75}
.in-cmap path.on:hover,.tb-usmap path.on:hover{stroke:var(--map-edge);stroke-width:.75}
.in-cmap,.tb-usmap,#caMap,.in-cmap path,.tb-usmap path,#caMap path,.in-cmap path:focus,.tb-usmap path:focus,#caMap path:focus,#caMap:focus{outline:none}
.in-cmap path.on,.tb-usmap path.on{cursor:pointer}
path.map-lift{pointer-events:none;stroke:var(--map-edge-on);stroke-width:2;vector-effect:non-scaling-stroke;stroke-linejoin:round;filter:brightness(1.06)}
path.map-lift.frozen{stroke:var(--accent);stroke-width:2.6;filter:brightness(1.12) saturate(1.1)}
#caMap #caLift{vector-effect:non-scaling-stroke}
.tb-us-sel{font-size:var(--fs-md);color:var(--ink-2)}.tb-us-sel b{color:var(--ink)}
@media (max-width:760px){.tt .tt-sort{display:block}.tt table.db thead{display:none}
.tt table.db,.tt table.db tbody,.tt table.db tr,.tt table.db td{display:block;width:auto}
.tt table.db tr{padding:10px 4px;border-bottom:1px solid var(--line-2)}.tt table.db td{border:0;padding:2px 8px}
.tt table.db td[data-l]::before{content:attr(data-l) ": ";color:var(--ink-3);font-size:var(--fs-xs);text-transform:uppercase;letter-spacing:.05em}
.tt table.db td.tt-name::before{content:none}.tt table.db td.num{text-align:left}.tt tr.tt-det>td{padding:10px 8px}}
@media (max-width:640px){.tt .toolbar,.tbe .toolbar{grid-template-columns:auto minmax(0,1fr)}}
/* HEADER-v2: the entity-page header (tbHeadHtml) */
.tbe-head{display:grid;gap:12px;min-width:0}
.tbe-hcard{padding:0;min-width:0}
.tbh-top{padding:16px 18px 14px;display:grid;gap:4px;min-width:0}
.tbh-kick{display:flex;flex-wrap:wrap;align-items:baseline;gap:0 2px;letter-spacing:.08em}
.tbh-dot{margin:0 7px;opacity:.7}
.tbh-title{overflow-wrap:anywhere}
.tbh-dek{font-size:var(--fs-md);line-height:1.45;color:var(--ink-2);max-width:110ch;display:grid;gap:2px}
.tbh-grid{display:grid;grid-template-columns:minmax(0,1fr)}
.tbh-g{padding:12px 18px 14px;min-width:0;border-top:1px solid var(--line-2)}
@media (min-width:980px){.tbh-grid[data-n="2"]{grid-template-columns:repeat(2,minmax(0,1fr))}.tbh-grid[data-n="3"]{grid-template-columns:repeat(3,minmax(0,1fr))}.tbh-grid[data-n="4"]{grid-template-columns:repeat(4,minmax(0,1fr))}.tbh-g+.tbh-g{border-left:1px solid var(--line-2)}}
.tbh-gl{margin:0 0 8px;font:600 var(--fs-xs)/1.3 var(--f-body);letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3)}
.tb-tone-n{color:var(--ink-3);font-size:var(--fs-sm);font-variant-numeric:tabular-nums}
.tbe-facts{display:grid;grid-template-columns:8.5em minmax(0,1fr);gap:6px 14px;margin:0;align-items:baseline}
.tbe-facts>div{display:contents}
.tbe-facts dt{font-size:var(--fs-sm);line-height:1.45;color:var(--ink-3);overflow-wrap:anywhere}
.tbe-facts dd{margin:0;font-size:var(--fs-md);line-height:1.45;color:var(--ink);overflow-wrap:anywhere;min-width:0}
.tbe-facts dd .linkbtn{margin:0;padding:0;line-height:inherit;vertical-align:baseline;font-size:inherit;text-align:left}.linkbtn.tb-rlink{text-decoration:none}.linkbtn.tb-rlink:hover{text-decoration:underline}
.tbe-facts dd .sub{font-size:var(--fs-sm)}
.tbe-facts dd .lkw,.tbe-facts dd .tb-lk{margin:0}
.tbh-list{display:flex;flex-wrap:wrap;gap:3px 14px;align-items:baseline}
.tbh-i{display:block;min-width:0}.tbh-i[hidden]{display:none}
.tbh-more{font-size:var(--fs-md);font-weight:600}
.tbh-lines{display:grid;gap:3px}.tbh-ln{display:flex;flex-wrap:wrap;gap:0 6px;align-items:baseline}
.tbh-links{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px 20px;padding:11px 18px 12px;border-top:1px solid var(--line-2);background:var(--panel-2);border-radius:0 0 9px 9px}
.tbh-lk{grid-template-columns:auto minmax(0,1fr);flex:1 1 auto;min-width:0}
.tbh-lk dt{white-space:nowrap}
.tbe-acts{display:flex;gap:8px 14px;flex-wrap:wrap;align-items:center;font-size:var(--fs-md);margin-left:auto}
.tbe-extra{display:grid;gap:0;min-width:0}.tbe-extra>.tb-us:first-child,.tbe-extra>.tb-sec:first-child{margin-top:0}
/* EXTRASEP-v1 (Sammy 2026-10-28 on the release page box: "clearer separations between everything ... base it on the style we have going
   in the tracker"): each block of a page's own card (saved copy, copies, bill coverage, related, milestones ...) is set off by a
   hairline var(--line-2) rule and even spacing; release-box block titles use the story sheet's fact-label idiom (small uppercase muted) */
.tbe-extra>*+*{margin-top:16px;padding-top:16px;border-top:1px solid var(--line-2)}
.tbe-extra>.tb-us,.tbe-extra>.tb-sec{gap:8px}
.tbe-extra .tb-us-h,.tbe-extra .tb-sec>h3{font:600 var(--fs-xs)/1.35 var(--f-body);letter-spacing:.07em;text-transform:uppercase;color:var(--ink-3)}
.tbe-extra details.tb-us>summary.tb-us-h{list-style-position:outside}
.tbe-extra .tb-us>.cap,.tbe-extra .tb-sec>.cap{margin:0;max-width:100ch;font-size:var(--fs-sm);color:var(--ink-2)}
.tbe-extra .tb-us>.clip-list,.tbe-extra .tb-us>.note{margin-top:2px}
@media (max-width:640px){.tbe-extra>*+*{margin-top:14px;padding-top:14px}}
@media (max-width:640px){.tbh-top{padding:14px 14px 12px}.tbh-g{padding:11px 14px 12px}
.tbe-facts{grid-template-columns:7.2em minmax(0,1fr);column-gap:10px}.tbh-links{padding:10px 14px}.tbe-acts{margin-left:0}}
</style>`);
})();

/* ---- routing ---- */
function tbHash(){ const p = new URLSearchParams(); Object.entries(TB.params || {}).forEach(([k, v]) => { if (v != null && v !== '') p.set(k, v); });
  const q = p.toString(); return '#' + tbSlugOf(TB.cur) + (TB.sub ? '/' + encodeURIComponent(TB.sub) : '') + (q ? '?' + q : ''); }
/* '#<slug>[/<sub>][?q]' for a tab; '#insights[/<id>]', '#press-desk[/<slug>]', '#<old view id>' redirect; null when not a tab link */
function tbParse(h){
  h = String(h || '').replace(/^#/, ''); if (!h) return null;
  const [path, qs] = [h.split('?')[0], h.includes('?') ? h.slice(h.indexOf('?') + 1) : ''];
  const params = {}; if (qs) new URLSearchParams(qs).forEach((v, k) => params[k] = v);
  const parts = path.split('/'), head = parts[0];
  const bySlug = TB_MENU.find(x => x[2] === head) || [...TB.mods.values()].map(m => [m.id, m.label, m.slug]).find(x => x[2] === head);
  if (bySlug) return { id: bySlug[0], sub: parts.length > 1 ? decodeURIComponent(parts.slice(1).join('/')) : '', params, legacy: false };
  let old = null;
  if (head === 'insights' || head === 'press-desk'){ const x = parts[1] || ''; if (x === 'tone_topic' || x === 'tone-by-issue') return null; old = x ? TB_OLD[x] : 'reporters'; if (!old) return null; }
  else if (TB_OLD[head] && ['release_pickup', 'bill_timeline', 'story_travel', 'pitch'].includes(head)) old = TB_OLD[head];
  if (!old){   /* on page load a slug of a module that registers later (not in the menu list) is kept pending */
    if (!TB.booted && /^[a-z][a-z0-9-]*$/.test(head) && !['clips', 'trends', 'report', 'data', 'about', 'x-reset'].includes(head))
      return { id: head.replace(/-/g, '_'), slug: head, sub: parts.length > 1 ? decodeURIComponent(parts.slice(1).join('/')) : '', params, legacy: false };
    return null; }
  delete params.win;   // PITCH24-v1 links: the Reporters tab has its own date filter (no default since DEFCLEAR-v1)
  return { id: old, sub: '', params, legacy: true };
}
function tbSel(){ document.querySelectorAll('nav.tabs button[data-tab]').forEach(b => b.setAttribute('aria-selected', String(b.dataset.tab === S.tab && (S.tab !== 'tb' || b.dataset.tb === TB.cur))));
  const on = S.tab === 'tb' && $('#tab-tb-' + TB.cur); if (on && on.scrollIntoView){ const n = on.parentElement; if (n && n.scrollWidth > n.clientWidth + 1) n.scrollLeft = Math.max(0, on.offsetLeft - (n.clientWidth - on.offsetWidth) / 2); } }
const tbSetTab0 = setTab;
setTab = function(t){
  if (!TB.booted){ TB.booted = true;   /* a tab link on page load: the tab modules register after the main script */
    if (TB.pend && t !== 'in'){ t = 'tb'; TB.cur = TB.pend.id; if (TB.mods.has(TB.pend.id)){ const p = TB.pend; TB.pend = null; tbPrime(p); } } }
  if (t !== 'tb'){ tbSetTab0(t); $('#view-tb').hidden = true; tbSel(); return; }
  if (!TB.pend && (!TB.cur || !TB.mods.has(TB.cur))){ const f = TB_MENU.find(x => TB.mods.has(x[0])) || [...TB.mods.keys()].map(k => [k]); if (!f || !f[0]){ tbSetTab0('ov'); return; } TB.cur = f[0]; TB.sub = ''; TB.params = TB.last[TB.cur] || {}; }
  S.tab = 'tb'; ['ov', 'db', 'an', 'in'].forEach(k => { const v = $('#view-' + k); if (v) v.hidden = true; }); $('#view-tb').hidden = false; tbSel();
  try { history.replaceState(null, '', tbHash()); } catch(e){}
};
const tbRender0 = render;
render = function(){ tbRender0(); if (S.tab === 'tb') tbShow(); };
/* set the current tab/sub/params from a parsed link (legacy params are translated by the module) */
function tbPrime(p){
  const m = TB.mods.get(p.id); let sub = p.sub || '', params = Object.assign({}, p.params || {});
  if (p.legacy && m && typeof m.legacy === 'function'){ try { const x = m.legacy(params, tbCtx(p.id)) || {}; params = x.params || {}; sub = x.sub || ''; } catch(e){ console.error(e); params = {}; } }
  if (TB.cur && !TB.sub && TB.cur !== p.id) TB.last[TB.cur] = Object.assign({}, TB.params);
  TB.cur = p.id; TB.sub = sub; TB.params = params;
}
function tbOpen(id, params, sub, legacy){
  if (!TB.mods.has(id)) return false;
  if (legacy && params) { params = Object.assign({}, params); delete params.win; }   // PITCH24-v1 links carried win=12/24
  if (TB.cur === id && !TB.sub && sub && S.tab === "tb" && TB.drawn.has(id)){ TB.lists[id] = Object.assign({}, TB.params); try { sessionStorage.setItem('jg2-tb-lists', JSON.stringify(TB.lists)); } catch(e){} }   // the list state the back link returns to (kept for this browser tab)
  tbPrime({ id, sub: sub || '', params: params == null ? (sub ? {} : (TB.lists[id] || TB.last[id] || {})) : params, legacy });
  closeAuthorSheet(); S.page = 0; setTab('tb'); tbShow(true); scrollTo(0, 0); return true;
}
function tbShow(force){
  const id = TB.cur, m = TB.mods.get(id), body = $('#tbBody'); if (!m || !body) return;
  let el = body.querySelector(`.tb-view[data-tb="${id}"]`);
  if (!el){ el = document.createElement('div'); el.className = 'tb-view'; el.dataset.tb = id; body.appendChild(el); }
  body.querySelectorAll('.tb-view').forEach(v => v.hidden = v !== el);
  try { history.replaceState(null, '', tbHash()); } catch(e){}
  const key = insSig() + '|' + TB.sub + '|' + JSON.stringify(TB.params) + '|' + (tbPhone() ? 'p' : 'd');
  if (!force && TB.drawn.get(id) === key) return;
  TB.drawn.set(id, key);
  const fresh = el.cloneNode(false); el.replaceWith(fresh); el = fresh;
  const ctx = tbCtx(id), fail = e => { console.error(e); el.innerHTML = `<div class="card pad"><div class="empty">This tab could not be drawn: ${esc(e && e.message || e)}</div></div>`; };
  try {
    let r;
    if (TB.sub && m.page) r = tbEntityPage(el, ctx, m);
    else if (m.list) r = tbSearchTab(el, ctx, m.list);
    else if (m.render) r = m.render(el, ctx);
    if (r && r.catch) r.catch(fail);
  } catch(e){ fail(e); }
}
function tbCtx(id){
  const c = insCtx(id), m = TB.mods.get(id);
  Object.defineProperty(c, 'params', { get: () => Object.assign({}, TB.params), set: v => { TB.params = Object.assign({}, v || {}); try { history.replaceState(null, '', tbHash()); } catch(e){} }, configurable: true });
  Object.assign(c, {
    tab: id, sub: TB.sub, version: insSig(), phone: tbPhone(),
    setParams: p => { TB.params = Object.fromEntries(Object.entries(p || {}).filter(([, v]) => v != null && v !== '')); if (TB.cur === id){ TB.drawn.set(id, insSig() + '|' + TB.sub + '|' + JSON.stringify(TB.params) + '|' + (tbPhone() ? 'p' : 'd')); try { history.replaceState(null, '', tbHash()); } catch(e){} } },
    refresh: () => { if (TB.cur === id) tbShow(true); },
    go: (tab, params, sub) => tbOpen(tab, params || {}, sub || ''),
    openPage: sub => tbOpen(id, {}, sub),
    back: () => tbOpen(id, TB.lists[id] || {}, ''),
    block: name => tbBlock(name) || insBlock(name),
    fold: tbFold, slug: tbSlug, tone: tbTone, toneText: tbToneText, toneLabel: tbToneLabel, toneHtml: tbToneHtml, hlist: tbHList, lines: tbLines, affOf: tbAffOf, affOutlets: tbAffOutlets, repInfo: tbRepInfo, outlet: tbOutlet, house: (n, aid) => repHouse(n, aid), publishers: tbPublishers, publisherOf: tbPublisherOf,
    link: tbLink, storyLinks: tbStoryLinks, linksOf,   /* PRINTLINK-v1: modules list links through linksOf */ pageLink: tbPageLink, billLink: tbBillLink, authorLink: tbAuthorLink, issueLink: t => tbIssueLink(t, c.scope), facetLink: (f, v) => tbFacetLink(f, v, c.scope), outletSub: tbOutletSub, miniList: tbMiniList, scope: null, hasSaved: tbHasSaved, openSaved: tbOpenSaved, clip: tbClip, row: tbRow, cpBtn, embed: tbEmbed, dates: TB_DATES, cut: tbCut,
    timeChart, niceScale, niceMax, axis, usMap: (h, o, p) => geoUsOutlets(h, o, Object.assign({ scope: c.scope }, p || {})), outModel: geoUsModel, drawCountyMap: gmDrawCounty, geoMap: (h, sp) => geoMap(h, Object.assign({ scope: c.scope }, sp || {})), langOf, vals, FACETS, cut0: n => addDays(TODAY, -n), mod: m,
    rels: relIndex,   /* RELREVERSE-v1 (rp-reverse): releases + story -> releases index (01_authors.js) */
    info: tbInfo   /* RELUI-v1: the shared ⓘ tooltip */
  });
  return c;
}
/* entry points that used to open Press desk views (story panel, Home, Data) now open the tabs */
const tbInsShow0 = insShow;
insShow = function(id, params, force){ const t = TB_OLD[id]; if (t && TB.mods.has(t)){ tbOpen(t, Object.assign({}, params || {}), '', true); return; } return tbInsShow0(id, params, force); };
const tbInsNav0 = insNav;
insNav = function(){ const ids = tbInsNav0(); const ti = $('#tab-in'); if (ti) ti.hidden = true; return ids; };
const tbInsParse0 = insParse;
insParse = function(h){ const t = tbParse(h); if (t){ TB.pend = t; return null; } return tbInsParse0(h); };
/* a tab link whose module never registered falls back to Home */
document.addEventListener('DOMContentLoaded', () => { if (TB.pend && !TB.mods.has(TB.pend.id)){ const p = TB.pend; go('ov'); TB.pend = p;
  setTimeout(() => { if (TB.pend === p) TB.pend = null; }, 8000); } });   /* a module that registers a little later still opens its link */
/* AVTAB-v1 (agent-avtab data; inbox item 2): a small "Audio & video" box in the story panel for podcast/radio/TV/video stories */
function tbAvBox(r){
  const a = r && r.av; if (!a || a.type === 'Web story') return '';
  const j = (...x) => x.filter(Boolean).join(' · '), row = (k, v) => v ? `<dt>${esc(k)}</dt><dd>${v}</dd>` : '';
  const guests = [a.g1, a.g2, a.g3, a.g4].filter(Boolean).map(esc).join(', ') + (a.gmore ? ` <span class="note">${esc(a.gmore)}</span>` : '');
  const ti = avtInfo(r), ments = (ti ? ti.ments : [a.m1, a.m2, a.m3, a.m4, a.m5].filter(Boolean)).map(m => `<li>${esc(m)}</li>`).join('') + (a.mmore ? `<li class="note">${esc(a.mmore)}</li>` : '');
  const hosts = /^(Podcast|Radio|TV|Video)$/.test(r.media || '') && (r.authors || []).length ? r.authors.map(esc).join(', ') : '';
  const links = [['lshow', 'Show page'], ['lapple', 'Apple Podcasts'], ['lspotify', 'Spotify'], ['lyoutube', 'YouTube'], ['larchive', 'Internet Archive']].filter(([k]) => a[k]).map(([k, l]) => tbLink(a[k], l)).join('');
  return `<div class="tb-av"><h4>Audio &amp; video${a.type ? ` <span class="note">${esc(a.type)}</span>` : ''}</h4><dl>
    ${row('Channel', esc(j(a.channel, a.channel && a.network && !String(a.channel).includes(a.network) ? a.network : '')))}${row('Show', esc(a.show || ''))}${row('Episode', esc(j(a.title, a.epno ? '#' + a.epno : '')))}${row(ti ? ti.label : 'Aired', ti ? esc(j(ti.date && dateLabel({ date: ti.date, prec: 'day' }), ti.when)) + (ti.src ? ` <span class="note">(source: ${esc(ti.src)})</span>` : '') : esc(j(a.air, a.airtime)))}${row('Length', esc(a.dur || ''))}
    ${row('Hosts', hosts)}${row('His role', esc(String(a.role || '').replace(/^./, c => c.toUpperCase())))}${row('Guests', guests)}${row('Transcript', esc(a.tkind && a.tkind !== 'none' ? a.tkind.replace(/^./, c => c.toUpperCase()) + (a.larchive && a.type === 'Broadcast segment' ? ' (auto-captions)' : '') : ''))}</dl>
    ${ments ? `<div class="tb-av-m"><b>Mentions</b>${a.tbasis ? ` <span class="note">${esc(/^transcript time marker/.test(a.tbasis) ? 'clock time from the transcript, shown in Pacific; "in" = time since the show started' : /^offset into the program/.test(a.tbasis) ? 'time into the program (TV News Archive clip start)' : a.tbasis)}</span>` : ''}<ul>${ments}</ul></div>` : ''}${links ? `<div class="tb-av-l">${links}</div>` : ''}</div>`;   /* AVSHOW-v1: Notes and "Details from" are back-end text, kept in the sheet and data only; NOSHOWCHAN-v1: a blank Channel is left out like Show (no station/network fallback) */
}
/* HOWSPREAD-v1 (Sammy 2026-10-28): the story panel links "How it spread ›" to the Story travel page when another outlet ran
   the story (copies in its own outlet or house don't count). Reporter pages are reached from the byline itself (and, inside Clips,
   from the "page ›" icons), so the old "Reporter page" links are gone. */
const tbTravels = r => repNames(r).length > 0;   /* REPCOUNT-v1: the same count as Clips, Data, Outlets and Story travel (other outlets, own house left out) */
insEntry = function(r){
  const out = [];
  if (tbTravels(r)) out.push(`<button class="linkbtn" data-ins-go="story_travel" data-ins-k="id" data-ins-v="${esc(r.id)}" title="See where this story ran (Story travel tab)">How it spread ›</button>`);
  return (out.length ? `<div class="in-entry">${out.join('')}</div>` : '') + tbAvBox(r);   /* + AVTAB-v1 box */
};
/* PAGEICON-v1 (Sammy 2026-10-28): inside Clips a click on a bill, author or outlet in the story panel keeps filtering Clips;
   a small "page ›" icon next to each opens its Bills / Reporters / Outlets page */
function tbPanelIcons(id){
  if (S.tab !== 'db') return; const r = byId.get(id), meta = document.querySelector('#sheet .sheet-meta'); if (!r || !meta || r._copy) return;
  const ic = (tab, sub, what) => sub ? `<button type="button" class="tb-pgo" data-tb-go="${tab}" data-tb-sub="${esc(sub)}" title="Open the ${esc(what)} page" aria-label="Open the ${esc(what)} page">page ›</button>` : '';
  const add = (b, h) => { if (h && !(b.nextElementSibling && b.nextElementSibling.classList.contains('tb-pgo'))) b.insertAdjacentHTML('afterend', h); };
  meta.querySelectorAll('[data-bill]').forEach(b => add(b, ic('bills', tbBillSlug(b.dataset.bill, r.date), b.dataset.bill)));
  meta.querySelectorAll('[data-author]').forEach(b => add(b, ic('reporters', tbAuthorSub(b.dataset.author), b.dataset.author)));
  meta.querySelectorAll('[data-pub]').forEach(b => add(b, ic('outlets', tbOutletSub(r.outlet, r.aid), tbOutlet(r.outlet, r.aid))));
}
document.querySelector('nav.tabs').addEventListener('click', e => { const b = e.target.closest('button[data-tb]'); if (!b) return;
  e.stopPropagation(); const id = b.dataset.tb; if (S.tab === 'tb' && TB.cur === id && !TB.sub) return;
  tbOpen(id, TB.sub && TB.cur === id ? (TB.lists[id] || {}) : null, ''); }, true);
addEventListener('hashchange', () => { const t = tbParse(location.hash); if (t && TB.mods.has(t.id)) tbOpen(t.id, t.params, t.sub, t.legacy); });
let tbRT; addEventListener('resize', () => { clearTimeout(tbRT); tbRT = setTimeout(() => { if (S.tab === 'tb') tbShow(); }, 220); });
document.addEventListener('click', e => { const b = e.target.closest('[data-tb-go]'); if (!b) return; e.preventDefault(); e.stopPropagation();
  let p = {}; try { p = JSON.parse(b.dataset.tbP || '{}'); } catch(x){} tbOpen(b.dataset.tbGo, p, b.dataset.tbSub || ''); });

document.addEventListener('click', e => { const b = e.target.closest('[data-tbstory]'); if (!b) return; e.preventDefault(); e.stopPropagation(); openViewer(b.dataset.tbstory, (b.dataset.tborder || b.dataset.tbstory).split(',')); });
/* inside a tab (not its entity-page story list, which filters itself) and in the story panel opened from a tab, bill,
   reporter and outlet links open the Bills / Reporters / Outlets pages instead of Clips (Sammy: the tabs never send the
   user to Clips). Clips, Home and Data keep their links into Clips. */
document.addEventListener('click', e => {
  const t0 = e.target; if (!t0.closest) return;
  /* LINKRULES-v1: an author name anywhere outside Clips (Home, Data, the tabs, a story panel opened outside Clips) opens the
     reporter page; inside Clips (its list and the story panel opened from it) it keeps filtering Clips */
  const au0 = t0.closest('[data-author]');
  if (au0 && TB.mods.has('reporters') && S.tab !== 'db' && !t0.closest('#view-db') && !t0.closest('.tbe-body, .tbe-xbody') && !t0.closest('details.facet')){
    const sub = tbAuthorSub(au0.dataset.author); e.preventDefault(); e.stopPropagation(); closeAuthorSheet();
    if (sub) tbOpen('reporters', {}, sub); else tbOpen('reporters', { q: au0.dataset.author }, ''); return; }
  const t = e.target;   /* LINKRULES-v2: the story panel opened from Home / Data too (Clips keeps filtering) */
  if (S.tab !== 'tb' && !(t.closest('#sheet') && S.tab !== 'db')) return;
  const inTab = t.closest('#view-tb') && !t.closest('.tbe-body, .tbe-xbody') && !t.closest('details.facet'), inSheet = t.closest('#sheet');
  if (!inTab && !inSheet) return;
  const b = t.closest('[data-bill]'), au = t.closest('[data-author]'), pb = t.closest('[data-pub]');
  if (b && TB.mods.has('bills')){ e.preventDefault(); e.stopPropagation(); closeAuthorSheet();
    const date = b.dataset.date || (inSheet && S.openId && byId.get(S.openId) ? byId.get(S.openId).date : ''), m = TB.mods.get('bills');
    let sl = ''; try { sl = m.billSlug ? m.billSlug(b.dataset.bill, { date }, tbCtx('bills')) : ''; } catch(x){}
    if (sl) tbOpen('bills', {}, sl); else tbOpen('bills', { q: b.dataset.bill }, ''); return; }
  if (au && TB.mods.has('reporters')){ e.preventDefault(); e.stopPropagation(); closeAuthorSheet(); tbOpen('reporters', { author: au.dataset.author }, '', true); return; }
  if (pb && TB.mods.has('outlets')){ e.preventDefault(); e.stopPropagation(); closeAuthorSheet(); const r = inSheet && S.openId ? byId.get(S.openId) : null;
    tbOpen('outlets', { outlet: r ? tbOutlet(r.outlet, r.aid) : pb.dataset.pub }, '', true); return; }
}, true);

/* Data's "Reporters with the most stories: A (n), B (n) and C (n)." names link to the reporter pages (LINKRULES-v1) */
function tbWhoHtml(t){ const m = /^(.*?:\s*)(.+?)(\.?)$/.exec(String(t || '')); if (!m) return esc(t);
  const parts = m[2].split(/(, | and )/);
  return esc(m[1]) + parts.map(p => { if (p === ', ' || p === ' and ') return p; const mm = /^(.+?)( \(\d+\))?$/.exec(p); return mm ? tbAuthorLink(mm[1]) + esc(mm[2] || '') : esc(p); }).join('') + esc(m[3]); }

/* ---- NAVHIST-v1 (Sammy: "a tracker wide, forward and back page button that goes on the header") ----
   An internal stack of the tracker's own places (the artifact frame's history is not reliable and every in-app move uses
   replaceState): a tab, an entity page, the filters a tab keeps in its URL, and the story panel. One entry per move;
   quick successive URL changes (typing in a search box) collapse into one entry; Back / Forward / Alt+arrows walk it and
   never leave the tracker. */
const NAV = { st: [], i: -1, lock: 0, t: null, burst: 0 };
const navCur = () => ({ h: location.hash || '', s: (!$('#sheet').hidden && S.openId) || '' });
function navRecord(now){
  if (NAV.lock) return;
  const go_ = () => { NAV.t = null; if (NAV.lock) return; const c = navCur(), top = NAV.st[NAV.i];
    if (top && top.h === c.h && top.s === c.s) return;
    const prev = NAV.st[NAV.i - 1]; if (top && top.s && !c.s && prev && prev.h === c.h && !prev.s){ NAV.i--; NAV.burst = 0; navBtns(); return; }   // closing the panel is a Back
    if (top && Date.now() - NAV.burst < 900 && top.h.split('?')[0] === c.h.split('?')[0] && top.s === c.s && !now) NAV.st[NAV.i] = c;   // the same place, typed on: one entry
    else { NAV.st = NAV.st.slice(0, NAV.i + 1); NAV.st.push(c); if (NAV.st.length > 200) NAV.st.shift(); NAV.i = NAV.st.length - 1; }
    NAV.burst = Date.now(); navBtns(); };
  clearTimeout(NAV.t); if (now) go_(); else NAV.t = setTimeout(go_, 350);
}
function navBtns(){ const b = $('#navBack'), f = $('#navFwd'); if (b) b.disabled = NAV.i <= 0; if (f) f.disabled = NAV.i >= NAV.st.length - 1; }
function navApply(e){
  NAV.lock++; clearTimeout(NAV.t);
  try {
    const h = e.h.replace(/^#/, ''), t = tbParse('#' + h);
    if (!$('#sheet').hidden && !e.s) closeViewer();
    if (t && TB.mods.has(t.id)) tbOpen(t.id, t.params, t.sub, t.legacy);
    else if (h === 'clips') go('db'); else if (h === 'data' || h === 'report' || h === 'trends') go('an'); else if (!h) go('ov');
    else { try { history.replaceState(null, '', '#' + h); } catch(x){} }
    if (e.s && byId.has(e.s)) openViewer(e.s, S._sheetOrder && S._sheetOrder.includes(e.s) ? S._sheetOrder : [e.s]);
  } finally { setTimeout(() => { NAV.lock--; navBtns(); }, 0); }
}
function navGo(d){ const j = NAV.i + d; if (j < 0 || j >= NAV.st.length) return; NAV.i = j; navApply(NAV.st[j]); navBtns(); }
(function navMount(){
  const row = document.querySelector('header.mast .mast-row'); if (!row || $('#navBack')) return;
  const ic = d => `<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" focusable="false"><path d="${d}" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  row.insertAdjacentHTML('afterbegin', `<div class="nav-hist" role="group" aria-label="Page history"><button type="button" class="upd-btn nav-hb" id="navBack" title="Back (Alt+←)" aria-label="Back" disabled>${ic('M10 3 5 8l5 5')}</button><button type="button" class="upd-btn nav-hb" id="navFwd" title="Forward (Alt+→)" aria-label="Forward" disabled>${ic('M6 3l5 5-5 5')}</button></div>`);
  document.head.insertAdjacentHTML('beforeend', `<style id="navhist-css">.nav-hist{display:inline-flex;gap:6px;align-items:center;flex:none;margin-right:6px}
.nav-hist .nav-hb{padding:6px 8px;justify-content:center}.nav-hist .nav-hb:disabled{opacity:.38;cursor:default}
@media (min-width:641px){body:has(#sheet:not([hidden])) header.mast{z-index:41}}   /* Back stays clickable above the panel's scrim (the panel, later in the page, still covers its own area) */
@media (max-width:640px){.mast-row{position:relative}.nav-hist{position:absolute;top:0;right:0;margin:0}.nav-hist .nav-hb{padding:6px 7px}}</style>`);
  /* MASTHEAD-v2 (Sammy 2026-10-28: "reorganize this header so that it displays buttons for tabs cleanly"): row 1 = history + brand,
     with the action buttons at the right (or on their own row when narrow); last row = the tab bar on its own, full width, buttons
     sharing the width evenly. Phone: brand + history, the actions as a compact 2x2, then one scrolling tab strip (no wrapping) with a
     fade at the edge that has more tabs and the selected tab kept in view. --hdr follows the real height (CORNER-v2 ResizeObserver). */
  document.head.insertAdjacentHTML('beforeend', `<style id="mast2-css">
header.mast .mast-row{display:grid;grid-template-columns:auto minmax(0,1fr) auto;grid-template-areas:"hist brand acts" "tabs tabs tabs";column-gap:16px;row-gap:10px;align-items:center;padding-block:12px 10px}
header.mast .mast-row>.nav-hist{grid-area:hist;margin:0;position:static}
header.mast .mast-row>.brand{grid-area:brand}
header.mast .mast-row>.hdr-acts{grid-area:acts;justify-self:end;order:0;width:auto;margin:0;flex-wrap:nowrap}
header.mast .mast-row>nav.tabs{grid-area:tabs;order:0;margin:0;width:100%;min-width:0}
header.mast nav.tabs button{flex:1 1 0;min-width:max-content;padding:6px 12px;text-align:center}
@media (max-width:1180px){header.mast .brand .sub{display:none}}
@media (min-width:641px) and (max-width:920px){header.mast .mast-row{grid-template-columns:auto minmax(0,1fr);grid-template-areas:"hist brand" "acts acts" "tabs tabs"}
header.mast .mast-row>.hdr-acts{justify-self:start}header.mast .brand .sub{display:block}}
@media (max-width:640px){header.mast .mast-row{grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"brand hist" "acts acts" "tabs tabs";column-gap:10px;row-gap:8px;padding-block:10px 8px}
header.mast .brand img{height:40px}
header.mast .mast-row>.hdr-acts{display:grid;grid-template-columns:1fr 1fr;gap:6px;width:100%;justify-self:stretch}
header.mast .mast-row>.hdr-acts .upd-btn{justify-content:center;padding:6px 8px;font-size:var(--fs-md)}
header.mast .mast-row>nav.tabs{overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;flex-wrap:nowrap}
header.mast nav.tabs::-webkit-scrollbar{display:none}
header.mast nav.tabs button{flex:none;min-width:0;padding:6px 11px}
header.mast nav.tabs.more-r{-webkit-mask-image:linear-gradient(to right,#000 calc(100% - 30px),transparent);mask-image:linear-gradient(to right,#000 calc(100% - 30px),transparent)}
header.mast nav.tabs.more-l{-webkit-mask-image:linear-gradient(to left,#000 calc(100% - 30px),transparent);mask-image:linear-gradient(to left,#000 calc(100% - 30px),transparent)}
header.mast nav.tabs.more-l.more-r{-webkit-mask-image:linear-gradient(to right,transparent,#000 30px,#000 calc(100% - 30px),transparent);mask-image:linear-gradient(to right,transparent,#000 30px,#000 calc(100% - 30px),transparent)}}
</style>`);
  (function mastStrip(){ const nav = document.querySelector('header.mast nav.tabs'); if (!nav) return;
    const edge = () => { const m = nav.scrollWidth - nav.clientWidth > 2; nav.classList.toggle('more-r', m && nav.scrollLeft < nav.scrollWidth - nav.clientWidth - 2); nav.classList.toggle('more-l', m && nav.scrollLeft > 2); };
    const keep = () => { const b = nav.querySelector('button[aria-selected="true"]:not([hidden])'); if (b && nav.scrollWidth > nav.clientWidth){ const l = b.offsetLeft - nav.offsetLeft, r = l + b.offsetWidth;
      if (l < nav.scrollLeft + 8 || r > nav.scrollLeft + nav.clientWidth - 8) nav.scrollLeft = Math.max(0, l - (nav.clientWidth - b.offsetWidth) / 2); } edge(); };
    nav.addEventListener('scroll', edge, { passive: true }); addEventListener('resize', keep);
    try { new MutationObserver(keep).observe(nav, { subtree: true, attributes: true, attributeFilter: ['aria-selected', 'hidden'], childList: true }); } catch(e){}
    setTimeout(keep, 0); addEventListener('load', keep); })();
  $('#navBack').onclick = () => navGo(-1); $('#navFwd').onclick = () => navGo(1);
  addEventListener('keydown', e => { if (!e.altKey || e.ctrlKey || e.metaKey) return; if (e.key === 'ArrowLeft'){ e.preventDefault(); navGo(-1); } else if (e.key === 'ArrowRight'){ e.preventDefault(); navGo(1); } });
  const rs = history.replaceState.bind(history); history.replaceState = (a, b, u) => { const r = rs(a, b, u); navRecord(); return r; };
  const ov = openViewer, cv = closeViewer;
  openViewer = async function(id, order){ const r = await ov(id, order); navRecord(true); return r; };
  closeViewer = function(){ const r = cv(); navRecord(true); return r; };
  addEventListener('load', () => navRecord(true));
  /* PAGEICON-v1: the panel's meta is drawn synchronously by the first part of openViewer, so the icons go in right after */
  const ov2 = openViewer; openViewer = function(id, order){ const p = ov2(id, order); try { tbPanelIcons(id); } catch(e){ console.error(e); } return p; };
  /* RELUI-v1: stand-in records (releases, release copies) get the plain viewer; the meta is drawn synchronously, the text after */
  const ov3 = openViewer; openViewer = function(id, order){ const p = ov3(id, order); try { tbCopySheet(id); } catch(e){ console.error(e); }
    if (p && p.then) p.then(() => { try { if (S.openId === id) tbCopySheet(id); } catch(e){} }); return p; };
})();

/* ---- DATATRIM-v1 (Sammy 2026-10-28: "remove any redundancies from the data tab that are better executed in the new tabs";
   "only move ... if it adds something valuable, otherwise get rid of it"). Dropped Data cards leave no stub; their render
   targets move into a hidden holder so the shared renderers keep working. Kept / moved / dropped list: DECISIONS 2026-10-28. */
(function dataTrim(){
  const v = $('#view-an'); if (!v || v.dataset.trim) return; v.dataset.trim = '1';
  const hold = document.createElement('div'); hold.id = 'anRetired'; hold.hidden = true; v.appendChild(hold);
  const drop = el => { if (el) hold.appendChild(el); };
  const cardOf = id => { const e = $(id); return e && e.closest('.card'); };
  drop(cardOf('#bills'));            // Bills in the news -> Bills tab (stories per bill, date range, LegInfo)
  drop(cardOf('#pubBars'));          // Top outlets -> Outlets tab (sorted by stories, any date range)
  drop(cardOf('#reprint'));          // Stories that travel (Most reprinted | Which issues travel) -> Story travel tab
  drop(cardOf('#relBars'));          // Outlet relationships: "New" moved to Outlets › First story; "Loyal" dropped
  drop(v.querySelector('.rg-who'));  // Reporters with the most stories -> Reporters tab
  drop(cardOf('#gapPubs'));          // Outlets gone quiet -> Outlets › Gone quiet
  drop(cardOf('#gapHome'));          // District & Valley outlets -> Outlets › Reach = District & Valley, sorted by Last story
  /* DATAGAP-off (Sammy thread 28acc489, 2026-10-28: "eliminate this entirely"): the whole Gaps section goes to the hidden holder
     (its renderer still finds #hGap there); no stub, no link left */
  drop(v.querySelector('.rp-sec[data-rgk="gap"]') || (($('#hGap') || {}).closest && $('#hGap').closest('.rp-sec')));
  /* Other languages: By language stays; its Top outlets view goes (Outlets › Language does it) */
  const ep = $('#ethPubs'), lg = ep && ep.closest('.card');
  if (lg){ const tg = lg.querySelector('.rg-tg'); if (tg) tg.remove(); ep.hidden = true; hold.appendChild(ep); const eb = $('#ethBars'); if (eb) eb.hidden = false; }
  v.querySelectorAll('.two, .grid2').forEach(t => { if (t.children.length < 2) t.className = ''; if (!t.children.length) t.remove(); });
  v.querySelectorAll('.rp-sec').forEach(sc => { [...sc.children].forEach(c => { if (c.tagName === 'DIV' && !c.className && !c.id && !c.children.length && !c.textContent.trim()) c.remove(); }); });
})();

/* ---- registration ---- */
window.AJGTabs = Object.freeze({
  register(m){
    if (!m || typeof m.id !== 'string' || !/^[a-z][a-z0-9_]*$/.test(m.id) || TB.mods.has(m.id) || !(m.list || m.render)) return false;
    const menu = TB_MENU.find(x => x[0] === m.id);
    const mod = Object.assign({}, m, { label: String(m.label || (menu && menu[1]) || m.id), slug: m.slug || (menu && menu[2]) || m.id.replace(/_/g, '-') });
    TB.mods.set(m.id, mod);
    let b = $('#tab-tb-' + m.id);
    if (!b){ document.querySelector('nav.tabs').insertAdjacentHTML('beforeend', `<button role="tab" id="tab-tb-${m.id}" data-tab="tb" data-tb="${m.id}" aria-selected="false">${esc(mod.label)}</button>`); b = $('#tab-tb-' + m.id); }
    b.hidden = false; b.textContent = mod.label;
    if (TB.pend && (TB.pend.id === m.id || TB.pend.slug === mod.slug || (TB_OLD[TB.pend.id] === m.id)) && TB.booted){ TB.pend.id = m.id; const p = TB.pend; TB.pend = null; tbOpen(p.id, p.params, p.sub, p.legacy); }
    else if (S.tab === 'tb' && TB.cur === m.id) tbShow(true);
    /* BILLSLUG-v1 (rp-reverse 2026-10-28, thread d38d2b91 / C3): tab modules register in menu order, so a page drawn on load
       before a later module registered (e.g. a release page before bills.js: its bill numbers had no billSlug and stayed
       plain text until a Bills visit) is drawn again, and other drawn views are marked stale */
    else if (m.billSlug && TB.drawn.size){ TB.drawn.clear(); if (S.tab === 'tb' && TB.mods.has(TB.cur)) tbShow(true); }
    return true;
  },
  get ids(){ return [...TB.mods.keys()]; }
});

/* ======================= shared component 1: the search tab ======================= */
/* spec (build/tabs_contract.md §4): noun, title, cap, answer?, items | units+group, key, text, facets, columns, sort,
   row?, open ('page'|'detail'|''), detail?, step?, csvName?, copies?, legacyHook? */
/* LISTHEAD-v1 (Sammy: "make this much cleaner"): one heading and one short caption (the caption's first sentence; the rest
   under "About this list"), the answer sentence as the one line under it, no card around the header */
function tbHead(title, cap){ cap = String(cap || ''); const i = cap.search(/[.!?](\s|$)/), first = i > 0 ? cap.slice(0, i + 1) : cap, rest = i > 0 ? cap.slice(i + 1).trim() : '';
  return `<div class="tt-h1"><h2 class="sec">${title}</h2>${first ? `<span class="cap">${first}</span>` : ''}</div>${rest ? `<details class="tt-about"><summary>About this list</summary><div class="cap">${rest}</div></details>` : ''}`; }
function tbFacetList(spec){ return (spec.facets || []).map(f => Object.assign({ type: 'multi', level: 'item', order: 'count' }, f)); }
/* BLANKFACET-v1: a blank single value is "Not recorded" (listed last); an empty list stays empty (no bill is not a blank bill) */
const TB_NR = 'Not recorded';
function tbVals(f, x){ const v = f.vals ? f.vals(x) : x[f.key]; if (!Array.isArray(v)) return [v == null || v === '' ? TB_NR : v]; return v.filter(a => a != null && a !== ''); }
function tbDatesOf(f, x){ const v = f.date ? f.date(x) : x[f.key]; return (Array.isArray(v) ? v : [v]).filter(a => typeof a === 'string' && /^\d{4}/.test(a)); }
function tbOpts(f){ return f.type === 'date' ? (f.presets || TB_DATES).map(([id, label, d0]) => ({ id, label, d0: typeof d0 === 'function' ? d0() : d0 })) : (f.options || []); }
function tbTest(f, x, sel, ctx){
  if (!sel || !sel.length) return true;
  if (f.type === 'multi'){ const v = tbVals(f, x); return v.some(a => sel.includes(a)); }
  if (f.type === 'date'){
    const ds = tbDatesOf(f, x);
    if (sel[0] === 'c'){ const a = sel[1] || '', z = sel[2] || ''; return ds.some(d => (!a || d >= a) && (!z || d.slice(0, z.length) <= z)); }
    const o = tbOpts(f).find(o => o.id === sel[0]); return !o || ds.some(d => d > o.d0);
  }
  const o = tbOpts(f).find(o => o.id === sel[0]); return !o || !!o.test(x, ctx);
}
function tbState(spec, F, p){
  const st = { q: p.q || '', sort: (spec.sort || {}).key || (spec.columns[0] || {}).key, dir: (spec.sort || {}).dir || 1, f: {}, open: p.open || '' };
  if (p.sort){ const d = p.sort[0] === '-', k = d ? p.sort.slice(1) : p.sort; if (spec.columns.some(c => c.key === k)){ st.sort = k; st.dir = d ? -1 : 1; } }
  F.forEach(f => { const raw = p[f.key];
    if (raw == null) st.f[f.key] = f.def == null ? [] : [].concat(f.def);
    else if (raw === '~') st.f[f.key] = [];
    else if (f.type === 'date' && raw.startsWith('c:')){ const [a, z] = raw.slice(2).split('..'); st.f[f.key] = ['c', a || '', z || '']; }
    else st.f[f.key] = f.type === 'multi' ? raw.split('|').filter(Boolean) : [raw]; });
  return st;
}
function tbEncode(spec, F, st){
  const p = {}; if (st.q) p.q = st.q;
  const d = spec.sort || {}; if (st.sort !== (d.key || (spec.columns[0] || {}).key) || st.dir !== (d.dir || 1)) p.sort = (st.dir < 0 ? '-' : '') + st.sort;
  F.forEach(f => { const v = st.f[f.key] || [], def = f.def == null ? [] : [].concat(f.def);
    if (JSON.stringify(v) === JSON.stringify(def)) return;
    p[f.key] = !v.length ? '~' : v[0] === 'c' && f.type === 'date' ? `c:${v[1] || ''}..${v[2] || ''}` : v.join('|'); });
  if (st.open) p.open = st.open;
  return p;
}
function tbSearchTab(el, ctx, spec){
  const id = ctx.tab, F = tbFacetList(spec), cols = spec.columns || [], noun = spec.noun || ['item', 'items'];
  const st = tbState(spec, F, ctx.params);
  if (typeof spec.legacyHook === 'function') spec.legacyHook(st, ctx);
  const openF = TB.open.get(id) || TB.open.set(id, new Set(F.filter(f => f.open).map(f => f.key))).get(id);
  const fq = {}, fall = {};
  const mk = TB.memo.get(id) || {}; TB.memo.set(id, mk);
  if (mk.v !== ctx.version){ mk.v = ctx.version; mk.units = spec.units ? spec.units(ctx) : null; mk.items = spec.items ? spec.items(ctx) : null; mk.all = null; mk.uni = {}; }
  const U = mk.units, group = us => spec.group(us, ctx);
  const all = () => mk.all || (mk.all = U ? group(U) : mk.items);
  const textOf = it => (it.__tt != null ? it.__tt : (it.__tt = tbFold(spec.text ? spec.text(it, ctx) : '')));
  const keyOf = it => String(spec.key ? spec.key(it) : it.key);
  let shown = 0, res = [], counts = {}, base = [];
  const qPass = it => { const w = tbQ(st.q).split(' ').filter(Boolean); if (!w.length) return true; const t = textOf(it); return w.every(x => t.includes(x)); };
  const uF = F.filter(f => f.level === 'unit'), iF = F.filter(f => f.level !== 'unit');
  const uPass = (u, skip) => uF.every(f => f.key === skip || tbTest(f, u, st.f[f.key], ctx));
  const iPass = (it, skip) => iF.every(f => f.key === skip || tbTest(f, it, st.f[f.key], ctx)) && qPass(it);
  function universe(f){   // every value a multi facet can take (zero counts included)
    if (mk.uni[f.key]) return mk.uni[f.key];
    const s = new Set(); (f.level === 'unit' ? U : all()).forEach(x => tbVals(f, x).forEach(v => s.add(v)));
    return (mk.uni[f.key] = [...s]);
  }
  function compute(){
    base = U ? group(U.filter(u => uPass(u))) : all();
    res = base.filter(it => iPass(it));
    counts = {};
    F.forEach(f => { if (isOpen(f)) countFacet(f); });
    sortRes();
  }
  /* counts are computed only for open facets (a closed facet's summary shows how many values are on, not counts) */
  const isOpen = f => openF.has(f.key) || (st.f[f.key] || []).length > 0;
  function countFacet(f){
    { const c = new Map(); counts[f.key] = c;
      if (f.level === 'unit'){
        const Uf = U.filter(u => uPass(u, f.key));
        if (f.type === 'multi'){ const by = new Map(); Uf.forEach(u => tbVals(f, u).forEach(v => (by.get(v) || by.set(v, []).get(v)).push(u)));
          by.forEach((us, v) => c.set(v, group(us).filter(it => iPass(it)).length)); }
        else tbOpts(f).forEach(o => c.set(o.id, group(Uf.filter(u => tbTest(f, u, [o.id], ctx))).filter(it => iPass(it)).length));
      } else {
        const B = base.filter(it => iPass(it, f.key));
        if (f.type === 'multi') B.forEach(it => tbVals(f, it).forEach(v => c.set(v, (c.get(v) || 0) + 1)));
        else tbOpts(f).forEach(o => c.set(o.id, B.filter(it => tbTest(f, it, [o.id], ctx)).length));
      }
      if (f.type !== 'multi'){ const allN = f.level === 'unit' ? group(U.filter(u => uPass(u, f.key))).filter(it => iPass(it)).length : base.filter(it => iPass(it, f.key)).length; c.set('', allN); }
    }
  }
  function sortRes(){
    const col = cols.find(c => c.key === st.sort) || cols[0], dir = st.dir;
    const val = it => col ? (col.sort ? col.sort(it) : col.val ? col.val(it) : it[col.key]) : 0;
    const idx = new Map(res.map((it, i) => [it, i]));
    res.sort((a, b) => { let x = val(a), y = val(b); const ex = x == null || x === '', ey = y == null || y === '';
      if (ex || ey) return (ex - ey) || idx.get(a) - idx.get(b);
      if (typeof x === 'string') { x = x.toLowerCase(); y = String(y).toLowerCase(); }
      return (x < y ? -1 : x > y ? 1 : 0) * dir || idx.get(a) - idx.get(b); });
  }
  const step = () => tbPhone() ? ((spec.step && spec.step.phone) || 25) : ((spec.step && spec.step.desk) || 100);
  const save = () => ctx.setParams(tbEncode(spec, F, st));
  const fLabel = (f, v) => f.label_ ? f.label_(v) : f.type === 'multi' ? v : ((tbOpts(f).find(o => o.id === v) || {}).label || v);
  const search = '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" focusable="false" style="color:var(--ink-3);flex:none"><circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M10.4 10.4 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
  el.innerHTML = `<div class="tt${spec.row ? ' tt-rowlist' : ''}" data-tt-id="${id}">
  <div class="tt-head">${tbHead(spec.title || esc(ctx.mod.label), spec.cap)}<div class="tt-ans" hidden></div></div>
  <div class="grid-clips">
    <aside class="rail tt-rail" aria-label="Filters"><div class="rail-head"><h2>Filters</h2><span style="display:flex;gap:14px;align-items:center"><button class="linkbtn" data-tt="clear">Clear all</button><button class="btn" data-tt="done" style="padding:5px 12px">Done</button></span></div><div class="tt-facets"></div></aside>
    <div class="pane">
      <div class="toolbar tt-bar"><span class="fgroup"><button class="btn filters-toggle tt-ft" data-tt="rail">Filters</button></span>
        <label class="search">${search}<input type="search" class="tt-q" placeholder="${esc(spec.placeholder || 'Search')}" aria-label="${esc(spec.placeholder || 'Search')}" autocomplete="off" value="${esc(st.q)}"></label>
        <select class="sel tt-sort" aria-label="Sort by">${cols.filter(c => c.sortable !== false).map(c => `<option value="${c.key}">Sort: ${esc(c.label.toLowerCase())}</option>`).join('')}</select>
        <details class="dlmenu tt-exp"><summary class="btn">Export</summary><div class="menu">
          ${(spec.copies || []).map((c, i) => `<button data-tt="copyx" data-i="${i}"><b>${esc(c.label)}</b><span>${esc(c.sub || '')}</span></button>`).join('')}
          <button data-tt="copy"><b>Copy list</b><span>Every ${esc(noun[0])} listed, as rows to paste into a spreadsheet</span></button>
          <button data-tt="csv"><b>Download CSV</b><span>Every ${esc(noun[0])} listed, with every column</span></button></div></details></div>
      <div class="chips tt-chips"></div>
      <div class="card tt-list"></div>
      <div class="tt-extra"${spec.extra ? '' : ' hidden'}></div>
    </div></div>
  <div class="scrim tt-scrim" hidden></div></div>`;
  const $$ = s => el.querySelector(s), rail = $$('.tt-rail'), scrim = $$('.tt-scrim');
  const optHtml = (f, v, n, on, type, lab) => { lab = lab == null ? fLabel(f, v) : lab; return `<label class="opt ${n || on ? '' : 'zero'}"><input type="${type}" ${type === 'radio' ? `name="tt-${id}-${f.key}"` : ''} data-ttf="${f.key}" value="${esc(v)}" ${on ? 'checked' : ''}>${f.sw && v ? `<span class="sw" style="background:${f.sw(v)}"></span>` : ''}<span class="lab" title="${esc(lab)}">${esc(lab)}${f.note && v ? `<small class="bname"> ${esc(f.note(v) || '')}</small>` : ''}</span><span class="n">${n == null ? '' : fmt(n)}</span></label>`; };
  function drawFacets(){
    $$('.tt-facets').innerHTML = F.map(f => {
      const sel = st.f[f.key] || [], c = counts[f.key] || new Map(); let body = '', on = 0;
      if (f.type === 'multi'){
        let vs = universe(f).slice(); const q = tbFold(fq[f.key] || '');
        if (Array.isArray(f.order)) vs = f.order.filter(v => vs.includes(v)).concat(vs.filter(v => !f.order.includes(v)));
        else if (typeof f.order === 'function') vs.sort(f.order);
        else if (f.order === 'alpha') vs.sort((a, b) => String(fLabel(f, a)).localeCompare(fLabel(f, b)));
        else vs.sort((a, b) => (c.get(b) || 0) - (c.get(a) || 0) || String(a).localeCompare(b));
        vs = vs.filter(v => v !== TB_NR).concat(vs.filter(v => v === TB_NR));   /* BLANKFACET-v1 */
        const n0 = vs.length;
        if (q) vs = vs.filter(v => tbFold(fLabel(f, v) + ' ' + (f.note ? f.note(v) : '')).includes(q));
        const lim = f.limit || (f.search ? 8 : 0), cut = lim && !q && !fall[f.key] ? vs.slice(0, lim) : vs;
        const show = sel.filter(v => !cut.includes(v)).concat(cut); on = sel.length;
        body = (f.search && n0 > (lim || 8) ? `<input class="fsearch" data-ttq="${f.key}" type="search" placeholder="Find one of ${fmt(n0)}" aria-label="Find ${esc(f.label)}" value="${esc(fq[f.key] || '')}">` : '')
          + show.map(v => optHtml(f, v, c.get(v) || 0, sel.includes(v), 'checkbox')).join('')
          + (lim && !q && n0 > lim ? `<button class="linkbtn" data-ttmore="${f.key}">${fall[f.key] ? 'Show fewer' : 'Show all ' + fmt(n0)}</button>` : '');
      } else {
        const cur = sel[0] || ''; on = cur ? 1 : 0;
        body = optHtml(f, '', c.get(''), !cur, 'radio', f.any || 'Any')
          + tbOpts(f).map(o => optHtml(f, o.id, c.get(o.id) || 0, cur === o.id, 'radio')).join('')
          + (f.type === 'date' ? `<div class="tt-cust"><input type="date" data-ttc0="${f.key}" aria-label="From" value="${cur === 'c' ? esc(sel[1]) : ''}"><span>to</span><input type="date" data-ttc1="${f.key}" aria-label="To" value="${cur === 'c' ? esc(sel[2]) : ''}"><button class="btn" data-tt="cust" data-k="${f.key}" style="padding:3px 10px">Apply</button></div>` : '');
      }
      return `<details class="facet" data-ttfacet="${f.key}" ${openF.has(f.key) || on ? 'open' : ''}><summary>${esc(f.label)}<small>${on ? (f.type === 'multi' ? on + ' on' : '1 on') : ''}</small></summary><div class="body">${f.hint ? `<div class="hint">${f.hint}</div>` : ''}${body}</div></details>`;
    }).join('');
  }
  function chipList(){ const out = []; if (st.q) out.push(['q', '', 'Search', `“${st.q}”`]);
    F.forEach(f => { const s = st.f[f.key] || []; if (!s.length) return;
      if (f.type === 'multi') s.forEach(v => out.push([f.key, v, f.label, fLabel(f, v)]));
      else if (s[0] === 'c') out.push([f.key, 'c', f.label, s[1] && s[2] ? `${s[1]} – ${s[2]}` : s[1] ? `Since ${s[1]}` : `Through ${s[2]}`]);
      else out.push([f.key, s[0], f.label, fLabel(f, s[0])]); });
    return out; }
  function drawChips(){ const ch = chipList();
    $$('.tt-ft').innerHTML = 'Filters' + (ch.length ? ` <span class="fcount">${ch.length}</span>` : '');
    $$('.tt-chips').innerHTML = `<span class="result-line"><b style="color:var(--ink)">${fmt(res.length)}</b> of ${fmt(all().length)} ${esc(noun[1])}</span>`
      + ch.map(([k, v, l, t]) => `<span class="chip"><span class="k">${esc(l)}</span><span>${esc(t)}</span><button aria-label="Remove ${esc(l)} filter" data-ttrm="${esc(k)}" data-v="${esc(v)}">${IC.xs}</button></span>`).join('')
      + (ch.length ? ' <button class="linkbtn" data-tt="clear">Clear all</button>' : ''); }
  function drawList(){
    const box = $$('.tt-list'), lim = Math.min(res.length, Math.max(shown, step()));
    const ans = $$('.tt-ans'); if (spec.answer){ const t = spec.answer(res, st, ctx); ans.hidden = !t; ans.textContent = t || ''; }
    const ss = $$('.tt-sort'); if (ss) ss.value = st.sort;
    if (!res.length){ box.innerHTML = `<div class="empty tt-empty">${spec.empty ? spec.empty(st) : 'Nothing matches these filters.'} <button class="linkbtn" data-tt="clear">Clear all filters</button></div>`; return; }
    const rest = res.length - lim, more = rest > 0 ? `<div class="tt-more"><button class="btn" data-tt="more">${tbPhone() ? 'Show ' + fmt(Math.min(rest, step())) + ' more' : 'Show all ' + fmt(res.length)}</button></div>` : '';
    const slice = res.slice(0, lim);
    if (spec.row){
      box.innerHTML = `<div class="tt-rows clip-list">${slice.map(it => `<div class="tt-r${keyOf(it) === st.open ? ' tt-on' : ''}" data-ttk="${esc(keyOf(it))}">${spec.row(it, ctx)}</div>`).join('')}</div>` + more;
    } else {
      const head = cols.map(c => { const on = st.sort === c.key;
        return `<th${c.num ? ' class="num"' : ''}>${c.sortable === false ? `<button disabled>${esc(c.label)}</button>` : `<button data-ttsort="${c.key}"${on ? ` data-dir="${st.dir > 0 ? '↑' : '↓'}" aria-sort="${st.dir > 0 ? 'ascending' : 'descending'}"` : ''}>${esc(c.label)}</button>`}</th>`; }).join('');
      box.innerHTML = `<div class="tablewrap"><table class="db tt-tab"><thead><tr>${head}</tr></thead><tbody>${slice.map(it => `<tr data-ttk="${esc(keyOf(it))}" tabindex="0"${keyOf(it) === st.open ? ' class="tt-on"' : ''}>${cols.map((c, i) => `<td class="${i === 0 ? 'tt-name ' : ''}${c.num ? 'num ' : ''}${c.cls || ''}" data-l="${esc(c.label)}">${c.cell ? c.cell(it, ctx) : esc(c.val ? c.val(it) : it[c.key])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>` + more;
    }
    if (st.open && spec.open === 'detail' && spec.detail){
      const it = res.find(x => keyOf(x) === st.open), row = box.querySelector(`[data-ttk="${CSS.escape(st.open)}"]`);
      if (it && row){ let host;
        if (row.tagName === 'TR'){ row.insertAdjacentHTML('afterend', `<tr class="tt-det"><td colspan="${cols.length}"><div class="tt-detail"></div></td></tr>`); host = row.nextElementSibling.querySelector('.tt-detail'); }
        else { row.insertAdjacentHTML('beforeend', '<div class="tt-detail"></div>'); host = row.querySelector('.tt-detail'); }
        try { spec.detail(it, host, ctx); } catch(e){ console.error(e); host.innerHTML = `<div class="empty">Could not draw the details: ${esc(e.message || e)}</div>`; }
      }
    }
  }
  function drawExtra(){ if (!spec.extra) return; try { spec.extra($$('.tt-extra'), res.slice(), ctx); } catch(e){ console.error(e); } }
  function draw(keepShown){ compute(); if (!keepShown) shown = 0;
    if (st.open){ const at = res.findIndex(it => keyOf(it) === st.open); if (at >= Math.max(shown, step())) shown = at + 1; }
    drawFacets(); drawChips(); drawList(); drawExtra(); save(); }
  const csvCols = () => cols.filter(c => c.csv !== false).map(c => [c.csvLabel || c.label, it => typeof c.csv === 'function' ? c.csv(it) : c.val ? c.val(it) : it[c.key]]).concat(spec.csvExtra || []);
  const openRail = on => { rail.classList.toggle('open', on); scrim.hidden = !on; };
  el.addEventListener('input', e => {
    const t = e.target;
    if (t.matches('.tt-q')){ clearTimeout(TB._qT); TB._qT = setTimeout(() => { st.q = t.value.trim(); st.open = ''; draw(); }, 120); return; }
    if (t.dataset.ttq){ fq[t.dataset.ttq] = t.value; const k = t.dataset.ttq, pos = t.selectionStart; drawFacets(); const i = el.querySelector(`[data-ttq="${k}"]`); if (i){ i.focus(); try { i.setSelectionRange(pos, pos); } catch(x){} } }
  });
  el.addEventListener('change', e => {
    const t = e.target;
    if (t.matches('.tt-sort')){ const c = cols.find(x => x.key === t.value); st.sort = t.value; st.dir = (c && c.dir) || 1; draw(true); return; }
    if (t.dataset.ttf){ const f = F.find(x => x.key === t.dataset.ttf);
      if (f.type === 'multi'){ const s = st.f[f.key] = (st.f[f.key] || []).slice(); if (t.checked){ if (!s.includes(t.value)) s.push(t.value); } else s.splice(s.indexOf(t.value), 1); }
      else st.f[f.key] = t.value ? [t.value] : [];
      st.open = ''; draw(); }
  });
  el.addEventListener('toggle', e => { const d = e.target.closest && e.target.closest('details[data-ttfacet]'); if (!d) return; const k = d.dataset.ttfacet;
    if (d.open){ openF.add(k); if (!counts[k]){ countFacet(F.find(f => f.key === k)); drawFacets(); } } else openF.delete(k); }, true);
  el.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches && e.target.matches('tr[data-ttk]')){ e.preventDefault(); e.target.click(); }
    if (e.key === 'Escape' && rail.classList.contains('open')) openRail(false); });
  el.addEventListener('click', e => {
    const t = e.target, b = t.closest('[data-tt]'), act = b && b.dataset.tt;
    if (act === 'rail'){ openRail(true); return; }
    if (act === 'done' || t === scrim){ openRail(false); return; }
    if (act === 'clear'){ st.q = ''; $$('.tt-q').value = ''; F.forEach(f => st.f[f.key] = []); st.open = ''; draw(); return; }
    if (act === 'more'){ shown = tbPhone() ? Math.max(shown, step()) + step() : 1e9; drawList(); return; }
    if (act === 'csv'){ b.closest('details').open = false; ctx.saveFile(spec.csvName ? spec.csvName(st, ctx) : `AJG ${noun[1]} ${TODAY}.csv`, insCsv(res, csvCols())); return; }
    if (act === 'copy'){ b.closest('details').open = false; const cc = csvCols(); ctx.copy([cc.map(c => c[0]).join('\t')].concat(res.map(it => cc.map(c => tsvCell(c[1](it))).join('\t'))).join('\n'), `Copied ${pl(res.length, noun[0], noun[1])}`); return; }
    if (act === 'copyx'){ b.closest('details').open = false; const c = spec.copies[+b.dataset.i]; ctx.copy(c.text(res, st, ctx), c.ok ? c.ok(res) : `Copied ${pl(res.length, noun[0], noun[1])}`, b); return; }
    if (act === 'cust'){ const k = b.dataset.k, a = el.querySelector(`[data-ttc0="${k}"]`).value, z = el.querySelector(`[data-ttc1="${k}"]`).value;
      if (!a && !z){ toast('Pick a from date, a to date, or both.'); return; } st.f[k] = ['c', a && z && a > z ? z : a, a && z && a > z ? a : z]; st.open = ''; draw(); return; }
    const m = t.closest('[data-ttmore]'); if (m){ fall[m.dataset.ttmore] = !fall[m.dataset.ttmore]; drawFacets(); return; }
    const rm = t.closest('[data-ttrm]'); if (rm){ const k = rm.dataset.ttrm;
      if (k === 'q'){ st.q = ''; $$('.tt-q').value = ''; } else { const f = F.find(x => x.key === k); st.f[k] = f.type === 'multi' ? (st.f[k] || []).filter(v => v !== rm.dataset.v) : []; }
      st.open = ''; draw(); return; }
    const so = t.closest('[data-ttsort]'); if (so){ const k = so.dataset.ttsort, c = cols.find(x => x.key === k);
      if (st.sort === k) st.dir = -st.dir; else { st.sort = k; st.dir = (c && c.dir) || 1; } draw(true); return; }
    const row = t.closest('[data-ttk]');
    if (row && !t.closest('.tt-detail') && !t.closest('a[href],.cpb,input,select,[data-author],[data-pub],[data-fk],[data-bill],[data-tb-go],[data-tbstory],[data-tbclip]') && (!t.closest('button') || t.closest('.tt-open,.tt-name .linkbtn'))){
      const k = row.dataset.ttk; e.stopPropagation(); e.preventDefault();
      if (spec.open === 'page' && ctx.mod.page){ const it = res.find(x => keyOf(x) === k); if (it) ctx.openPage(ctx.mod.page.slug ? ctx.mod.page.slug(it, ctx) : k); return; }
      if (spec.open === 'detail'){ st.open = st.open === k ? '' : k; drawList(); save(); const r2 = el.querySelector(`[data-ttk="${CSS.escape(k)}"]`); if (r2 && st.open && r2.scrollIntoView) r2.scrollIntoView({ block: 'nearest' }); return; }
      if (spec.onRow){ const it = res.find(x => keyOf(x) === k); if (it) spec.onRow(it, ctx); }
    }
  });
  draw();
  if (st.open){ const r2 = el.querySelector(`[data-ttk="${CSS.escape(st.open)}"]`); if (r2) setTimeout(() => { try { r2.scrollIntoView({ block: 'center' }); } catch(x){} }, 0); }
  return { state: st, results: () => res.slice(), redraw: () => draw(true) };
}

/* ======================= EMBEDROWS-v1: a tab's own rows embedded on another page ======================= */
/* Sammy (preview comment cb3058b3, "pull the reporter profiles from the reporter tab ... Apply throughout"): where a page
   lists reporters or outlets, it shows the Reporters / Outlets tab's own rows (same cells), filtered to that page: sortable,
   the first 10 then "Show all", a compact search when there are more than 10, a name opens its page. The tab's item-level
   embed filters apply (f.mini; Reporters: people only); dates do not (a page covers all its stories). o.person(p, u): which
   people of a story count (AFFIL-v1: an outlet's reporters are the people whose own outlet it is).
   o = { tab, title, cap?, unit(u) (which stories count, two-level tabs), item(it)?, cols: [column keys], limit } */
const TB_SEARCH_IC = '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" focusable="false" style="color:var(--ink-3);flex:none"><circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M10.4 10.4 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
function tbMiniList(host, tab, o){
  const m = TB.mods.get(tab); if (!host || !m || !m.list) return 0;
  o = o || {}; const spec = m.list, c = tbCtx(tab), F = tbFacetList(spec);
  let items = spec.units ? spec.group(spec.units(c).filter(o.unit || (() => true)), c, { person: o.person }) : (spec.items(c) || []).slice();
  /* DEFCLEAR-v1: the tabs open with no filters; an embedded list keeps its own item filter (f.mini, e.g. Reporters: people only) */
  F.filter(f => f.level !== 'unit' && (f.mini != null || f.def != null) && f.type !== 'date').forEach(f => { items = items.filter(it => tbTest(f, it, [].concat(f.mini != null ? f.mini : f.def), c)); });
  if (o.item) items = items.filter(o.item);
  if (!items.length){ host.innerHTML = ''; return 0; }
  const cols = (spec.columns || []).filter(x => !o.cols || o.cols.includes(x.key)), noun = spec.noun || ['item', 'items'];
  const keyOf = it => String(spec.key ? spec.key(it) : it.key), LIM = o.limit || 10;
  const st = { sort: (spec.sort || {}).key, dir: (spec.sort || {}).dir || 1, all: false, q: '' };
  if (!cols.some(x => x.key === st.sort)){ st.sort = cols[0].key; st.dir = cols[0].dir || 1; }
  const tt = new Map(), textOf = it => tt.has(it) ? tt.get(it) : tt.set(it, tbFold(spec.text ? spec.text(it, c) : '')).get(it);
  host.innerHTML = `<div class="tt tb-mini" data-tb-mini="${esc(tab)}"><div class="tb-mini-h"><h2 class="sec">${esc(o.title || m.label)} <span class="tb-mini-n">${fmt(items.length)}</span></h2>`
    + (items.length > LIM ? `<label class="search tb-mini-q">${TB_SEARCH_IC}<input type="search" placeholder="Find one of ${fmt(items.length)}" aria-label="Find ${esc(noun[0])}" autocomplete="off"></label>` : '')
    + `</div>${o.cap ? `<div class="cap">${o.cap}</div>` : ''}<div class="card tb-mini-list"></div></div>`;
  const box = host.querySelector('.tb-mini-list');
  function draw(){
    const w = tbQ(st.q).split(' ').filter(Boolean), res = items.filter(it => !w.length || w.every(x => textOf(it).includes(x)));
    const col = cols.find(x => x.key === st.sort) || cols[0], val = it => col.sort ? col.sort(it) : col.val ? col.val(it) : it[col.key], idx = new Map(res.map((it, i) => [it, i]));
    res.sort((a, b) => { let x = val(a), y = val(b); const ex = x == null || x === '', ey = y == null || y === '';
      if (ex || ey) return (ex - ey) || idx.get(a) - idx.get(b);
      if (typeof x === 'string'){ x = x.toLowerCase(); y = String(y).toLowerCase(); }
      return (x < y ? -1 : x > y ? 1 : 0) * st.dir || idx.get(a) - idx.get(b); });
    const lim = st.all || w.length ? res.length : Math.min(res.length, LIM);
    const head = cols.map(x => { const on = st.sort === x.key;
      return `<th${x.num ? ' class="num"' : ''}>${x.sortable === false ? `<button disabled>${esc(x.label)}</button>` : `<button data-tbmsort="${x.key}"${on ? ` data-dir="${st.dir > 0 ? '↑' : '↓'}" aria-sort="${st.dir > 0 ? 'ascending' : 'descending'}"` : ''}>${esc(x.label)}</button>`}</th>`; }).join('');
    box.innerHTML = !res.length ? `<div class="empty tt-empty">No ${esc(noun[1])} match.</div>`
      : `<div class="tablewrap"><table class="db tt-tab"><thead><tr>${head}</tr></thead><tbody>${res.slice(0, lim).map(it => `<tr data-tbmk="${esc(keyOf(it))}" tabindex="0">${cols.map((x, i) => `<td class="${i === 0 ? 'tt-name ' : ''}${x.num ? 'num ' : ''}${x.cls || ''}" data-l="${esc(x.label)}">${x.cell ? x.cell(it, c) : esc(x.val ? x.val(it) : it[x.key])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`
        + (res.length > lim ? `<div class="tt-more"><button class="btn" data-tbm="all">Show all ${fmt(res.length)}</button></div>` : '');
  }
  host.addEventListener('input', e => { if (e.target.matches('.tb-mini-q input')){ st.q = e.target.value.trim(); draw(); } });
  host.addEventListener('click', e => { const t = e.target;
    const so = t.closest('[data-tbmsort]'); if (so){ e.stopPropagation(); const k = so.dataset.tbmsort, x = cols.find(q => q.key === k); if (st.sort === k) st.dir = -st.dir; else { st.sort = k; st.dir = (x && x.dir) || 1; } draw(); return; }
    if (t.closest('[data-tbm="all"]')){ e.stopPropagation(); st.all = true; draw(); return; }
    const row = t.closest('tr[data-tbmk]');
    if (row && !t.closest('a[href],.cpb,input,select,[data-author],[data-pub],[data-fk],[data-bill],[data-tb-go],[data-tbstory],[data-tbclip]') && (!t.closest('button') || t.closest('.tt-open'))){
      e.stopPropagation(); e.preventDefault(); const it = items.find(x => keyOf(x) === row.dataset.tbmk); if (it && m.page) tbOpen(tab, {}, m.page.slug ? m.page.slug(it, c) : keyOf(it)); } });
  host.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches && e.target.matches('tr[data-tbmk]')){ e.preventDefault(); e.target.click(); } });
  draw(); return items.length;
}

/* ======================= shared component 2: the entity page ======================= */
/* module.page = { slug(item, ctx), find(sub, ctx) -> entity | null, spec(entity, ctx) -> { kicker, title, sub, facts:[[label, html]],
   extra, rows (tracker stories), clips (Clips filters for "Open in Clips"), noun, placeholder, backLabel } } */
const TB_WHEN = () => WHEN.filter(w => w[0] !== 'pick');
const tbWhenLabel = w => { const x = TB_WHEN().find(v => v[0] === w); if (x) return x[1]; if (!String(w).startsWith('c:')) return w;
  const [a, z] = w.slice(2).split('..'), lb = d => !d ? '' : d.length === 7 ? monthName(d) : dateLabel({ date: d.slice(0, 10), prec: 'day' });
  if (a && z && z === a + '-99') return lb(a); if (a && z && /-99$/.test(z)) return `${lb(a)} – ${lb(z.slice(0, 7))}`; return a && z ? `${lb(a)} – ${lb(z)}` : a ? `Since ${lb(a)}` : `Through ${lb(z)}`; };
/* ---- the entity page's chart: Data's "Coverage over time" (timeChart) over the entity's stories ---- */
/* CHARTFIX-v1 (Sammy, preview): the default view is the plain count (no overlaid line); the tone line appears only in the
   "Tone over time" view (tone mix by period + the average on its own labelled axis) */
const TB_QV = { volume: { bk: 'none', meas: 'stories', show: 'n', tl: false, avg: false }, issues: { bk: 'topic', meas: 'stories', show: 'n', tl: false },
  tone: { bk: 'tone', meas: 'stories', show: 'n', tl: true, avg: false }, reach: { bk: 'reach', show: 'pct' }, formats: { bk: 'media', show: 'pct' },
  role: { bk: 'role', show: 'n' }, reprints: { bk: 'none', meas: 'all', show: 'n' } };
const TB_CHART_KEYS = { iv: 'ci', bk: 'cb', only: 'co', meas: 'cm', show: 'cs', from: 'cf', avg: 'ca', tl: 'ct', qv: 'cq' };
function tbChartState(p, rows){
  const ys = rows.filter(r => r.date).map(r => +r.date.slice(0, 4)).filter(Boolean), y0 = ys.length ? Math.min(...ys) : +TODAY.slice(0, 4), y1 = ys.length ? Math.max(...ys) : y0;
  const def = { iv: y1 - y0 <= 2 ? 'month' : y1 - y0 <= 8 ? 'quarter' : 'year', bk: 'none', only: '', meas: 'stories', show: 'n', from: String(y0), avg: false, tl: false, qv: 'volume', y0 };
  const c = Object.assign({}, def); c.def = def;
  Object.entries(TB_CHART_KEYS).forEach(([k, u]) => { if (p[u] == null) return; c[k] = k === 'avg' || k === 'tl' ? p[u] === '1' : p[u]; });
  return c;
}
function tbChartEnc(c){ const q = {}; Object.entries(TB_CHART_KEYS).forEach(([k, u]) => { const v = c[k], d = c.def[k]; if (v === d) return; q[u] = typeof v === 'boolean' ? (v ? '1' : '0') : String(v); }); return q; }
function tbChartCard(rows){
  const sel = (k, label, opts) => `<label>${label}<select data-tbc="${k}">${opts.map(([v, l]) => `<option value="${v}">${esc(l)}</option>`).join('')}</select></label>`;
  return `<div class="card chartcard tbe-chart"><h2 class="sec tbe-ctitle">Coverage over time</h2><div class="cap tbe-ccap"></div><div class="legend tbe-cleg"></div><div class="chart tbe-cchart"></div><div class="tbe-cnote" hidden></div>
    <details class="opts tbe-copts"><summary>Chart options</summary><div class="quick tbe-quick" role="group" aria-label="Quick views"><span class="ql">Quick views</span>
    ${[['volume', 'Coverage volume'], ['issues', 'Issues over time'], ['tone', 'Tone over time'], ['reach', 'National vs. local'], ['formats', 'Medium and format over time'], ['role', 'Headlines vs. mentions'], ['reprints', 'With reprints']].map(([k, l]) => `<button type="button" data-tbqv="${k}">${l}</button>`).join('')}</div>
    <div class="an-controls">${sel('iv', 'Group by', [['month', 'Month'], ['quarter', 'Quarter'], ['year', 'Year']])}
    ${sel('bk', 'Color by', [['topic', 'Issue'], ['reach', 'Reach'], ['media', 'Medium'], ['fmt', 'Format'], ['role', 'How Gabriel appears'], ['pub', 'Outlet'], ['tone', 'Tone'], ['none', 'Nothing']])}
    <label>Show only<select data-tbc="only"><option value="">All of them</option></select></label>
    ${sel('meas', 'Count', [['stories', 'Stories'], ['all', 'Stories plus reprints']])}${sel('show', 'Show', [['n', 'Number'], ['pct', 'Share of total']])}
    <label>Starting<select data-tbc="from"></select></label>
    <label class="chk"><input type="checkbox" data-tbc="avg">Average line</label></div></details>
    <details class="dt"><summary>Show the numbers</summary><div class="tbe-ctable" style="overflow-x:auto"></div></details></div>`;
}
function tbChartSync(el, c){
  const f = el.querySelector('.tbe-chart select[data-tbc="from"]'); if (f && !f.options.length) f.innerHTML = YEARS.map(y => `<option value="${y}">${y}</option>`).join('');
  el.querySelectorAll('.tbe-chart [data-tbc]').forEach(x => { const k = x.dataset.tbc; if (k === 'only') return; if (x.type === 'checkbox') x.checked = !!c[k]; else x.value = String(c[k]); });
  el.querySelectorAll('.tbe-chart [data-tbqv]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.tbqv === c.qv)));
}
/* the tone average per period on a right-hand scale (Very negative -2 ... Very positive +2), rated stories only */
function tbToneLine(g){
  const by = new Map(); g.rows.forEach(r => { if (!Object.prototype.hasOwnProperty.call(TB_PTS, r.tone)) return; const k = g.key(r); if (k == null) return; const a = by.get(k) || by.set(k, [0, 0]).get(k); a[0] += TB_PTS[r.tone]; a[1]++; });
  const MINN = 3; let mx = 0; by.forEach(a => { if (a[1] >= MINN) mx = Math.max(mx, Math.abs(a[0] / a[1])); });   // periods with 3+ rated stories only
  const T = niceScale(mx, 'tone').max || 0.5;   // AXIS-v1: symmetric around 0, zoomed to the data (at least +-0.5)
  const y = v => g.m.t + g.ih * (1 - (v + T) / (2 * T)); let d = '', dots = '';
  let prev = -2;
  g.buckets.forEach((b, i) => { const a = by.get(b); if (!a || a[1] < MINN) return; const v = a[0] / a[1], x = (g.m.l + i * g.band + g.band / 2).toFixed(1);
    d += `${d && prev === i - 1 ? 'L' : 'M'}${x},${y(v).toFixed(1)}`; prev = i;   /* a gap where a period has fewer than 3 rated stories */ dots += `<circle class="tb-tone" cx="${x}" cy="${y(v).toFixed(1)}" r="3" fill="var(--accent)" data-b="${esc(b)}" data-tv="${(Math.round(v * 100) / 100).toFixed(2)}" data-tn="${a[1]}"><title>${esc(b)}: average tone ${esc(tbToneText(v, a[1]))} (${a[1]} rated ${a[1] === 1 ? 'story' : 'stories'})</title></circle>`; });
  if (!d) return '';
  const z = y(0).toFixed(1), xr = g.W - g.m.r, lab = v => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(T < 1 ? 1 : 0);
  const title = `<text class="tb-tax" x="${xr}" y="${(g.m.t - 4).toFixed(1)}" text-anchor="end" style="fill:var(--accent);font-size:var(--fs-xs)">Average tone</text>`;
  const ticks = [T, -T].map(v => `<text class="tb-tax" x="${xr}" y="${(y(v) + (v > 0 ? 11 : -3)).toFixed(1)}" text-anchor="end" style="fill:var(--accent);font-size:var(--fs-xs)">${lab(v)}</text>`).join('');
  return `<line x1="${g.m.l}" x2="${xr}" y1="${z}" y2="${z}" stroke="var(--accent)" stroke-dasharray="2 4" stroke-width="1" opacity=".55"></line><text x="${xr}" y="${(+z - 4).toFixed(1)}" text-anchor="end" style="fill:var(--accent);font-size:var(--fs-xs)">Neutral (0)</text>${title}${ticks}<g class="tb-tscale" data-t="${T}"></g><path d="${d}" fill="none" stroke="var(--accent)" stroke-width="2"></path>${dots}`;
}
function tbChartDraw(el, c, rows, nAll, pick){
  const q = s => el.querySelector('.tbe-chart ' + s), note = q('.tbe-cnote'), chart = q('.tbe-cchart');
  if (!q('.tbe-cchart')) return null;
  if (nAll <= 3){   // too few stories for a chart: a plain line instead
    ['.tbe-cchart', '.tbe-copts', '.tbe-cleg', '.dt'].forEach(k => { const x = q(k); if (x) x.hidden = true; });
    q('.tbe-ctitle').textContent = 'Coverage over time'; q('.tbe-ccap').textContent = '';
    note.hidden = false; note.className = 'cap tbe-cnote';
    note.textContent = nAll ? `Only ${pl(nAll, 'story', 'stories')}, so no chart: ${rows.slice().sort((a, b) => a.date.localeCompare(b.date)).map(r => dateLabel(r)).join('; ')}.` : 'No stories.';
    return null;
  }
  /* CHARTRULE-v1 (DECISIONS 2026-10-28): no chart that would be a single bar, or with every story in one period: a sentence
     instead. A tone line needs 2 or more periods with 3+ rated stories, else a note and no line. Data's own charts are unaffected. */
  const per = r => { const d = String(r.date || ''); if (!/^\d{4}/.test(d) || +d.slice(0, 4) < +c.from) return null;
    return c.iv === 'year' ? d.slice(0, 4) : c.iv === 'quarter' ? d.slice(0, 4) + ' Q' + (Math.floor((+d.slice(5, 7) || 1) - 1) / 3 + 1 | 0) : d.slice(0, 7); };
  const ps = new Map(); rows.forEach(r => { const k = per(r); if (k) ps.set(k, (ps.get(k) || 0) + 1); });
  const parts = ['.tbe-cchart', '.tbe-cleg', '.dt'];
  if (!ps.size){   /* nothing passes the filters: Data's empty state in the chart's place (AXIS-v1), not a broken axis */
    parts.forEach(k => { const x = q(k); if (x) x.hidden = k !== '.tbe-cchart'; }); q('.tbe-ccap').textContent = ''; note.hidden = true; note.textContent = '';
    chart.innerHTML = `<div class="empty">${rows.length ? 'No dated stories in this range, so there is nothing to chart.' : 'No stories match these filters, so there is nothing to chart.'}</div>`; chart.onclick = chart.onmousemove = null;
    return null;
  }
  if (ps.size <= 1){
    parts.forEach(k => { const x = q(k); if (x) x.hidden = true; }); q('.tbe-ccap').textContent = '';
    const n = [...ps.values()].reduce((a, b) => a + b, 0), lab = ps.size ? [...ps.keys()][0] : '';
    const when = !lab ? '' : c.iv === 'year' ? 'in ' + lab : c.iv === 'quarter' ? 'in ' + lab.replace(' ', ', ') : 'in ' + dateLabel({ date: lab + '-01', prec: 'month' });
    note.hidden = false; note.className = 'cap tbe-cnote';
    note.textContent = n ? `All ${pl(n, 'story', 'stories')} here ran ${when}, so there is no chart. Try a finer “Group by”.`.replace(' Try a finer “Group by”.', c.iv === 'month' ? '' : ' Try a finer “Group by”.') : 'No dated stories in this range, so there is no chart.';
    return null;
  }
  parts.forEach(k => { const x = q(k); if (x) x.hidden = false; }); note.hidden = true; note.textContent = '';
  let tlOn = c.tl && c.show !== 'pct' && c.bk === 'tone';   /* TONEVIEW-v1: the tone line belongs to "Tone over time" only (no checkbox to lay it over the coverage bars) */
  if (tlOn){ const tp = new Map(); rows.forEach(r => { if (!Object.prototype.hasOwnProperty.call(TB_PTS, r.tone)) return; const k = per(r); if (k) tp.set(k, (tp.get(k) || 0) + 1); });
    if ([...tp.values()].filter(v => v >= 3).length < 2){ tlOn = false; note.hidden = false; note.className = 'cap tbe-cnote';
      note.textContent = 'No tone line: it needs 3 or more rated stories in at least 2 periods.'; } }
  const os = q('[data-tbc="only"]');
  if (os && c.only && ![...os.options].some(x => x.value === c.only)) os.insertAdjacentHTML('beforeend', `<option value="${esc(c.only)}">${esc(c.only)}</option>`);
  if (os) os.value = c.only || '';
  const out = timeChart(rows, { iv: c.iv, bk: c.bk, meas: c.meas, from: +c.from, pct: c.show === 'pct', avgOn: c.avg, avgEl: q('[data-tbc="avg"]'), onlyEl: q('[data-tbc="only"]'),
    title: q('.tbe-ctitle'), cap: q('.tbe-ccap'), legend: q('.tbe-cleg'), chart, table: q('.tbe-ctable'), quick: false, pick, foot: 'Click to list these stories below',
    capEnd: ' Click a bar to list those stories below.', extra: tlOn ? tbToneLine : null,
    legendExtra: tlOn ? '<span class="it"><span class="line" style="background:var(--accent)"></span>Average tone (rated stories only; periods with 3 or more), right axis: 0 = neutral, −2 very negative … +2 very positive</span>' : '' });
  const o = q('[data-tbc="only"]'); if (o) c.only = o.value;
  return out;
}
/* HEADER-v2 (Sammy comments 87f23f23 + 8065396d: the entity-page header was a run-on block): one header for every entity page.
   Kicker (type · date · source), title, one-line dek, then the facts in labelled clusters Who / What / Coverage / Links, each a
   two-column list (fixed label column, values wrap under themselves), lists as items with even gaps ("first N + more"),
   links (with their copy icons) in their own Links row (no "Copy link to this page" since NOCOPYLINK-v1). The page's other content (spec.extra:
   release copies, bill milestones ...) is its own card under the header, not part of it.
   spec: kicker (string or [parts]), title, dek | sub (html), groups: [{ label, facts: [[label, html]] }] or facts: [[label, html]]
   (sorted into the clusters by label, TB_HGROUP), links: [[label, html]], extra (html). */
const TB_HGROUP = { who: ['publisher', 'original', 'by', 'source', 'title', 'outlets', 'reporters', 'others named', 'role', 'where', 'format', 'reach', 'language', 'languages', 'also listed as'],
  coverage: ['stories', 'originals', 'reprints', 'pickups', 'tone average', 'negative', 'negative stories', 'last story', 'first story', 'latest story', 'busiest week', 'original coverage', 'outlets reached', 'copies', 'days to last pickup', 'furthest', 'press releases', 'picked up by', 'also ran in'],
  links: ['website', 'leginfo', 'story', 'official release', 'links', 'saved copy'] };
const TB_HGL = { who: 'Who', what: 'What', coverage: 'Coverage', links: 'Links' };
function tbHeadGroups(P){
  /* an empty value is left out of the header (no rows of dashes); a cluster with nothing left is dropped */
  const full = f => f && f[1] != null && String(f[1]).replace(/<[^>]*>/g, '').trim() !== '';
  if (Array.isArray(P.groups)) return P.groups.map(g => g && Object.assign({}, g, { facts: (g.facts || []).filter(full) })).filter(g => g && g.facts.length);
  const g = { who: [], what: [], coverage: [], links: [] };
  (P.facts || []).filter(full).forEach(f => { const k = String(f[0] || '').toLowerCase(); const c = Object.keys(TB_HGROUP).find(x => TB_HGROUP[x].includes(k)) || 'what'; g[c].push(f); });
  (P.links || []).filter(full).forEach(f => g.links.push(f));
  return ['who', 'what', 'coverage', 'links'].filter(k => g[k].length).map(k => ({ key: k, label: TB_HGL[k], facts: g[k] }));
}
function tbHeadHtml(P){
  const kick = Array.isArray(P.kicker) ? P.kicker.filter(Boolean).map(x => esc(x)).join('<span class="tbh-dot" aria-hidden="true">·</span>') : P.kicker ? esc(P.kicker) : '';
  const dek = P.dek != null ? P.dek : P.sub;
  const dd = v => v == null || v === '' ? '<span class="sub">—</span>' : v;
  const gs = tbHeadGroups(P), links = gs.find(g => g.key === 'links' || g.label === 'Links');
  /* NOGLABEL-v1 (Sammy 2026-10-28, Reporters: "get rid of this subtitle"): spec.groupLabels === false drops the Who/What/Coverage h3s; the hairline rules between clusters stay */
  const cl = g => `<section class="tbh-g" data-g="${esc(g.key || tbSlug(g.label))}">${P.groupLabels === false ? '' : `<h3 class="tbh-gl">${esc(g.label)}</h3>`}<dl class="tbe-facts">${g.facts.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${dd(v)}</dd></div>`).join('')}</dl></section>`;
  const body = gs.filter(g => g !== links).map(cl).join('');
  /* NOCOPYLINK-v1 (Sammy 2026-10-28: "remove throughout"): no "Copy link to this page" button; the Links row shows only when the page has links */
  const lk = links ? `<div class="tbh-links"><dl class="tbe-facts tbh-lk">${links.facts.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${dd(v)}</dd></div>`).join('')}</dl></div>` : '';
  return `<div class="tbe-head"><div class="card tbe-hcard"><div class="tbh-top">${kick ? `<div class="eyebrow tbh-kick">${kick}</div>` : ''}<h2 class="sec tbh-title">${esc(P.title)}</h2>${dek ? `<div class="tbe-sub tbh-dek">${dek}</div>` : ''}</div>`
    + (body ? `<div class="tbh-grid" data-n="${gs.filter(g => g !== links).length}">${body}</div>` : '') + lk + `</div>`
    + (P.extra ? `<div class="card pad tbe-extra">${P.extra}</div>` : '') + `</div>`;
}
function tbEntityPage(el, ctx, m){
  const ent = m.page.find(ctx.sub, ctx);
  if (!ent){ el.innerHTML = `<div class="tbe"><div class="tbe-back"><button class="linkbtn" data-tbe="back">‹ ${esc(m.label)}</button></div><div class="card pad"><div class="empty">Nothing in ${esc(m.label)} is called “${esc(ctx.sub)}”.</div></div></div>`;
    el.querySelector('[data-tbe="back"]').onclick = () => ctx.back(); return; }
  try { ctx.scope = m.page.scope ? m.page.scope(ent, ctx) || null : null; } catch(e){ console.error(e); ctx.scope = null; }   /* LINKSCOPE-v1 */
  const P = m.page.spec(ent, ctx), p = ctx.params;
  const rows0 = (P.rows || []).map(r => P.rowAs ? Object.assign({}, r, P.rowAs(r) || {}) : r);   // rowAs: this entity's copy (outlet, date, pub, prec) of each story
  const FK = FACETS.map(f => f.key);
  /* RELUI-v1 (rp-ui): optional page hooks — P.rowTag(r) -> HTML in the row's meta line; P.rank(r) -> number (lower = stronger;
     the list then opens "strongest link first", sort key 'ev'); P.how = { label, opts: [[id, label]], of(r) -> id } filter chips
     above the list (URL param how); P.below = HTML after the list */
  const DEF_SORT = P.rank ? { key: 'ev', dir: 1 } : { key: 'date', dir: -1 };
  const st = { q: p.q || '', sel: {}, when: p.when || 'all', sort: DEF_SORT, how: p.how || '', page: Math.max(0, (+p.pg || 1) - 1), per: [25, 50, 100, 250].includes(+p.per) ? +p.per : 50 };
  if (p.sort){ const d = p.sort[0] === '-', k = d ? p.sort.slice(1) : p.sort; if (['date', 'hl', 'topic', 'reach', 'rep'].includes(k) || (k === 'ev' && P.rank)) st.sort = { key: k, dir: d ? -1 : 1 }; }
  FK.forEach(k => st.sel[k] = new Set(p[k] ? p[k].split('|').filter(Boolean) : []));
  const openF = TB.open.get(ctx.tab + ':page') || TB.open.set(ctx.tab + ':page', new Set(['topic', 'tone'])).get(ctx.tab + ':page');
  const fq = {}, fall = {};
  const range = () => { const w = st.when; if (w === 'all') return [null, null]; if (/^\d+$/.test(w)) return [addDays(TODAY, -(+w)), null];
    if (w[0] === 'y') return [w.slice(1), w.slice(1) + '-99']; if (w === 'early') return [null, '2016-99']; if (w.startsWith('c:')){ const [a, z] = w.slice(2).split('..'); return [a || null, z || null]; } return [null, null]; };
  const words = () => tbQ(st.q).split(' ').filter(Boolean);
  const textOf = r => { const ft = FT.get(r.id) || '', k = r.id, c = TB.ft.get(k); if (c && c.n === ft.length) return c.t; const t = tbFold(r._s + ' ' + ft); TB.ft.set(k, { n: ft.length, t }); return t; };
  const pass = (r, skip, noDate) => { const w = words(); if (w.length){ const t = textOf(r); if (!w.every(x => t.includes(x))) return false; }
    for (const k of FK){ if (k === skip) continue; const s = st.sel[k]; if (s.size && !vals(r, k).some(v => s.has(v))) return false; }
    if (noDate) return true; const [a, z] = range(); if (a && r.date < a) return false; if (z && r.date > z) return false; return true; };
  const howOk = r => !P.how || !st.how || P.how.of(r) === st.how;
  const sorted = rows => { if (st.sort.key === 'ev' && P.rank){ const k = rows.map(r => [P.rank(r), r]); k.sort((x, y) => x[0] - y[0] || String(y[1].date || '').localeCompare(String(x[1].date || '')));
      return k.map(x => x[1]); }
    const keep = S.sort; S.sort = st.sort; try { return sortRows(rows); } finally { S.sort = keep; } };
  const save = () => { const q = {}; if (st.q) q.q = st.q; FK.forEach(k => { if (st.sel[k].size) q[k] = [...st.sel[k]].join('|'); });
    if (st.when !== 'all') q.when = st.when; if (st.sort.key !== DEF_SORT.key || st.sort.dir !== DEF_SORT.dir) q.sort = (st.sort.dir < 0 ? '-' : '') + st.sort.key; if (st.how) q.how = st.how;
    if (st.page) q.pg = String(st.page + 1); if (st.per !== 50) q.per = String(st.per); Object.assign(q, tbChartEnc(cs)); ctx.setParams(q); };
  const cs = tbChartState(p, rows0);
  const fillWhen = () => { const sel = $$('.tbe-when'); sel.innerHTML = TB_WHEN().map(([v, l]) => `<option value="${v}">${esc(l)}</option>`).join('') + (st.when.startsWith('c:') ? `<option value="${esc(st.when)}">${esc(tbWhenLabel(st.when))}</option>` : ''); sel.value = st.when; };
  const search = '<svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true" focusable="false" style="color:var(--ink-3);flex:none"><circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M10.4 10.4 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
  const ph = P.placeholder || `Search ${pl(rows0.length, 'story', 'stories')} ${P.noun ? 'of this ' + P.noun : ''}`.trim();
  el.innerHTML = `<div class="tbe" data-tbe-id="${esc(ctx.sub)}">
  <div class="tbe-back"><button class="linkbtn" data-tbe="back">‹ ${esc(P.backLabel || ('All ' + m.label.toLowerCase()))}</button></div>
  ${tbHeadHtml(P)}
  ${P.cards || ''}
  ${(P.embeds || []).map((x, i) => `<div class="tbe-emb" data-emb="${i}"></div>`).join('')}
  ${P.chart === false ? '' : tbChartCard(rows0)}
  <div class="grid-clips"${P.list === false ? ' hidden' : ''}>
    <aside class="rail tt-rail" aria-label="Filters"><div class="rail-head"><h2>Filters</h2><span style="display:flex;gap:14px;align-items:center"><button class="linkbtn" data-tbe="clear">Clear all</button><button class="btn" data-tbe="done" style="padding:5px 12px">Done</button></span></div><div class="tbe-facets"></div></aside>
    <div class="pane">
      <div class="toolbar"><span class="fgroup"><button class="btn filters-toggle tbe-ft" data-tbe="rail">Filters</button></span>
        <label class="search">${search}<input type="search" class="tbe-q" placeholder="${esc(ph)}" aria-label="${esc(ph)}" autocomplete="off" value="${esc(st.q)}"></label>
        <select class="sel tbe-when" aria-label="Date range"></select>
        <details class="dlmenu"><summary class="btn">Export</summary><div class="menu">
          <button data-tbe="copyclips"><b>Copy clips list</b><span>A dated list to paste into an email or memo</span></button>
          <button data-tbe="copysheet"><b>Copy for spreadsheet</b><span>Rows to paste into Excel or Google Sheets</span></button>
          <button data-tbe="csv"><b>Download CSV</b><span>The listed stories, with every field</span></button></div></details></div>
      <div class="chips tbe-chips"></div>${P.how || P.rank ? '<div class="tbe-how"></div>' : ''}
      <div class="card"><div class="tablewrap"><table class="db tbe-tab"><thead><tr>
        <th class="c-d"><button data-tbsort="date">Date</button></th><th class="c-h"><button data-tbsort="hl">Story</button></th>
        <th class="c-t"><button data-tbsort="topic">Issue / Bill</button></th><th class="c-rc"><button data-tbsort="reach">Reach</button></th>
        <th class="c-r"><button data-tbsort="rep" title="Other outlets that ran the same story">Reprints</button></th></tr></thead><tbody class="tbe-body"></tbody></table></div><div class="pager tbe-pager"></div></div>
    </div></div>
  ${P.below || ''}
  <div class="scrim tt-scrim" hidden></div></div>`;
  const $$ = s => el.querySelector(s), rail = $$('.tt-rail'), scrim = $$('.tt-scrim');
  let rows = [], order = [];
  const optH = (f, v, n, on) => `<label class="opt ${n || on ? '' : 'zero'}"><input type="checkbox" data-tbef="${f.key}" value="${esc(v)}" ${on ? 'checked' : ''}>${f.sw ? `<span class="sw" style="background:${colorFor(f.key, v)}"></span>` : ''}<span class="lab" title="${esc(f.key === 'bills' && billName(v) ? v + ': ' + billName(v) : NR_LABEL(v))}">${esc(NR_LABEL(v))}${f.key === 'bills' && billName(v) ? `<small class="bname"> ${esc(billName(v))}</small>` : ''}</span><span class="n">${fmt(n)}</span></label>`;
  function drawFacets(){
    $$('.tbe-facets').innerHTML = FACETS.map(f => {
      const c = new Map(); rows0.forEach(r => { if (pass(r, f.key)) vals(r, f.key).forEach(v => c.set(v, (c.get(v) || 0) + 1)); });
      const have = new Set(); rows0.forEach(r => vals(r, f.key).forEach(v => have.add(v == null ? '' : v)));
      let vs = (valuesOf(f.key) || []).filter(v => have.has(v)); have.forEach(v => { if (!vs.includes(v)) vs.push(v); });
      const sel = st.sel[f.key], q = tbFold(fq[f.key] || ''), n0 = vs.length;
      if (f.search){ if (q) vs = vs.filter(v => tbFold(v + ' ' + (f.key === 'bills' ? billName(v) : '')).includes(q)); vs.sort((a, b) => (c.get(b) || 0) - (c.get(a) || 0)); }
      vs = vs.filter(v => !NR_BLANK(v)).concat(vs.filter(NR_BLANK));   /* BLANKFACET-v1 */
      const cut = f.search && !q && !fall[f.key] ? vs.slice(0, f.limit || 8) : vs, show = [...sel].filter(v => !cut.includes(v)).concat(cut);
      if (!n0) return '';
      return `<details class="facet" data-tbefacet="${f.key}" ${openF.has(f.key) || sel.size ? 'open' : ''}><summary>${esc(f.label)}<small>${sel.size ? sel.size + ' on' : ''}</small></summary><div class="body">${f.hint ? `<div class="hint">${f.hint}</div>` : ''}`
        + (f.search && n0 > (f.limit || 8) ? `<input class="fsearch" data-tbeq="${f.key}" type="search" placeholder="Find one of ${fmt(n0)}" aria-label="Find ${esc(f.label)}" value="${esc(fq[f.key] || '')}">` : '')
        + show.map(v => optH(f, v, c.get(v) || 0, sel.has(v))).join('')
        + (f.search && !q && n0 > (f.limit || 8) ? `<button class="linkbtn" data-tbemore="${f.key}">${fall[f.key] ? 'Show fewer' : 'Show all ' + fmt(n0)}</button>` : '') + '</div></details>';
    }).join('');
  }
  /* LINKSCOPE-v1: the row's issue and reach tags open Clips on that value within this page's scope */
  const clipTag = (k, v) => v ? tbFacetLink(k, v, ctx.scope).replace('class="linkbtn tb-fl"', 'class="tag tlink tb-fl"').replace('">' + esc(v) + '</button>', `"><span class="sw" style="background:${colorFor(k, v)}"></span>${esc(v)}</button>`) : '';
  const ftS = r => { const k = S.q; S.q = foldQ(st.q).trim(); try { return ftSnippet(r); } finally { S.q = k; } };
  function rowH(r){ const q = words().length;
    return `<tr data-id="${r.id}" tabindex="0"><td class="d">${dateLabel(r)}</td>
      <td class="h"><div class="hl">${esc(r.hl)}</div>${r.hl_en ? `<div class="hl-en">${esc(r.hl_en)}</div>` : ''}${q && !words().every(w => tbFold(r._s).includes(w)) ? ftS(r) : ''}<div class="ol"><span class="mdate">${dateLabel(r)}</span>${P.rowTag ? P.rowTag(r) || '' : ''}<span>${r.outlet ? `<button type="button" class="tlink" data-pub="${esc(r.pub || r.outlet)}" data-ol="${esc(tbOutlet(r.outlet, r.aid))}" title="Open the ${esc(tbOutlet(r.outlet, r.aid))} page">${esc(r.outlet)}</button>` : ''}</span>${r.authors.length ? `<span class="by">By ${r.authors.map(a => `<button type="button" class="tlink" data-author="${esc(a)}" title="Open the ${esc(a)} page">${esc(a)}</button>`).join(', ')}</span>` : ''}${badges(r, false, P.noRelBadge)}</div></td>
      <td class="t">${clipTag('topic', r.topic)}${r.bills.length ? `<span class="bchips">${r.bills.map(b => `<button type="button" class="bchip" data-bill="${esc(b)}" data-date="${esc(String(r.date || '').slice(0, 10))}" title="Open the ${esc(b)} page${billName(b) ? ': ' + esc(billName(b)) : ''}">${esc(b)}</button>`).join('')}</span>` : ''}</td>
      <td class="rc">${reachTags(r).map(v => clipTag('reach', v)).join(' · ')}</td>
      <td class="r">${r.pick || ''}</td></tr>`; }
  function draw(keepPage){
    rows = sorted(rows0.filter(r => pass(r) && howOk(r))); order = rows.map(r => r.id); if (!keepPage) st.page = 0;
    const hw = $$('.tbe-how'); if (hw){ const base = rows0.filter(r => pass(r)), n = {}; if (P.how) base.forEach(r => { const k = P.how.of(r); n[k] = (n[k] || 0) + 1; });
      const chip = (id, label, c) => `<button type="button" class="tbe-hw${st.how === id ? ' on' : ''}" data-tbhow="${esc(id)}" aria-pressed="${st.how === id}">${esc(label)}${c != null ? ` <span class="n">${fmt(c)}</span>` : ''}</button>`;
      const opts = P.how ? P.how.opts.filter(([id]) => n[id] || st.how === id) : [];
      hw.innerHTML = (opts.length > 1 || st.how ? `<span class="tbe-hw-l">${esc(P.how.label)}</span>` + chip('', 'All', base.length) + opts.map(([id, l]) => chip(id, l, n[id] || 0)).join('') : '')
        + (P.rank ? `<span class="tbe-hw-s"><label for="tbeSort${esc(ctx.sub)}">Sort</label><select class="sel tbe-evsort" id="tbeSort${esc(ctx.sub)}"><option value="ev"${st.sort.key === 'ev' ? ' selected' : ''}>Strongest link first</option><option value="date"${st.sort.key === 'date' && st.sort.dir < 0 ? ' selected' : ''}>Newest first</option><option value="date+"${st.sort.key === 'date' && st.sort.dir > 0 ? ' selected' : ''}>Oldest first</option>${['ev', 'date'].includes(st.sort.key) ? '' : '<option selected>Column sort</option>'}</select></span>` : ''); }
    const pages = Math.max(1, Math.ceil(rows.length / st.per)); if (st.page >= pages) st.page = pages - 1;
    const slice = rows.slice(st.page * st.per, st.page * st.per + st.per);
    el.querySelectorAll('.tbe-tab th button[data-tbsort]').forEach(b => { if (b.dataset.tbsort === st.sort.key) b.dataset.dir = st.sort.dir < 0 ? '↓' : '↑'; else delete b.dataset.dir; });
    $$('.tbe-body').innerHTML = slice.length ? slice.map(rowH).join('') : `<tr><td colspan="5" class="empty">No stories match. <button class="linkbtn" data-tbe="clear">Clear all filters</button></td></tr>`;
    const from = rows.length ? st.page * st.per + 1 : 0, to = Math.min(rows.length, (st.page + 1) * st.per);
    $$('.tbe-pager').innerHTML = `<span class="mono">${fmt(from)}–${fmt(to)} of ${fmt(rows.length)}</span><span class="ctl"><label>Per page</label><select class="tbe-per">${[25, 50, 100, 250].map(n => `<option ${n === st.per ? 'selected' : ''}>${n}</option>`).join('')}</select><button data-tbpg="-1" ${st.page === 0 ? 'disabled' : ''}>Previous</button><span class="mono">${st.page + 1} / ${pages}</span><button data-tbpg="1" ${st.page >= pages - 1 ? 'disabled' : ''}>Next</button></span>`;
    const ch = []; if (st.q) ch.push(['q', '', 'Search', `“${st.q}”`]); if (st.when !== 'all') ch.push(['when', '', 'Dates', tbWhenLabel(st.when)]);
    FACETS.forEach(f => st.sel[f.key].forEach(v => ch.push([f.key, v, f.label, NR_LABEL(v)])));
    $$('.tbe-ft').innerHTML = 'Filters' + (ch.length ? ` <span class="fcount">${ch.length}</span>` : '');
    $$('.tbe-chips').innerHTML = `<span class="result-line"><b style="color:var(--ink)">${fmt(rows.length)}</b> of ${pl(rows0.length, 'story', 'stories')}</span>` + ch.map(([k, v, l, t]) => `<span class="chip"><span class="k">${esc(l)}</span><span>${esc(t)}</span><button aria-label="Remove ${esc(l)} filter" data-tberm="${esc(k)}" data-v="${esc(v)}">${IC.xs}</button></span>`).join('');
    drawFacets(); drawChart(); save();
  }
  function drawChart(){ tbChartDraw(el, cs, rows0.filter(r => pass(r, null, true)), rows0.length, (b, iv) => {
      st.when = iv === 'year' ? 'y' + b : iv === 'month' ? `c:${b}..${b}-99` : (() => { const yr = b.slice(0, 4), q = +b.slice(-1); return `c:${yr}-${String(q * 3 - 2).padStart(2, '0')}..${yr}-${String(q * 3).padStart(2, '0')}-99`; })();
      fillWhen(); draw(); toast(`Showing ${tbWhenLabel(st.when)}`); const t = el.querySelector('.tbe-tab'); if (t) t.scrollIntoView({ block: 'start', behavior: 'smooth' }); }); }
  /* exports reuse the Clips exporters on exactly these rows (S.pick / S.sort are swapped in and restored at once) */
  const viaClips = fn => { const kp = S.pick, ks = S.sort; S.pick = new Set(order); S.sort = st.sort; try { fn(); } finally { S.pick = kp; S.sort = ks; } };
  const openRail = on => { rail.classList.toggle('open', on); scrim.hidden = !on; };
  el.addEventListener('input', e => { const t = e.target;
    if (t.matches('.tbe-q')){ clearTimeout(TB._eT); TB._eT = setTimeout(() => { st.q = t.value.trim(); draw(); }, 120); return; }
    if (t.dataset.tbeq){ fq[t.dataset.tbeq] = t.value; const k = t.dataset.tbeq, pos = t.selectionStart; drawFacets(); const i = el.querySelector(`[data-tbeq="${k}"]`); if (i){ i.focus(); try { i.setSelectionRange(pos, pos); } catch(x){} } } });
  el.addEventListener('change', e => { const t = e.target;
    if (t.dataset.tbef){ const s = st.sel[t.dataset.tbef]; t.checked ? s.add(t.value) : s.delete(t.value); draw(); return; }
    if (t.matches('.tbe-when')){ st.when = t.value; draw(); return; }
    if (t.matches('.tbe-per')){ st.per = +t.value; draw(); return; }
    if (t.matches('.tbe-evsort')){ st.sort = t.value === 'ev' ? { key: 'ev', dir: 1 } : { key: 'date', dir: t.value === 'date+' ? 1 : -1 }; draw(); return; }
    if (t.dataset.tbc){ cs[t.dataset.tbc] = t.type === 'checkbox' ? t.checked : t.value; cs.qv = ''; if (t.dataset.tbc === 'bk') cs.only = ''; drawChart(); save(); } });
  el.addEventListener('toggle', e => { const d = e.target.closest && e.target.closest('details[data-tbefacet]'); if (d) d.open ? openF.add(d.dataset.tbefacet) : openF.delete(d.dataset.tbefacet); }, true);
  el.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches && e.target.matches('tr[data-id]')) e.target.click(); if (e.key === 'Escape' && rail.classList.contains('open')) openRail(false); });
  el.addEventListener('click', e => {
    const t = e.target, b = t.closest('[data-tbe]'), a = b && b.dataset.tbe;
    if (a === 'back'){ e.stopPropagation(); ctx.back(); return; }
    if (a === 'rail'){ openRail(true); return; } if (a === 'done' || t === scrim){ openRail(false); return; }
    if (a === 'clear'){ e.stopPropagation(); st.q = ''; $$('.tbe-q').value = ''; FK.forEach(k => st.sel[k].clear()); st.when = 'all'; $$('.tbe-when').value = 'all'; draw(); return; }
    if (a === 'copyclips'){ b.closest('details').open = false; viaClips(() => $('#copyClips').onclick()); return; }
    if (a === 'copysheet'){ b.closest('details').open = false; viaClips(() => $('#copySheet').onclick()); return; }
    if (a === 'csv'){ b.closest('details').open = false; viaClips(() => download('csv')); return; }
    const qv = t.closest('[data-tbqv]'); if (qv){ Object.assign(cs, TB_QV[qv.dataset.tbqv], { qv: qv.dataset.tbqv, only: '' }); tbChartSync(el, cs); drawChart(); save(); return; }
    const mo = t.closest('[data-tbemore]'); if (mo){ fall[mo.dataset.tbemore] = !fall[mo.dataset.tbemore]; drawFacets(); return; }
    const hw = t.closest('[data-tbhow]'); if (hw){ st.how = hw.dataset.tbhow; draw(); return; }
    const rm = t.closest('[data-tberm]'); if (rm){ const k = rm.dataset.tberm; if (k === 'q'){ st.q = ''; $$('.tbe-q').value = ''; } else if (k === 'when'){ st.when = 'all'; $$('.tbe-when').value = 'all'; } else st.sel[k].delete(rm.dataset.v); draw(); return; }
    const so = t.closest('[data-tbsort]'); if (so){ const k = so.dataset.tbsort; st.sort = st.sort.key === k ? { key: k, dir: -st.sort.dir } : { key: k, dir: (k === 'date' || k === 'rep') ? -1 : 1 }; draw(); return; }
    const pg = t.closest('[data-tbpg]'); if (pg){ st.page += +pg.dataset.tbpg; draw(true); el.querySelector('.tbe-tab').scrollIntoView({ block: 'start' }); return; }
    /* inside this page, outlet / reporter / issue / reach / bill links filter the page (Clips' own links would leave it) */
    const inList = t.closest('.tbe-body, .tbe-xbody');   /* RELLATER-v1: extra story tables (.tbe-xbody) behave like the main list */
    if (inList){
      const fk = t.closest('[data-fk]'), bl = t.closest('[data-bill]'), pb = t.closest('[data-pub]'), au = t.closest('[data-author]');
      const add = (k, v) => { e.stopPropagation(); e.preventDefault(); if (st.sel[k]){ st.sel[k].add(v); draw(); toast(`Filtered this page to ${v}`); } };
      if (fk && st.sel[fk.dataset.fk]) return add(fk.dataset.fk, fk.dataset.fv);
      /* LINKRULES-v2 (Sammy 2026-10-28): a bill opens its Bills page, an outlet its Outlets page (issues and reach open Clips
         with this page's scope through [data-tbclip]); the filter rail still filters this list */
      if (bl){ e.stopPropagation(); e.preventDefault(); const sl = tbBillSlug(bl.dataset.bill, bl.dataset.date); if (sl) tbOpen('bills', {}, sl); else add('bills', bl.dataset.bill); return; }
      if (pb){ e.stopPropagation(); e.preventDefault(); const sub = tbOutletSub(pb.dataset.ol || pb.dataset.pub); if (sub && !(ctx.tab === 'outlets' && sub === ctx.sub)) tbOpen('outlets', {}, sub); else if (!sub) add('pub', pb.dataset.pub); return; }
      if (au){ e.stopPropagation(); e.preventDefault(); const sub = tbAuthorSub(au.dataset.author); if (sub) tbOpen('reporters', {}, sub); else tbOpen('reporters', { q: au.dataset.author }, ''); return; }   /* LINKRULES-v1 */
      if (t.closest('a[href]')) return;
      const tr = t.closest('tr[data-id]'); if (tr){ e.stopPropagation(); openViewer(tr.dataset.id, inList.dataset.order ? inList.dataset.order.split(',') : order); }
    }
  });
  fillWhen(); tbChartSync(el, cs); draw(true);
  /* RELLATER-v1 (Sammy 2026-10-29): a module's extra story lists (P.xrows[key] into <tbody class="tbe-xbody" data-tbx=key>) use the
     main list's row renderer (title, outlet / date, P.rowTag evidence tag, click opens the story; no links) */
  el.querySelectorAll('.tbe-xbody[data-tbx]').forEach(tb => { const xs = ((P.xrows || {})[tb.dataset.tbx] || []).map(r => P.rowAs ? Object.assign({}, r, P.rowAs(r) || {}) : r);
    tb.dataset.order = xs.map(r => r.id).join(','); tb.innerHTML = xs.map(rowH).join(''); });
  (P.embeds || []).forEach((x, i) => { const h = el.querySelector(`.tbe-emb[data-emb="${i}"]`); let n = 0; try { n = tbMiniList(h, x.tab, x); } catch(e){ console.error(e); } if (!n && h) h.remove(); });
  if (typeof P.after === 'function'){ try { P.after(el.querySelector('.tbe'), ctx); } catch(e){ console.error(e); } }
  return { rows: () => rows.slice() };
}
/* Data keeps its links into the tools; their labels name the new tabs (anchored edits in code/patch_tabs.py) */
/* ---------- /TABS-v1 ---------- */
/* ---------- RELUI-v1 (rp-ui 2026-10-28): the shared ⓘ tooltip ----------
   tbInfo(text, about) -> a small ⓘ button; click / tap / Enter toggles a popover with the text (title attributes do not show
   on phones), hover shows it on a mouse, Esc or a click elsewhere closes it. Text: plain, lines split on "\n". One popover
   element for the page. Used for rule definitions instead of paragraphs (text from the data blocks' rules tables). */
function tbInfo(text, about){ text = String(text || '').trim(); if (!text) return '';
  return `<button type="button" class="tb-i" data-tbi="${esc(text)}" aria-label="${esc(about ? 'About ' + about : 'More about this')}" aria-expanded="false">i</button>`; }
(function tbInfoMount(){
  let pop = null, on = null, hov = false;
  const close = () => { if (pop) pop.hidden = true; if (on) on.setAttribute('aria-expanded', 'false'); on = null; };
  const open = b => { if (!pop){ pop = document.createElement('div'); pop.className = 'tb-ipop'; pop.setAttribute('role', 'tooltip'); pop.id = 'tbIpop'; document.body.appendChild(pop); }
    if (on && on !== b) on.setAttribute('aria-expanded', 'false');
    on = b; b.setAttribute('aria-expanded', 'true'); b.setAttribute('aria-describedby', 'tbIpop');
    pop.innerHTML = String(b.dataset.tbi).split('\n').map(l => `<p>${esc(l)}</p>`).join(''); pop.hidden = false;
    const r = b.getBoundingClientRect(), w = Math.min(340, innerWidth - 24); pop.style.width = w + 'px';
    const x = Math.max(12, Math.min(r.left + r.width / 2 - w / 2, innerWidth - w - 12));
    const below = r.bottom + 8 + pop.offsetHeight < innerHeight || r.top < pop.offsetHeight + 16;
    pop.style.left = (x + scrollX) + 'px'; pop.style.top = ((below ? r.bottom + 8 : r.top - pop.offsetHeight - 8) + scrollY) + 'px'; };
  document.addEventListener('click', e => { const b = e.target.closest && e.target.closest('.tb-i');
    if (b){ e.preventDefault(); e.stopPropagation(); if (on === b && !pop.hidden && !hov) close(); else open(b); hov = false; return; }
    if (on && !(e.target.closest && e.target.closest('.tb-ipop'))) close(); }, true);
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && on){ const b = on; close(); try { b.focus(); } catch(x){} } });
  document.addEventListener('mouseover', e => { if (!matchMedia('(hover:hover)').matches) return; const b = e.target.closest && e.target.closest('.tb-i'); if (b && on !== b){ hov = true; open(b); } });
  document.addEventListener('mouseout', e => { const b = e.target.closest && e.target.closest('.tb-i'); if (b && hov && on === b && !(e.relatedTarget && b.contains(e.relatedTarget))){ hov = false; close(); } });
  addEventListener('scroll', () => { if (on) close(); }, { passive: true, capture: true });
  document.head.insertAdjacentHTML('beforeend', `<style id="relui-css">
.tb-i{display:inline-flex;align-items:center;justify-content:center;width:16px;height:16px;margin:0 0 0 5px;padding:0;border:1px solid var(--line);border-radius:50%;background:var(--panel);color:var(--ink-3);font:italic 700 var(--fs-xs)/1 Georgia,serif;cursor:pointer;vertical-align:1px;flex:none}
.tb-i:hover,.tb-i[aria-expanded="true"]{color:var(--accent);border-color:var(--accent)}.tb-i:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.tb-ipop{position:absolute;z-index:90;padding:9px 12px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink-2);box-shadow:0 6px 22px rgba(0,0,0,.16);font:400 var(--fs-md)/1.45 var(--f-body);text-transform:none;letter-spacing:0}
.tb-ipop p{margin:0}.tb-ipop p+p{margin-top:5px}
.tbe-how{display:flex;flex-wrap:wrap;align-items:center;gap:6px 6px;font-size:var(--fs-md)}
.tbe-hw-l{color:var(--ink-3);font-weight:600;margin-right:2px}
.tbe-hw{border:1px solid var(--line);border-radius:999px;background:var(--panel);color:var(--ink-2);padding:3px 10px;font:500 var(--fs-md)/1.3 var(--f-body);cursor:pointer}
.tbe-hw .n{color:var(--ink-3);font-variant-numeric:tabular-nums}.tbe-hw.on{background:var(--ink);border-color:var(--ink);color:var(--panel)}.tbe-hw.on .n{color:inherit;opacity:.8}
.tbe-hw:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.tbe-hw-s{margin-left:auto;display:inline-flex;gap:6px;align-items:center;color:var(--ink-3)}.tbe-hw-s .sel{font-size:var(--fs-md);padding:3px 6px}
@media (max-width:640px){.tbe-hw-s{margin-left:0}}
/* Press releases (build/tabs/releases.js RELUI-v1) */
.rl-btns{display:flex;flex-wrap:wrap;align-items:center;gap:8px 18px;margin-top:10px}
.rl-btns .rl-read{padding:7px 16px;font-weight:600}.rl-btns .tb-lk{font-size:var(--fs-md)}.rl-wc{font-size:var(--fs-md)}
.rl-lead{display:none}
@media (min-width:1100px){.rl-lead:not(:empty){display:block;margin-top:10px;padding:8px 12px;border-left:3px solid var(--line);color:var(--ink-2);font-size:var(--fs-md);line-height:1.5;max-width:100ch}}
.rl-lead .linkbtn{display:inline;font-size:inherit;font-weight:600;padding:0}
.tbh-title.rl-tlink{cursor:pointer}.tbh-title.rl-tlink:hover{color:var(--accent);text-decoration:underline;text-underline-offset:3px}
.rl-tag{display:inline-block;font:600 var(--fs-xs)/1.5 var(--f-body);padding:0 7px;border-radius:999px;background:var(--panel-2);border:1px solid var(--line);color:var(--ink-2);white-space:nowrap}
.rl-tag[data-ev="text"],.rl-tag[data-ev="nearcopy"],.rl-tag[data-ev="quote"]{border-color:var(--accent);color:var(--accent)}
.tbe-body .ol .rl-tag{margin:0 2px}.rl-lag{color:var(--ink-3);font-size:var(--fs-sm);margin-left:5px;white-space:nowrap}
.rl-ms{color:var(--ink-2)}.rl-bg{display:block;margin-top:2px}
.rl-relh{display:grid;gap:3px;padding:6px 2px 0}
.rl-relh .tb-us-h{margin:0;font:600 var(--fs-xs)/1.35 var(--f-body);letter-spacing:.07em;text-transform:uppercase;color:var(--ink-3)}
.rl-brk{font-size:var(--fs-md);color:var(--ink-2)}
.rl-det>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:6px}.rl-det>summary::-webkit-details-marker{display:none}
.rl-det>summary::before{content:'';width:0;height:0;border-style:solid;border-width:4px 0 4px 6px;border-color:transparent transparent transparent currentColor;transition:transform .12s;flex:none}
.rl-det[open]>summary::before{transform:rotate(90deg)}
#tbBody table.db.tbe-xtab thead th{padding:9px 12px}#tbBody table.db.tbe-xtab thead th.c-r{text-align:center}.rl-xh{margin-top:6px}.rl-xdet{display:grid;gap:8px;margin-top:6px}.rl-xdet>summary.tb-us-h{margin:0;padding:6px 2px 0;font:600 var(--fs-xs)/1.35 var(--f-body);letter-spacing:.07em;text-transform:uppercase;color:var(--ink-3)}
.rl-thr{display:grid;gap:2px}.rl-thr+.rl-thr{margin-top:10px}.rl-thr-h{display:flex;flex-wrap:wrap;gap:4px 6px;align-items:center}
.rl-sub{display:flex;flex-wrap:wrap;gap:3px 10px;align-items:center;margin-top:2px}.rl-sub .bchips{margin-top:0}
.rl-type{font-weight:600;color:var(--ink-2)}
.rl-pm{display:none}
/* RELRECS-v1 R3: the release list's quarter chart sits under the filter chips, above the list */
.tt[data-tt-id="releases"] .tt-bar{order:0}.tt[data-tt-id="releases"] .tt-chips{order:1}.tt[data-tt-id="releases"] .tt-extra{order:2}.tt[data-tt-id="releases"] .tt-list{order:3}
.rl-chart .rl-copts{margin-top:6px}
@media (max-width:760px){.tt[data-tt-id="releases"] table.db td.rl-dk{display:none}.tt[data-tt-id="releases"] .rl-pm{display:block;margin-top:3px}}
#sheet.sheet-copy .meta-tog{display:none}#sheet.sheet-copy .sheet-meta.fold>.dlinks{display:flex}
</style>`);
})();
