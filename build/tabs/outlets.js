/* Outlets tab (agent-tab-outlets, TABS-v1, 2026-10-27; contract build/tabs_contract.md §9 "Outlets").
   One row per canonical outlet (ctx.outlet: spelling variants merged). Units = what an outlet ran: every tracker story in
   its own outlet ("original") plus, once per other outlet, its reprints (r.reps; a story's copies in its own outlet and
   repeat copies in one reprint outlet are not counted again; a reprint is dated by its earliest copy, else the story's
   date). Story filters (date, issue, publisher at the time, language, ran as, story tone) cut units before grouping, so
   every count, tone average and last story is over the stories that pass. Publisher = the sheet's Publisher column as
   dated spans (ctx.publishers); a story's publisher is the span covering its date, else the last owner before it.
   Reach / format / language / county / state come from the sheet per outlet (tab_outlets block, outlets_data.py), with
   the tracker's own story fields as fallback. Click an outlet: its page (#outlets/<slug>) with the shared entity page. */
(function(){ "use strict";
  var NEG = { 'Negative': 1, 'Very negative': 1 };
  var TONES = ['Very positive', 'Positive', 'Neutral', 'Negative', 'Very negative', 'Not rated'];
  var SKIP_T = { '': 1, 'Unassigned': 1 };
  var ST = { AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware',
    DC: 'District of Columbia', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa', KS: 'Kansas',
    KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi',
    MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York',
    NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island',
    SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington',
    WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming', PR: 'Puerto Rico', USA: 'United States' };
  var LINK_SKIP = /(newsbank|proquest|oclc|castatelib|archive\.org|google\.|bing\.|yahoo\.com\/news|msn\.com|newsbreak|ground\.news)/i;
  var G = { v: null };   // per data version: slugs, spellings, websites, sheet attributes

  function byCount(m){ return Array.from(m.entries()).sort(function(a, b){ return b[1] - a[1] || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0); }); }
  function inc(m, k, n){ if (k) m.set(k, (m.get(k) || 0) + (n || 1)); }
  function yr(d){ return d ? String(d).slice(0, 4) : ''; }

  /* everything that does not depend on filters, once per data version */
  function glob(ctx){
    if (G.v === ctx.version && G.ctxD === ctx.D) return G;
    var b = ctx.block('outlets') || { k: [''], o: {} }, K = b.k || [''];
    var attrs = new Map(); Object.keys(b.o || {}).forEach(function(n){ var a = b.o[n];
      attrs.set(n, { reach: K[a[0]] || '', medium: K[a[1]] || '', lang: K[a[2]] || '', county: K[a[3]] || '', state: K[a[4]] || '', city: K[a[5]] || '' }); });
    var spell = new Map(), hosts = new Map(), fb = new Map();
    var note = function(o, raw){ raw = String(raw || '').trim(); if (!o || !raw) return; var s = spell.get(o) || spell.set(o, new Set()).get(o); if (raw !== o) s.add(raw); };
    var fall = function(o){ return fb.get(o) || fb.set(o, { reach: new Map(), medium: new Map(), lang: new Map(), county: new Map(), state: new Map() }).get(o); };
    ctx.D.forEach(function(r){ if (!r) return;
      var o = ctx.outlet(r.outlet, r.aid); note(o, r.outlet);
      var f = fall(o); String(r.reach || '').split(';').forEach(function(x){ inc(f.reach, x.trim()); }); inc(f.medium, r.media); inc(f.lang, ctx.langOf(r)); inc(f.county, r.county);
      [r.plink, r.link].forEach(function(u){ var m = /^https?:\/\/(?:www\.)?([^\/?#]+)/i.exec(String(u || '')); if (m && !LINK_SKIP.test(m[1])){ var h = hosts.get(o) || hosts.set(o, new Map()).get(o); inc(h, m[1].toLowerCase()); } });
      (r.reps || []).forEach(function(p){ if (!p) return; var q = ctx.outlet(p.outlet, p.aid); note(q, p.outlet); var g = fall(q); inc(g.county, p.county); inc(g.state, p.state); }); });
    var names = Array.from(spell.keys()).sort(function(a, b){ return a.localeCompare(b); }), used = new Set(), slug = new Map(), bySlug = new Map();
    names.forEach(function(n){ var s = ctx.slug(n), t = s, i = 2; while (used.has(t)) t = s + '-' + (i++); used.add(t); slug.set(n, t); bySlug.set(t, n); });
    G = { v: ctx.version, ctxD: ctx.D, attrs: attrs, spell: spell, hosts: hosts, fb: fb, slug: slug, bySlug: bySlug, pubs: new Map(), info: new Map() };
    return G;
  }
  /* the outlet's fixed attributes: the sheet's (tab_outlets), else the tracker stories' own fields */
  function info(ctx, o){
    var g = glob(ctx); if (g.info.has(o)) return g.info.get(o);
    var a = g.attrs.get(o) || {}, f = g.fb.get(o), top = function(m){ var x = m ? byCount(m)[0] : null; return x ? x[0] : ''; };
    var reach = a.reach || (f ? byCount(f.reach).map(function(x){ return x[0]; }).slice(0, 2).join('; ') : '');
    var county = a.county || top(f && f.county), state = a.state || top(f && f.state) || (county ? 'CA' : '');
    var lang = a.lang || top(f && f.lang);
    var where = !state ? (county ? county + ' County, California' : 'Not recorded')
      : state === 'CA' ? (county ? county + ' County, California' : 'California')
      : state === 'USA' ? 'United States (national)' : /^no home county$/i.test(state) ? ((a.medium || top(f && f.medium)) === 'Podcast' ? 'Podcast (no location)' : 'National or network (no home county)')   /* REVIEW4-PAGE-v1 E7 */
      : (ST[state] || state);
    var h = g.hosts.get(o), site = h ? byCount(h)[0][0] : '';
    var x = { reach: reach, reachTags: reach ? reach.split(';').map(function(s){ return s.trim(); }).filter(Boolean) : [], medium: a.medium || top(f && f.medium), lang: lang,
      county: county, state: state, city: a.city || '', where: where, site: site, spell: Array.from(g.spell.get(o) || []).sort() };
    g.info.set(o, x); return x;
  }
  /* the sheet's Publisher spans for an outlet, and the publisher at a date (span covering it, else the last one before it,
     else the first one after it; undated spans only when nothing is dated) */
  function spans(ctx, o){ var g = glob(ctx); if (!g.pubs.has(o)) g.pubs.set(o, (ctx.publishers(o) || []).slice().sort(function(a, b){ return (a.d0 || '9') < (b.d0 || '9') ? -1 : (a.d0 || '9') > (b.d0 || '9') ? 1 : a.name.localeCompare(b.name); })); return g.pubs.get(o); }
  function pubAt(ctx, o, d){
    var ps = spans(ctx, o); if (!ps.length) return ''; d = String(d || '').slice(0, 10);
    var dated = ps.filter(function(p){ return p.d0; }); if (!d || !dated.length) return ctx.publisherOf(o, d || undefined);
    var hit = dated.filter(function(p){ return p.d0 <= d && d <= (p.d1 || '9999'); });
    if (hit.length) return hit.sort(function(a, b){ return b.n - a.n; })[0].name;
    var before = dated.filter(function(p){ return (p.d1 || p.d0) < d; }).sort(function(a, b){ return (b.d1 || b.d0) < (a.d1 || a.d0) ? -1 : 1; });
    return (before[0] || dated[0]).name;
  }
  /* "McClatchy" or "Tegna 2019–2026; Nexstar Media Group 2026" (years from the sheet's dated rows) */
  function pubText(ctx, o){
    var ps = spans(ctx, o); if (!ps.length) return '';
    var m = new Map(); ps.forEach(function(p){ var x = m.get(p.name) || m.set(p.name, { name: p.name, d0: '', d1: '', n: 0 }).get(p.name);
      if (p.d0 && (!x.d0 || p.d0 < x.d0)) x.d0 = p.d0; if (p.d1 && (!x.d1 || p.d1 > x.d1)) x.d1 = p.d1; x.n += p.n; });
    var l = Array.from(m.values()); if (l.length === 1) return l[0].name;
    return l.map(function(x){ var a = yr(x.d0), z = yr(x.d1); return x.name + (a ? ' ' + (a === z || !z ? a : a + '–' + z) : ''); }).join('; ');
  }

  /* FORMAT-v1: what a unit is (Article, Print, Broadcast segment, ...): the story's / the reprint's own Format cell, else the AV type, else Article */
  var AVF = { 'Broadcast segment': 'Broadcast segment', 'Video clip': 'Video clip', 'Episode': 'Podcast episode', 'Web story': 'Article' };
  function fmtOfRow(r){ if (r.fmt) return r.fmt; var t = r.av && r.av.type; return t ? (AVF[t] || 'Article') : 'Article'; }
  function fmtOfRep(r, p){ if (p && p.fmt) return p.fmt; var t = p && p.av && p.av.type; return t ? (AVF[t] || 'Article') : 'Article'; }
  function units(ctx){
    var out = [];
    ctx.D.forEach(function(r){
      if (!r) return; var own = ctx.outlet(r.outlet, r.aid), seen = new Set([own]), ownH = ctx.house ? ctx.house(r.outlet, r.aid) : own;   /* REPCOUNT-v1: a copy in the original's own house is not a reprint */
      if (own) out.push(unit(ctx, r, own, 'Original', r.date));
      (r.reps || []).filter(function(p){ return p && !p.blend; }).slice().sort(function(a, b){ return (a.date || '9') < (b.date || '9') ? -1 : (a.date || '9') > (b.date || '9') ? 1 : 0; }).forEach(function(p){
        var o = ctx.outlet(p.outlet, p.aid); if (!o || seen.has(o) || (ctx.house && ctx.house(p.outlet, p.aid) === ownH)) return; seen.add(o); out.push(unit(ctx, r, o, 'Reprint', p.date || r.date, p)); });
    });
    return out;
  }
  function unit(ctx, r, o, kind, d, pp){
    var lang = kind === 'Original' ? ctx.langOf(r) : (info(ctx, o).lang || ctx.langOf(r));
    return { r: r, o: o, kind: kind, fmt: (kind === 'Original' ? fmtOfRow(r) : fmtOfRep(r, pp)), d: d || '', lang: lang, pub: pubAt(ctx, o, d) || 'Not recorded', tone: r.tone || 'Not rated', topic: String(r.topic || '').trim() || 'Unassigned' };
  }
  /* people who wrote the outlet's ORIGINAL stories (people only, as Reporters: no staff groups, wires, organisations,
     author titles or Jesse Gabriel; one entry per person via authorKey + canon) */
  function people(ctx, us){
    var P = new Map();
    us.forEach(function(u){ if (u.kind !== 'Original') return; var r = u.r, seen = new Set();
      var titles = new Set(String(r.atitle || '').split(';').map(function(t){ return ctx.authorKey(t); }).filter(Boolean));
      (r.authors || []).forEach(function(a){ a = String(a || '').trim(); if (!a || titles.has(ctx.authorKey(a))) return;
        if ((ctx.authorKind ? ctx.authorKind(a) : 'person') !== 'person') return;
        var k = ctx.authorKey(a); if (!k || k === 'jesse gabriel' || seen.has(k)) return; seen.add(k);
        if (ctx.affOf && ctx.affOf(r, a) !== u.o) return;   /* AFFIL-v1: only people whose own outlet this is (not an edited re-run of their story) */
        var p = P.get(k) || P.set(k, { name: ctx.canonAuthors([a])[0] || a, n: 0 }).get(k); p.n++; }); });
    return Array.from(P.values()).sort(function(a, b){ return b.n - a.n || a.name.localeCompare(b.name); });
  }
  function group(us, ctx){
    var g = glob(ctx), m = new Map();
    us.forEach(function(u){ var it = m.get(u.o); if (!it){ it = { name: u.o, us: [] }; m.set(u.o, it); } it.us.push(u); });
    return Array.from(m.values()).map(function(it){
      var I = info(ctx, it.name), ids = new Set(), rs = [], top = new Map(), last = null, first = null;
      it.us.forEach(function(u){ if (!ids.has(u.r.id)){ ids.add(u.r.id); rs.push(u.r); } if (!SKIP_T[u.topic]) inc(top, u.topic);
        if (u.d && (!last || u.d > last.d)) last = u; if (u.d && (!first || u.d < first.d)) first = u; });
      var tone = ctx.tone(rs), ppl = people(ctx, it.us), fm = new Map(); it.us.forEach(function(u){ inc(fm, u.fmt); });
      return { key: g.slug.get(it.name) || ctx.slug(it.name), name: it.name, us: it.us, rs: rs, n: rs.length,
        orig: it.us.filter(function(u){ return u.kind === 'Original'; }).length, reps: it.us.filter(function(u){ return u.kind === 'Reprint'; }).length,
        neg: rs.filter(function(r){ return NEG[r.tone]; }).length, tone: tone, issues: byCount(top).slice(0, 3),
        last: last ? last.d : '', lastId: last ? last.r.id : '', lastR: last ? last.r : null, first: first ? first.d : '', firstR: first ? first.r : null,
        people: ppl, pub: pubText(ctx, it.name), info: I, fmts: byCount(fm) };
    });
  }
  var dl = function(ctx, r, d){ return r ? ctx.dateLabel(Object.assign({}, r, { date: d || r.date, prec: d && d !== r.date ? 'day' : r.prec })) : ''; };
  var sub = function(ctx, it){ var I = it.info; return [I.city && I.state === 'CA' && I.county ? I.city : I.where === 'Not recorded' ? '' : I.where, I.reach, I.medium + (it.fmts.length > 1 ? ' (' + it.fmts.map(function(x){ return x[1] + ' ' + x[0].toLowerCase(); }).join(', ') + ')' : ''), I.lang && I.lang !== 'English' ? I.lang : ''].filter(Boolean).map(ctx.esc).join(' · '); };
  var issT = function(it){ return it.issues.map(function(x){ return x[0] + ' (' + x[1] + ')'; }).join('; '); };
  var pplT = function(it, k){ return it.people.slice(0, k || 3).map(function(p){ return p.name; }).join('; '); };

  var list = {
    noun: ['outlet', 'outlets'], title: 'Outlets', placeholder: 'Search outlets, publishers, places',
    cap: 'Every outlet that ran a story mentioning Gabriel, as an original or a reprint, with its publisher (the sheet’s Publisher column, by date where the owner changed). Counts, tone and last story follow the story filters. Click an outlet to open its page.',
    units: units, group: group, key: function(it){ return it.key; },
    text: function(it){ var I = it.info; return [it.name, I.spell.join(' '), it.pub, I.where, I.city, I.reach, I.medium, I.lang].join(' | '); },
    facets: [
      { key: 'date', label: 'Date range', type: 'date', level: 'unit', date: function(u){ return u.d; }, hint: 'Stories the outlet ran in this range (a reprint counts on the date it ran).' },
      { key: 'iss', label: 'Issue', level: 'unit', open: true, vals: function(u){ return u.topic; } },
      { key: 'pubr', label: 'Publisher', level: 'unit', search: true, limit: 8, vals: function(u){ return u.pub; }, hint: 'Who owned the outlet when it ran the story (the sheet’s Publisher column).' },
      { key: 'lng', label: 'Language', level: 'unit', vals: function(u){ return u.lang; } },
      { key: 'geo', label: 'County or state', search: true, limit: 8, vals: function(it){ return it.info.where; }, hint: 'Where the outlet is based. Statewide and national outlets show their home base.' },
      { key: 'rch', label: 'Reach', vals: function(it){ return it.info.reachTags.length ? it.info.reachTags : ['Not recorded']; }, hint: 'The kind of outlet (the sheet’s Reach column).' },
      { key: 'med', label: 'Medium', vals: function(it){ return it.info.medium ? [it.info.medium] : ['Not recorded']; }, hint: 'The kind of outlet (the sheet’s Medium column).' },
      { key: 'fmt', label: 'Format', level: 'unit', vals: function(u){ return u.fmt; }, hint: 'What the outlet ran: web articles, print pages, broadcast segments, video clips, audio segments or podcast episodes (the sheet’s Format column).' },
      { key: 'kind', label: 'Ran as', level: 'unit', order: ['Original', 'Reprint'], vals: function(u){ return u.kind; }, hint: 'Original: the story first ran here. Reprint: a copy of a story that first ran elsewhere.' },
      { key: 'tmix', label: 'Story tone', level: 'unit', order: TONES, vals: function(u){ return u.tone; }, hint: 'How the story portrays Gabriel. Rated from saved copies only.' },
      { key: 'n', label: 'Story count', type: 'one', options: [
        { id: '100', label: '100 or more', test: function(it){ return it.n >= 100; } }, { id: '20', label: '20 to 99', test: function(it){ return it.n >= 20 && it.n < 100; } },
        { id: '5', label: '5 to 19', test: function(it){ return it.n >= 5 && it.n < 20; } }, { id: '2', label: '2 to 4', test: function(it){ return it.n >= 2 && it.n < 5; } },
        { id: '1', label: 'One story', test: function(it){ return it.n === 1; } }] },
      { key: 'tavg', label: 'Tone average', type: 'one', hint: 'Average over rated stories: −2 very negative … +2 very positive.', options: [
        { id: 'pos', label: 'Above neutral', test: function(it){ return it.tone.n > 0 && it.tone.avg > 0; } },
        { id: 'neu', label: 'Neutral (exactly 0)', test: function(it){ return it.tone.n > 0 && it.tone.avg === 0; } },
        { id: 'neg', label: 'Below neutral', test: function(it){ return it.tone.n > 0 && it.tone.avg < 0; } },
        { id: 'anyneg', label: 'At least one negative story', test: function(it){ return it.neg > 0; } },
        { id: 'none', label: 'No rated stories', test: function(it){ return !it.tone.n; } }] },
      { key: 'active', label: 'Active within', type: 'date', date: function(it){ return it.last; }, any: 'Any time', hint: 'Outlets whose latest story is in this range.' },
      /* DATAMOVE-v1 (Sammy 2026-10-28): from Data › Gaps "Outlets gone quiet" and Data › "Outlet relationships › New" */
      { key: 'quiet', label: 'Gone quiet', type: 'one', hint: 'Outlets with 3 or more stories about him and none lately (wire services left out).', options: [90, 180, 365].map(function(d){
        return { id: String(d), label: 'Nothing in the last ' + (d === 90 ? '90 days' : d === 180 ? '6 months' : 'year'), test: function(it, ctx){ var c = ctx && ctx.cut0 ? ctx.cut0(d) : ''; return it.n >= 3 && !!it.last && it.last < c && it.info.medium !== 'Wire'; } }; }) },
      { key: 'first', label: 'First story', type: 'date', date: function(it){ return it.first; }, any: 'Any time', hint: 'Outlets whose first story about him is in this range: pick a recent range to see outlets new to covering him.' }
    ],
    columns: [
      { key: 'name', label: 'Outlet', val: function(it){ return it.name; }, cell: function(it, ctx){ var s = sub(ctx, it); return '<button type="button" class="linkbtn tt-open">' + ctx.esc(it.name) + '</button>' + (s ? '<div class="sub">' + s + '</div>' : ''); } },
      { key: 'pub', label: 'Publisher', val: function(it){ return it.pub; }, cell: function(it, ctx){ return it.pub ? ctx.esc(it.pub) : '<span class="sub">Not recorded</span>'; } },
      { key: 'n', label: 'Stories', num: true, dir: -1, val: function(it){ return it.n; }, cell: function(it, ctx){ return ctx.fmt(it.n); } },
      { key: 'orig', label: 'Originals', num: true, dir: -1, val: function(it){ return it.orig; }, cell: function(it, ctx){ return ctx.fmt(it.orig); } },
      { key: 'reps', label: 'Reprints', num: true, dir: -1, val: function(it){ return it.reps; }, cell: function(it, ctx){ return ctx.fmt(it.reps); } },
      { key: 'last', label: 'Last story', dir: -1, cls: 'nw', val: function(it){ return it.last; }, cell: function(it, ctx){ return it.lastR ? ctx.esc(dl(ctx, it.lastR, it.last)) : ''; } },
      { key: 'iss', label: 'Top issues', sortable: false, val: issT, cell: function(it, ctx){ return it.issues.map(function(x){ return (ctx.issueLink ? ctx.issueLink(x[0]) : ctx.esc(x[0])) + ' <span class="sub">' + x[1] + '</span>'; }).join('<br>'); } },
      { key: 'tone', label: 'Tone avg', num: true, dir: -1, cls: 'nw', sort: function(it){ return it.tone.n ? it.tone.avg : null; }, val: function(it){ return it.tone.text; }, cell: function(it, ctx){ return it.tone.n ? ctx.toneHtml(it.tone) : '<span class="sub">None rated</span>'; },
        csv: function(it){ return it.tone.csv; } },   /* TONELABEL-v1: the CSV keeps the number (−2 … +2); "Tone label" and "Rated stories" columns follow */
      { key: 'neg', label: 'Negative', num: true, dir: -1, val: function(it){ return it.neg; }, cell: function(it, ctx){ return ctx.fmt(it.neg); } },
      { key: 'ppl', label: 'Top reporters (own stories)', sortable: false, val: function(it){ return pplT(it, 3); }, cell: function(it, ctx){ return it.people.slice(0, 3).map(function(p){ return (ctx.authorLink ? ctx.authorLink(p.name) : ctx.esc(p.name)) + ' <span class="sub">' + p.n + '</span>'; }).join('<br>'); } }
    ],
    csvExtra: [['Where', function(it){ return it.info.where; }], ['County', function(it){ return it.info.county; }], ['State', function(it){ return it.info.state; }],
      ['City', function(it){ return it.info.city; }], ['Reach', function(it){ return it.info.reach; }], ['Medium', function(it){ return it.info.medium; }], ['Format mix', function(it){ return it.fmts.map(function(x){ return x[0] + ' ' + x[1]; }).join('; '); }],
      ['Language', function(it){ return it.info.lang; }], ['Tone label', function(it){ return it.tone.label; }], ['Rated stories', function(it){ return it.tone.n; }], ['First story', function(it){ return it.first; }],
      ['Also listed as', function(it){ return it.info.spell.join('; '); }], ['Website', function(it){ return it.info.site; }]],
    sort: { key: 'n', dir: -1 }, open: 'page', step: { desk: 100, phone: 25 },
    answer: function(res, st, ctx){
      if (!res.length) return '';
      var o = 0, p = 0, top = res.slice().sort(function(a, b){ return b.n - a.n || a.name.localeCompare(b.name); })[0];
      res.forEach(function(it){ o += it.orig; p += it.reps; });
      return ctx.pl(res.length, 'outlet', 'outlets') + ' ran ' + ctx.fmt(o) + ' original ' + (o === 1 ? 'story' : 'stories') + ' and ' + ctx.pl(p, 'reprint', 'reprints') + '. Most: ' + top.name + ' with ' + ctx.pl(top.n, 'story', 'stories') + '.';
    },
    empty: function(){ return 'No outlet matches these filters.'; },
    copies: [
      { label: 'Copy outlet names', sub: 'One outlet per line', text: function(res){ return res.map(function(it){ return it.name; }).join('\n'); } },
      { label: 'Copy names with publisher', sub: '“Outlet (Publisher)” per line', text: function(res){ return res.map(function(it){ return it.name + (it.pub ? ' (' + it.pub + ')' : ''); }).join('\n'); } }
    ],
    csvName: function(st, ctx){ return 'AJG outlets ' + ctx.TODAY + '.csv'; },
    /* Phase B list.extra: the 50-state map of the outlets listed (shows only with more than 5 qualifying out-of-state outlets) */
    extra: function(el, res, ctx){
      if (!el.firstChild) el.innerHTML = '<div class="card pad"><h2 class="sec">Outlets outside California</h2><div class="cap">The outlets listed above, by the state the sheet gives them.</div><div class="ol-us"></div></div>';
      ctx.usMap(el.querySelector('.ol-us'), res.map(function(it){ return it.name; }), { rows: Array.from(new Set([].concat.apply([], res.map(function(it){ return it.rs; })))) });   /* GEOMAP-v1 */
    }
  };

  var memo = { v: null, all: null };
  function allItems(ctx){ if (memo.v !== ctx.version || memo.d !== ctx.D){ memo = { v: ctx.version, d: ctx.D, all: group(units(ctx), ctx) }; } return memo.all; }
  /* RELREVERSE-v1 (rp-reverse 2026-10-28): the press releases this page's stories come from or relate to (ctx.rels, any
     evidence type but 'possible'), plus, on an outlet page, the releases the outlet ran as copies; newest first */
  function relsFor(rs, ctx, outlet){
    if (!ctx.rels) return [];
    var R = ctx.rels(), m = new Map(), get = function(t){ var e = m.get(t); if (!e){ e = { rel: t, n: 0, ran: false }; m.set(t, e); } return e; };
    rs.forEach(function(r){ (R.bySid.get(r.id) || []).forEach(function(x){ get(x.rel).n++; }); });
    if (outlet) R.list.forEach(function(t){ if (t.copies.some(function(q){ return ctx.outlet(q.raw, q.aid) === outlet; })) get(t).ran = true; });
    return Array.from(m.values()).sort(function(a, b){ return b.rel.date.localeCompare(a.rel.date); });
  }
  function relFact(rs, ctx, outlet){
    var a = relsFor(rs, ctx, outlet); if (!a.length) return null;
    return ['Press releases', ctx.hlist(a.map(function(e){ var t = e.rel, sub = [t.date ? ctx.dateLabel({ date: t.date, prec: 'day' }) : '', e.ran ? 'ran it' : '', e.n > 1 ? e.n + ' stories' : ''].filter(Boolean).join(' · ');
      /* an <a> (truly inline, unlike a button), so a long title wraps under itself and the fact label lines up with its first
         line; the framework's [data-tb-go] click handler opens the page */
      return '<a class="linkbtn tb-rlink" href="#press-releases/' + encodeURIComponent(t.sub) + '" data-tb-go="releases" data-tb-sub="' + ctx.esc(t.sub) + '" title="Open the release page">' + ctx.esc(t.title) + ' ›</a>' + (sub ? ' <span class="sub">' + ctx.esc(sub) + '</span>' : ''); }), 2)];
  }
  var page = {
    slug: function(it){ return it.key; },
    /* LINKSCOPE-v1: the outlet in Clips = its own stories' outlet names (Clips' Outlet filter), else "ran in" for an outlet that only reprinted */
    scope: function(it){ var pubs = []; it.us.forEach(function(u){ if (u.kind === 'Original' && u.r.pub && pubs.indexOf(u.r.pub) < 0) pubs.push(u.r.pub); });
      return { sel: { pub: pubs }, ranin: pubs.length ? '' : it.name, label: it.name }; },
    find: function(sub, ctx){ var s = String(sub || ''), a = allItems(ctx), t = ctx.slug(s);
      return a.filter(function(it){ return it.key === s; })[0] || a.filter(function(it){ return it.key === t; })[0] || null; },
    spec: function(it, ctx){
      var I = it.info, ps = spans(ctx, it.name);
      /* HEADER-v2: each publisher on its own line with its dated span */
      var pubH = ps.length > 1 ? ctx.lines(pubText(ctx, it.name).split('; ').map(function(x){ var m = /^(.*?)\s+(\d{4}(?:–\d{4})?)$/.exec(x); return m ? ctx.esc(m[1]) + ' <span class="sub">' + ctx.esc(m[2]) + '</span>' : ctx.esc(x); })) : ctx.esc(it.pub);
      var story = function(r, d){ return r ? '<button type="button" class="linkbtn" data-tbstory="' + ctx.esc(r.id) + '">' + ctx.esc(dl(ctx, r, d)) + '</button>' : ''; };
      /* LINKSCOPE-v1: reach, format, language and a California county open Clips on that value for this outlet */
      var fl = function(k, v){ return ctx.facetLink ? ctx.facetLink(k, v) : ctx.esc(v); };
      var whereH = I.state === 'CA' && I.county ? fl('county', I.county) + ' County, California' : ctx.esc(I.where);
      var who = [['Publisher', pubH], ['Where', whereH + (I.city && I.state === 'CA' ? ' <span class="sub">' + ctx.esc(I.city) + '</span>' : '')],
          ['Medium', fl('media', I.medium)], ['Format', ctx.hlist(it.fmts.map(function(x){ return (ctx.facetLink ? ctx.facetLink('fmt', x[0]) : ctx.esc(x[0])) + ' <span class="sub">' + x[1] + '</span>'; }))], ['Reach', I.reachTags.length ? ctx.hlist(I.reachTags.map(function(v){ return fl('reach', v); })) : '<span class="sub">Reach not set yet</span>']   /* REVIEW4-PAGE-v1 C2 (page part) */, ['Language', fl('lang', I.lang)]];
      if (I.spell.length) who.push(['Also listed as', ctx.hlist(I.spell.map(ctx.esc), 3)]);
      var what = [['Top issues', ctx.hlist(it.issues.map(function(x){ return (ctx.issueLink ? ctx.issueLink(x[0]) : ctx.esc(x[0])) + ' <span class="sub">' + x[1] + '</span>'; }))],
          ['Top reporters (own stories only)', ctx.hlist(it.people.slice(0, 6).map(function(p){ return (ctx.authorLink ? ctx.authorLink(p.name) : ctx.esc(p.name)) + ' <span class="sub">' + p.n + '</span>'; }), 3)]];
      var rf = relFact(it.rs, ctx, it.name); if (rf) what.push(rf);
      var cov = [['Stories', ctx.fmt(it.n)], ['Originals', ctx.fmt(it.orig)], ['Reprints', ctx.fmt(it.reps)],
          ['Tone average', it.tone.n ? ctx.toneHtml(it.tone) : ''], ['Negative', ctx.fmt(it.neg)],
          ['Last story', story(it.lastR, it.last)], ['First story', story(it.firstR, it.first)]];
      var links = [['Website', I.site ? ctx.link('https://' + I.site, I.site) : '']];
      var y0 = yr(it.first), y1 = yr(it.last), top = it.issues[0];
      return { kicker: ['Outlet', I.where === 'Not recorded' ? '' : I.where], title: it.name, noun: 'outlet', backLabel: 'All outlets',
        placeholder: 'Search the ' + ctx.pl(it.n, 'story', 'stories') + ' this outlet ran',
        dek: ctx.esc(ctx.pl(it.n, 'story', 'stories') + ' mentioning Gabriel' + (y0 ? (y0 === y1 ? ' in ' + y0 : ', ' + y0 + '–' + y1) : '') + ': ' + ctx.fmt(it.orig) + ' original, ' + ctx.pl(it.reps, 'reprint', 'reprints') + '.' + (top ? ' Most often on ' + top[0] + '.' : '')),
        groups: [{ key: 'who', label: 'Who', facts: who }, { key: 'what', label: 'What', facts: what }, { key: 'coverage', label: 'Coverage', facts: cov }, { key: 'links', label: 'Links', facts: links }],
        facts: who.concat(what, cov, links),
        rows: it.rs,
        /* EMBEDROWS-v1 (Sammy, preview comment): the Reporters tab's own rows for the people who wrote this outlet's stories */
        embeds: [{ tab: 'reporters', title: 'Reporters', cap: 'The Reporters tab’s rows for the people who wrote this outlet’s own stories (reporters whose stories it only reprinted or re-ran are left out), counted over those stories. Click a name for the reporter’s page.',
          unit: function(u){ return (u.affs || [u.outlet]).indexOf(it.name) >= 0; }, person: function(p){ return (p.aff || '') === it.name; }, cols: ['name', 'stories', 'last', 'topics', 'tone', 'neg'] }],
        /* Phase B rowAs: a story this outlet ran as a reprint is listed (and charted) as this outlet's copy: its date */
        rowAs: (function(){ var by = new Map(); it.us.forEach(function(u){ if (!by.has(u.r.id) || u.kind === 'Original') by.set(u.r.id, u); });
          return function(r){ var u = by.get(r.id); return u && u.kind === 'Reprint' ? { outlet: it.name, pub: it.name, date: u.d || r.date, prec: u.d && u.d.length >= 10 ? 'day' : r.prec } : null; }; })() };
    }
  };
  AJGTabs.register({ id: 'outlets', list: list, page: page,
    /* no old links point here; an outlet / pub param (e.g. from a hand-made link) opens that outlet's page, else searches */
    legacy: function(p, ctx){ var n = p.outlet || p.pub; if (!n) return { params: {}, sub: '' };
      var c = ctx.outlet(n), s = glob(ctx).slug.get(c); return s ? { params: {}, sub: s } : { params: { q: n }, sub: '' }; } });
})();
