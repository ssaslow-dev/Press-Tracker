/* Reporters tab (TABS-v1 module, agent-tab-reporters 2026-10-27; replaces Press desk › Pitch, build/insights/reporters.js).
   Units = tracker stories (Op-ed by Gabriel stories left out). Each story's bylines become one entry per person via the
   tracker's authorKey + canon (ACANON); Jesse Gabriel and author strings that are the story's author-title (r.atitle) are
   left out. Story facets (date range, outlet (AFFIL-v1: the reporter's own outlets), Reach, Medium, issue, bill, language) filter stories
   BEFORE grouping, so every count, tone average, last story and top issue is over the stories that pass them. Reporter facets:
   byline type (no default since DEFCLEAR-v1; staff groups under "Staff bylines"), story count, tone, active within.
   Row: name, outlets (ctx.outlet canonical names, most stories first), stories, last story, top issues, tone average over RATED
   stories (ctx.tone: "Negative −0.6", count in the tooltip), negative count (Negative + Very negative). Click -> reporter page #reporters/<slug>
   (all of that reporter's stories, independent of the list's filters). Old Pitch links: author -> that page, issue -> filter. */
(function(){ "use strict";
  /* v23-REPQ (Sammy, V23Q): op-ed / guest-only people are "Contributors", counted apart from reporters */
  var KIND = { person: 'People', contributor: 'Contributors', staff: 'Staff bylines', board: 'Editorial boards', wire: 'Wires', org: 'Organizations' };
  var KIND_ONE = { person: 'Reporter', contributor: 'Contributor', staff: 'Staff byline', board: 'Editorial board', wire: 'Wire', org: 'Organization' };
  /* REVIEW4-PAGE-v1 A10: "Governor’S Office" -> "Governor’s Office" (an apostrophe-S inside a name is never a capital S) */
  function fixCase(n){ return String(n || '').replace(/([a-z])([’'])S\b/g, '$1$2s'); }
  var KIND_ORDER = ['People', 'Contributors', 'Staff bylines', 'Editorial boards', 'Wires', 'Organizations'];
  var NEG = { 'Negative': 1, 'Very negative': 1 };
  var SKIP_TOPIC = { '': 1, 'Unassigned': 1 };
  var C = null;                                 // the latest ctx (facet notes / colours need it; set in units())
  var memo = { v: null, units: null, all: null, slugs: null, bySlug: null };

  function byCount(m){ return Array.from(m.entries()).sort(function(a, b){ return b[1] - a[1] || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0); }).map(function(x){ return x[0]; }); }
  function inc(m, k){ m.set(k, (m.get(k) || 0) + 1); }

  /* one unit per story: the tracker row plus its facet values and the people on its byline (computed once per data version) */
  function units(ctx){
    C = ctx;
    if (memo.v === ctx.version && memo.units) return memo.units;
    var out = [];
    ctx.D.forEach(function(r){
      if (!r || !r.date || r.role === 'Op-ed by Gabriel' || r.depth === 'List-only') return;   /* v23-REPQ: list-only stories are never on this tab */
      var titles = new Set(String(r.atitle || '').split(';').map(function(t){ return ctx.authorKey(t); }).filter(Boolean));
      var seen = new Set(), ppl = [];
      (r.authors || []).forEach(function(a, i){
        a = String(a || '').trim(); if (!a) return;
        var k = ctx.authorKey(a); if (!k || k === 'jesse gabriel' || titles.has(k) || seen.has(k)) return; seen.add(k);
        var kd = ctx.authorKind(a), ri = ctx.repInfo ? ctx.repInfo(k) : null; if (kd === 'person' && ri && ri.c) kd = 'contributor';   /* v23-REPQ */
        ppl.push({ k: k, name: fixCase(ctx.canonAuthors([a])[0] || a), kind: kd, title: titleOf(r, a, i), aff: ctx.affOf ? ctx.affOf(r, a) : ctx.outlet(r.outlet, r.aid) });
      });
      if (!ppl.length) return;
      var affs = []; ppl.forEach(function(p){ if (p.aff && affs.indexOf(p.aff) < 0) affs.push(p.aff); });
      out.push({ r: r, id: r.id, date: r.date, ppl: ppl, outlet: ctx.outlet(r.outlet, r.aid), affs: affs, topic: String(r.topic || '').trim() || 'Unassigned',
        bills: (r.bills || []).slice(), lang: ctx.langOf(r), reach: ctx.reachTags(r), media: r.media || '' });
    });
    memo.v = ctx.version; memo.units = out; memo.all = null; memo.slugs = null; memo.bySlug = null;
    return out;
  }
  /* the sheet's "Author title": titles in author order joined by "; " (only trusted when it lines up one to one, or one author) */
  function titleOf(r, a, i){
    var t = String(r.atitle || '').split(';').map(function(x){ return x.trim(); });
    var n = (r.authors || []).length;
    if (!r.atitle) return '';
    if (n === 1) return t.join('; ');
    return t.length === n ? (t[i] || '') : '';
  }
  /* one item per person over the given stories. AFFIL-v1: a person's outlets are the outlets of their own Original stories
     (p.aff: an outlet's edited re-run of their story counts under their outlet), never a reprint outlet; opts.person(p, u)
     limits which people of a story count (an outlet page lists only the people whose outlet it is) */
  function group(us, ctx, opts){
    var m = new Map(), keep = opts && opts.person;
    us.forEach(function(u){
      u.ppl.forEach(function(p){
        if (keep && !keep(p, u)) return;
        var o = m.get(p.k);
        if (!o){ o = { key: p.k, name: p.name, kind: p.kind, rs: [], out: new Map(), ran: new Set(), top: new Map(), bills: new Map(), titles: new Map(), langs: new Map(), billDate: {}, neg: 0, last: '', lastR: null }; m.set(p.k, o); }
        o.rs.push(u.r); inc(o.out, p.aff || u.outlet);
        if (u.outlet && u.outlet !== (p.aff || u.outlet)) o.ran.add(u.outlet);
        (u.r.reps || []).forEach(function(q){ var x = q && ctx.outlet(q.outlet, q.aid); if (x && x !== (p.aff || u.outlet)) o.ran.add(x); }); if (!SKIP_TOPIC[u.topic]) inc(o.top, u.topic);
        u.bills.forEach(function(b){ inc(o.bills, b); if (!o.billDate[b] || u.date > o.billDate[b]) o.billDate[b] = u.date; }); inc(o.langs, u.lang);
        if (p.title) inc(o.titles, p.title);
        if (NEG[u.r.tone]) o.neg++;
        if (u.date > o.last || (u.date === o.last && o.lastR && u.id > o.lastR.id)){ o.last = u.date; o.lastR = u.r; }
      });
    });
    var res = [];
    m.forEach(function(o){
      o.stories = o.rs.length; o.outlets = byCount(o.out); o.topics = byCount(o.top).slice(0, 3); o.billList = byCount(o.bills);
      /* v23-REPQ: "Also wrote for" = one-off outlets and opinion pieces (REPAFF rule D), never employers; "Ran in" = the outlets that
         ran a wire reporter's copy (rule C) or a wire byline's copy. Contributors keep their outlets as the outlets they wrote for. */
      var ri = ctx.repInfo ? ctx.repInfo(o.key) : null; o.also = []; o.ranIn = [];
      if (ri){ if (o.kind !== 'contributor') (ri.also || []).forEach(function(x){ if (o.out.has(x) && o.out.size > 1){ o.also.push(x); o.out.delete(x); } });
        (ri.ran || []).forEach(function(x){ if (!o.out.has(x)) o.ranIn.push(x); });
        if (o.also.length) o.outlets = byCount(o.out); }
      o.titleList = byCount(o.titles); o.tone = ctx.tone(o.rs); o.kindLabel = KIND[o.kind] || 'People';
      o.ranList = Array.from(o.ran).filter(function(x){ return !o.out.has(x); }).sort();
      res.push(o);
    });
    res.sort(function(a, b){ return b.stories - a.stories || (b.last < a.last ? -1 : b.last > a.last ? 1 : 0) || a.name.localeCompare(b.name); });
    return res;
  }
  /* every reporter over every story (no filters): the pages and their slugs (stable, unique, readable) */
  function everyone(ctx){
    units(ctx);
    if (memo.all) return memo.all;
    memo.all = group(memo.units, ctx);
    var used = new Map(), slugs = new Map(), bySlug = new Map();
    memo.all.slice().sort(function(a, b){ return a.key < b.key ? -1 : a.key > b.key ? 1 : 0; }).forEach(function(o){
      var s = ctx.slug(o.name), n = (used.get(s) || 0) + 1; used.set(s, n); if (n > 1) s = s + '-' + n;
      slugs.set(o.key, s); bySlug.set(s, o); });
    memo.slugs = slugs; memo.bySlug = bySlug;
    return memo.all;
  }
  function slugOf(key, ctx){ everyone(ctx); return memo.slugs.get(key) || ctx.slug(key); }

  function outletCell(o, ctx){
    var e = ctx.esc; if (!o.outlets.length) return '<span class="sub">—</span>';
    return o.outlets.slice(0, 2).map(e).join('; ') + (o.outlets.length > 2 ? ' <span class="sub">+' + (o.outlets.length - 2) + ' more</span>' : '');
  }
  function storyBtn(r, ctx, label){ return r ? '<button type="button" class="linkbtn" data-tbstory="' + ctx.esc(r.id) + '" title="Open this story">' + ctx.esc(label || ctx.dateLabel(r)) + '</button>' : ''; }
  /* every bill number links to its Bills-tab page (addendum: ctx.billLink; until the integrator adds it, an <a data-bill> the helper upgrades) */
  function billLink(b, date, ctx){
    if (typeof ctx.billLink === 'function') return ctx.billLink(b, { date: date });
    return '<a data-bill="' + ctx.esc(b) + '" data-date="' + ctx.esc(String(date || '').slice(0, 10)) + '">' + ctx.esc(b) + '</a>';
  }
  function dash(){ return '<span class="sub">—</span>'; }

  function rangeWords(st){
    var d = (st.f.date || [])[0];
    if (!d) return '';
    if (d === 'c'){ var a = st.f.date[1], z = st.f.date[2]; return a && z ? ' between ' + a + ' and ' + z : a ? ' since ' + a : ' through ' + z; }
    var m = { '30d': '30 days', '3m': '3 months', '6m': '6 months', '12m': '12 months', '24m': '24 months', '5y': '5 years' };
    return m[d] ? ' in the last ' + m[d] : '';
  }

  var list = {
    noun: ['reporter', 'reporters'], title: 'Reporters',
    cap: 'Who wrote about him, from the stories that pass the filters (his own op-eds left out). A reporter’s outlets are the outlets of their own original stories, never outlets that reprinted them. Names and outlets only: the tracker has no contact details. Tone average is over rated stories. Click a name to open the reporter’s page.',
    placeholder: 'Search reporters, outlets',
    units: units, group: group,
    key: function(o){ return o.key; },
    text: function(o){ return o.name + ' | ' + o.outlets.join(' | ') + (o.also && o.also.length ? ' | ' + o.also.join(' | ') : ''); },   /* v23-REPQ: search still finds them */
    facets: [
      { key: 'date', label: 'Date range', type: 'date', level: 'unit', date: function(u){ return u.date; }, hint: 'Stories dated in this range. Every count in the list is over these stories.' },
      { key: 'byline', label: 'Byline type', level: 'item', mini: 'People', open: true, order: KIND_ORDER, vals: function(o){ return o.kindLabel; },
        hint: 'Staff bylines are unsigned staff and newsroom credits, such as Daily News Staff.' },
      { key: 'iss', label: 'Issue', level: 'unit', open: true, vals: function(u){ return u.topic; }, sw: function(v){ return C ? C.colorFor('topic', v) : ''; } },
      { key: 'bill', label: 'Bill', level: 'unit', search: true, limit: 8, vals: function(u){ return u.bills; }, note: function(v){ return C ? C.billName(v) : ''; },
        hint: 'Gabriel bills the story covers.' },
      { key: 'outlet', label: 'Outlet', level: 'unit', search: true, limit: 8, vals: function(u){ return u.affs; }, hint: 'The outlets reporters wrote for (their Original stories). Outlets that only reprinted a story are not listed.' },
      { key: 'aud', label: 'Reach', level: 'unit', vals: function(u){ return u.reach; }, sw: function(v){ return C ? C.colorFor('reach', v) : ''; }, hint: 'The kind of outlet that ran the story.' },
      { key: 'med', label: 'Medium', level: 'unit', vals: function(u){ return u.media; } },
      { key: 'lng', label: 'Language', level: 'unit', vals: function(u){ return u.lang; } },
      { key: 'n', label: 'Story count', type: 'one', any: 'Any number', options: [
        { id: '10', label: '10 or more', test: function(o){ return o.stories >= 10; } },
        { id: '5', label: '5 to 9', test: function(o){ return o.stories >= 5 && o.stories < 10; } },
        { id: '2', label: '2 to 4', test: function(o){ return o.stories >= 2 && o.stories < 5; } },
        { id: '1', label: '1', test: function(o){ return o.stories === 1; } }] },
      { key: 'tmix', label: 'Tone', type: 'one', any: 'Any tone', hint: 'Over the rated stories in the list’s range.', options: [
        { id: 'neg', label: 'Any negative story', test: function(o){ return o.neg > 0; } },
        { id: 'noneg', label: 'No negative story', test: function(o){ return o.neg === 0; } },
        { id: 'below', label: 'Average below neutral', test: function(o){ return o.tone.n > 0 && o.tone.avg < 0; } },
        { id: 'above', label: 'Average above neutral', test: function(o){ return o.tone.n > 0 && o.tone.avg > 0; } },
        { id: 'unrated', label: 'No rated story', test: function(o){ return !o.tone.n; } }] },
      { key: 'active', label: 'Active within', type: 'date', level: 'item', date: function(o){ return o.last; }, hint: 'Latest story (within the other filters) in this period.' }
    ],
    columns: [
      { key: 'name', label: 'Reporter', val: function(o){ return o.name; },
        cell: function(o, ctx){ return '<button type="button" class="linkbtn tt-open">' + ctx.esc(o.name) + '</button>' + (o.kind !== 'person' ? '<div class="sub">' + ctx.esc(KIND_ONE[o.kind] || '') + '</div>' : ''); } },
      { key: 'outlets', label: 'Outlets', val: function(o){ return o.outlets.join('; '); }, sort: function(o){ return o.outlets[0] || ''; }, cell: outletCell },
      { key: 'stories', label: 'Stories', num: true, dir: -1, val: function(o){ return o.stories; }, cell: function(o, ctx){ return ctx.fmt(o.stories); } },
      { key: 'last', label: 'Last story', dir: -1, cls: 'nw', val: function(o){ return o.last; }, cell: function(o, ctx){ return storyBtn(o.lastR, ctx); } },
      { key: 'topics', label: 'Top issues', val: function(o){ return o.topics.join('; '); }, sort: function(o){ return o.topics[0] || ''; },
        cell: function(o, ctx){ return o.topics.length ? o.topics.map(function(t){ return ctx.issueLink ? ctx.issueLink(t) : ctx.esc(t); }).join(', ') : dash(); } },
      { key: 'tone', label: 'Tone avg', num: true, dir: 1, cls: 'nw', val: function(o){ return o.tone.text; }, sort: function(o){ return o.tone.n ? o.tone.avg : null; },
        cell: function(o, ctx){ return o.tone.n ? ctx.toneHtml(o.tone) : dash(); }, csv: function(o){ return o.tone.csv; }, csvLabel: 'Tone average (−2 to +2)' },
      { key: 'neg', label: 'Negative', num: true, dir: -1, val: function(o){ return o.neg; }, cell: function(o, ctx){ return o.neg ? ctx.fmt(o.neg) : '<span class="sub">0</span>'; }, csvLabel: 'Negative stories' }
    ],
    csvExtra: [['Tone label', function(o){ return o.tone.label; }], ['Rated stories', function(o){ return o.tone.n; }], ['Byline type', function(o){ return o.kindLabel; }], ['Title (sheet)', function(o){ return o.titleList.join('; '); }],
      ['Bills', function(o){ return o.billList.join('; '); }], ['Last headline', function(o){ return o.lastR ? o.lastR.hl : ''; }]],
    sort: { key: 'stories', dir: -1 }, step: { desk: 100, phone: 25 }, open: 'page',
    answer: function(res, st, ctx){
      var iss = st.f.iss || [], on = iss.length ? ' on ' + iss.join(' or ') : '';
      if (!res.length) return '';
      var top = res.slice().sort(function(a, b){ return b.stories - a.stories || (b.last < a.last ? -1 : 1); }).slice(0, 3)
        .map(function(o){ return o.name + (o.outlets[0] ? ', ' + o.outlets[0] : '') + ' (' + o.stories + ')'; });
      var nPeople = res.filter(function(o){ return o.kind === 'person' || o.kind === 'contributor'; }).length, nOther = res.length - nPeople;
      return ctx.pl(nPeople, 'reporter', 'reporters') + (nOther ? ' (plus ' + ctx.pl(nOther, 'staff byline, wire or organization', 'staff bylines, wires and organizations') + ')' : '') + ' wrote about him' + on + rangeWords(st) + '. Most stories: ' +
        (top.length < 2 ? top[0] : top.slice(0, -1).join('; ') + ' and ' + top[top.length - 1]) + '.';
    },
    empty: function(st){ return 'No reporter matches these filters.'; },
    copies: [{ label: 'Copy names', sub: 'Every reporter listed, one “Name (Outlet)” per line',
      text: function(res){ return res.map(function(o){ return o.name + (o.outlets[0] ? ' (' + o.outlets[0] + ')' : ''); }).join('\n'); },
      ok: function(res){ return 'Copied ' + res.length + (res.length === 1 ? ' name' : ' names'); } }],
    csvName: function(st, ctx){ var iss = (st.f.iss || []).join(' ').replace(/[\\/:*?"<>|]+/g, '-'); return 'AJG reporters' + (iss ? ' ' + iss : '') + ' ' + ctx.TODAY + '.csv'; }
  };

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
    slug: function(o, ctx){ return slugOf(o.key, ctx); },
    scope: function(o){ return { sel: { author: [o.name] }, label: o.name }; },   /* LINKSCOPE-v1: this reporter in Clips */
    find: function(sub, ctx){ everyone(ctx); return memo.bySlug.get(sub) || memo.bySlug.get(ctx.slug(sub)) || null; },
    spec: function(o, ctx){
      var e = ctx.esc, first = o.rs.reduce(function(a, r){ return !a || r.date < a.date ? r : a; }, null);
      var ids = {}; o.rs.forEach(function(r){ ids[r.id] = 1; });
      var langs = byCount(o.langs);
      var cnt = function(n){ return ' <span class="sub">' + ctx.fmt(n) + '</span>'; };
      /* HEADER-v2 clusters: Who (outlets, title, languages) / What (issues, bills) / Coverage (counts, tone, dates) */
      var who = [['Outlets', ctx.hlist(o.outlets.map(function(x){ return ctx.pageLink('outlets', ctx.outletSub ? (ctx.outletSub(x) || ctx.slug(x)) : ctx.slug(x), x, 'Open the outlet page') + cnt(o.out.get(x)); }), 4)]];
      if (o.also && o.also.length) who.push(['Also wrote for', ctx.hlist(o.also.map(function(x){ return ctx.pageLink('outlets', ctx.outletSub ? (ctx.outletSub(x) || ctx.slug(x)) : ctx.slug(x), x, 'Open the outlet page'); }), 4)]);   /* v23-REPQ */
      if (o.ranIn && o.ranIn.length) who.push(['Ran in', ctx.hlist(o.ranIn.map(function(x){ return ctx.pageLink('outlets', ctx.outletSub ? (ctx.outletSub(x) || ctx.slug(x)) : ctx.slug(x), x, 'Open the outlet page'); }), 4)]);   /* v23-REPQ: wire copy run by these outlets */
      if (o.titleList.length) who.push(['Title', ctx.hlist(o.titleList.map(e), 3)]);
      if (langs.length > 1 || (langs[0] && langs[0] !== 'English')) who.push(['Languages', ctx.hlist(langs.map(function(l){ return (ctx.facetLink ? ctx.facetLink('lang', l) : e(l)) + cnt(o.langs.get(l)); }))]);
      var what = [['Top issues', ctx.hlist(o.topics.map(function(t){ return ctx.issueLink ? ctx.issueLink(t) : e(t); }))],
        ['Bills', ctx.hlist(o.billList.map(function(b){ return billLink(b, o.billDate[b], ctx) + cnt(o.bills.get(b)); }), 5)]];
      var cov = [['Stories', ctx.fmt(o.stories)],
        ['Tone average', o.tone.n ? ctx.toneHtml(o.tone) : '<span class="sub">No rated story</span>'],
        ['Negative stories', ctx.fmt(o.neg)],
        ['Last story', o.lastR ? storyBtn(o.lastR, ctx) + '<div class="sub">' + e(o.lastR.hl || '') + '</div>' : ''],
        ['First story', first ? storyBtn(first, ctx) : '']];
      if (o.ranList.length) cov.push(['Picked up by', ctx.pl(o.ranList.length, 'other outlet', 'other outlets') + ' <span class="sub">reprints or re-runs; not the reporter’s outlets</span>']);
      var rf = relFact(o.rs, ctx); if (rf) what.push(rf);
      var facts = who.concat(what, cov);
      return { kicker: [KIND_ONE[o.kind] || 'Reporter', o.outlets.length ? o.outlets[0] : ''], title: o.name, noun: 'reporter', backLabel: 'All reporters',
        groups: [{ key: 'who', label: 'Who', facts: who }, { key: 'what', label: 'What', facts: what }, { key: 'coverage', label: 'Coverage', facts: cov }], groupLabels: false,   /* NOGLABEL-v1 */
        dek: ctx.pl(o.stories, 'story', 'stories') + ' mentioning Gabriel' + (first && o.lastR ? ', ' + e(ctx.dateLabel(first)) + (first.id !== o.lastR.id ? ' to ' + e(ctx.dateLabel(o.lastR)) : '') : '') + '. Every story, whatever the list’s filters.',
        /* EMBEDROWS-v1: the Outlets tab's own rows for the outlets this reporter's stories ran in first (no more text list) */
        embeds: [{ tab: 'outlets', title: 'Outlets', cap: 'The Outlets tab’s rows for the outlets this reporter wrote for (their original stories; outlets that only reprinted them are left out), counted over those stories. Click an outlet for its page.',
          unit: function(u){ return u.kind === 'Original' && !!ids[u.r.id] && (!ctx.affOf || ctx.affOf(u.r, o.name) === u.o) && !(o.also && o.also.indexOf(u.o) >= 0); }, cols: ['name', 'pub', 'n', 'last', 'iss', 'tone', 'neg'] }],
        facts: facts, rows: o.rs.slice(), placeholder: 'Search ' + ctx.pl(o.stories, 'story', 'stories') + ' by ' + o.name };
    }
  };

  AJGTabs.register({
    id: 'reporters', list: list, page: page,
    /* old Pitch / Insights links: author -> the reporter's page when known (else a search for the name); issue -> the filter */
    legacy: function(p, ctx){
      var q = {}, sub = '';
      if (p.author){
        everyone(ctx);
        var k = ctx.authorKey(ctx.canonAuthors([p.author])[0] || p.author);
        if (memo.slugs.has(k)){ sub = memo.slugs.get(k); if (p.issue) q.topic = p.issue; return { params: q, sub: sub }; }
        q.q = p.author;
      }
      if (p.issue) q.iss = p.issue;
      return { params: q, sub: '' };
    }
  });
})();
