/* RELRECS-v1 (Sammy 2026-11-02: R1, R2, R3, R5 facet only): "Picked up" leads (one number per release = related stories that are not wire
   and not reposts + copies at real outlets, FINDINGS definition D; tab-releases "nw" lists the wire / distributor / prservice /
   aggregator outlets); "Ran it" (copies) is the second number. Reporter and outlet facets + CSV columns from the related stories;
   a releases-per-quarter chart (ctx.timeChart, TIMEAXIS-v1) under the filter chips; the Pickup facet (nothing after 7 / 30 days).
   window.AJGRelPick(ctx, key) gives the Bills tab the same numbers.
   TABS-v1 Press releases tab (agent-tab-releases, 2026-10-27). Replaces Insights › Press releases (release_pickup.js).
   One row per release in ins-release_pickup (the sheet's Press releases tab in scope: Gabriel's office always, Jewish Caucus
   from the tenure date, plus the releases outlets ran that are not posted officially). Copies ("Ran it") = the sheet rows
   that are the release (RELRULE-v1 / EXCERPT-v1 / RELCOPIES-v2); they are not tracker stories. Type / quoted / dek / source
   from ins-release_pickup's appended columns when present, else tab-releases (releases_data.py). Search: title + dek, plus
   the full release text (data/release_texts.json, fetched once, the first time someone searches or opens a release page).
   RELRELATED-v1..v3: related stories come only from build-time evidence (code/relmatch.py -> tab-releases "rel": {Release ID
   or key: [[Story ID, type, days after], ...]}); the tier of a type (rules.t[type][0]) decides the section: 1 = Related
   stories (the list), 2 = Possibly related (collapsed), 3 = Later coverage.
   RELUI-v1 (rp-ui 2026-10-28, RELPLAN phase 2: UI review items 1-6, 8-11; backend review #8-#10): no rule paragraphs on the
   page. Every rule text (row tags, labels, ⓘ tooltips) comes from tab-releases "rules" (releases_data.py, built from
   relmatch / release_rule / relcopy constants); nothing here types a threshold. Release page, top to bottom: header (kicker
   type · date · source; title and [Read release] open the release in the viewer; official link; word count; an ~80-word
   lead at >= 1100 px; facts Who / What / Coverage incl. the milestone label and bill coverage from "bc"), "Ran the release"
   (copies, only when there are any), "Related stories" (heading + one-line breakdown + the list with a per-row evidence tag,
   "How it's related" chips, strongest link first; no chart), "Later coverage", "Other releases on this bill" (thr threads
   and pairs), "Possibly related" (collapsed). People (Others named, Joint with) come from thr (rp-threads RELTHREAD-v1). */
(function(){ "use strict";
  var TEXTS = 'data/release_texts.json';
  var SRC = { o: 'Gabriel’s office', c: 'Jewish Caucus', oc: 'Both sites', '': 'Not posted officially' };
  var SRC_ORDER = ['Gabriel’s office', 'Jewish Caucus', 'Both sites', 'Not posted officially'];
  /* display order of evidence (strongest first); unknown types go last */
  var RANK = ['nearcopy', 'text', 'quote', 'anchor', 'pre', 'bill', 'topic', 'roundup', 'laterquote', 'later', 'subject', 'possible'];   /* v23: roundup, subject */
  var M = { v: null, items: null, bySlug: null, byKey: null, R: null, thr: null, people: [], nw: null }, FT = { state: 'idle', map: null }, cur = { q: '', ctx: null };

  function dayNum(iso){ var p = iso.split('-'); return Date.UTC(+p[0], +p[1] - 1, +p[2]) / 864e5; }
  function lagOf(d0, d){ return (d0 && d && d.length >= 10 && d0.length >= 10) ? Math.round(dayNum(d.slice(0, 10)) - dayNum(d0.slice(0, 10))) : null; }
  function lagTxt(n){ return n == null ? '' : n === 0 ? 'same day' : (n > 0 ? '+' : '−') + Math.abs(n) + (Math.abs(n) === 1 ? ' day' : ' days'); }
  function srcCode(v){ var s = String(v || '').toLowerCase(); if (s === 'o' || s === 'c' || s === 'oc') return s;
    var o = /office|asmdc/.test(s), c = /caucus/.test(s); return o || c ? (o ? 'o' : '') + (c ? 'c' : '') : null; }
  function rk(t){ var i = RANK.indexOf(t); return i < 0 ? RANK.length : i; }
  /* the rules table (tab-releases "rules"); a build without it falls back to the type name and tiers by name */
  function tierOf(t){ var R = M.R; if (R && R.t && R.t[t]) return R.t[t][0]; return (t === 'possible' || t === 'subject') ? 2 : (t === 'later' || t === 'laterquote') ? 3 : 1; }
  function tagOf(t){ var R = M.R; return (R && R.t && R.t[t] && R.t[t][2]) || t; }
  function labelOf(t){ var R = M.R; return (R && R.t && R.t[t] && R.t[t][1]) || t; }
  function howOf(t){ var R = M.R; return (R && R.t && R.t[t] && R.t[t][3]) || ''; }
  function cap1(s){ s = String(s || ''); return s ? s[0].toUpperCase() + s.slice(1) : s; }
  function ruleLines(types){ return types.filter(function(t){ return howOf(t); }).map(function(t){ return tagOf(t) + ': ' + howOf(t) + '.'; }).join('\n'); }
  function info(ctx, text, about){ return ctx.info ? ctx.info(text, about) : ''; }

  function prep(ctx){
    if (M.v === ctx.version && M.items) return M.items;
    var blk = ctx.block('release_pickup'), tb = ctx.block('releases') || { r: {}, c: {} };
    if (!blk || !blk.rel){ M = { v: ctx.version, items: [], bySlug: new Map(), byKey: new Map(), R: null, thr: null, people: [] }; return M.items; }
    M.R = tb.rules || null; M.thr = tb.thr || null; M.nw = new Set(tb.nw || []);
    var NW = M.nw; M.tenure = (M.R && M.R.tenure) || blk.tenure || '';
    var cols = blk.cols || [], ci = function(n){ return cols.indexOf(n); };
    var iT = ci('type'), iQ = ci('quoted'), iDk = ci('dek'), iS = ci('source'), iP = ci('prid');
    var thr = M.thr || {}, TX = thr.x || {}, PP = thr.pp || [], TH = thr.th || [];
    var pName = function(i){ var p = PP[i]; return p ? p[1] : ''; };
    var items = blk.rel.map(function(t){
      var url = t[9] || '', x = tb.r[url] || [], it = { key: t[0], date: t[1] || '', iss: t[2], title: t[3] || '(untitled release)',
        bills: (t[4] || []).slice(), topic: t[5] || '', sids: t[7] || [], url: url, official: !!t[10] };
      it.type = (iT >= 0 ? t[iT] : x[0]) || 'Press release';
      it.quoted = (iQ >= 0 ? t[iQ] : x[1]) || '';
      it.dek = (iDk >= 0 ? t[iDk] : x[2]) || '';
      var sc = it.official ? srcCode(iS >= 0 ? t[iS] : x[3]) : '';
      if (sc == null) sc = it.iss === 'c' ? 'c' : 'o';
      it.src = SRC[sc]; it.wc = x[5] || '';
      it.prid = (iP >= 0 ? t[iP] : '') || x[6] || ''; it.saved = !!x[7];
      it.copies = (t[8] || []).map(function(q){ var c = tb.c[q[0]] || [];
        return { aid: q[0], raw: q[1], outlet: ctx.outlet(q[1], q[0]), date: q[2] || '', kind: q[3], lag: lagOf(it.date, q[2]), hl: c[0] || '', plink: c[1] || '', link: c[2] || '', pq: c[3] || '', sid: c[4] || '' }; });
      var seen = {}; it.outlets = [];
      it.copies.forEach(function(q){ if (!seen[q.outlet]){ seen[q.outlet] = 1; it.outlets.push(q.outlet); } });
      it.n = it.copies.length;
      /* evidence rows by tier: 1 related, 2 possibly related, 3 later coverage (one row per story, the strongest) */
      var rr = (tb.rel || {})[it.prid || it.key] || [], best = new Map();
      rr.forEach(function(x){ var r = ctx.byId(x[0]); if (!r) return; var o = best.get(x[0]); if (!o || rk(x[1]) < rk(o.type)) best.set(x[0], { r: r, type: String(x[1] || ''), lag: x[2] }); });
      it.related = []; it.possible = []; it.later = []; it.ev = best;
      best.forEach(function(e){ var n = tierOf(e.type); (n === 2 ? it.possible : n === 3 ? it.later : it.related).push(e); });
      /* RELRECS-v1 R1: Picked up = related stories that are not wire and not reposts (not a wire / distributor / prservice / aggregator
         outlet, Medium not Wire, evidence not nearcopy) + copies at outlets that are not one of those. R2: the reporters and outlets of the related stories */
      var reps = [], outs = [], seenR = {}, seenO = {};
      it.nRelPick = 0;
      it.related.forEach(function(e){ var r = e.r, o = ctx.outlet(r.outlet, r.aid);
        if (e.type !== 'nearcopy' && r.media !== 'Wire' && !NW.has(o)) it.nRelPick++;
        if (o && !seenO[o]){ seenO[o] = 1; outs.push(o); }
        (r.authors || []).forEach(function(a){ a = String(a || '').trim(); var k = a && ctx.authorKey ? ctx.authorKey(a) : '';
          if (!k || k === 'jesse gabriel' || seenR[k] || (ctx.authorKind && ctx.authorKind(a) !== 'person')) return;
          seenR[k] = 1; reps.push(String(ctx.canonAuthors ? ctx.canonAuthors([a])[0] || a : a).replace(/([a-z])([’'])S\b/g, '$1$2s')); }); });
      it.relReporters = reps; it.relOutlets = outs;
      it.nCopyPick = it.copies.filter(function(q){ return !NW.has(q.outlet); }).length;
      it.picked = it.nRelPick + it.nCopyPick;
      /* RELTHREAD-v1 people, milestone, threads, pairs */
      var tx = TX[it.prid || it.key] || {};
      it.named = (tx.n || []).map(function(i){ return { i: i, title: (PP[i] || [])[0] || '', name: pName(i) }; }).filter(function(p){ return p.name; });
      if (!M.thr && x[4]) it.named = x[4].split(/;\s*/).filter(Boolean).map(function(n){ return { i: -1, title: '', name: n }; });
      it.joint = (tx.j || []).map(pName).filter(Boolean);
      it.namedF = it.named.filter(function(p){ return p.i >= 0 && (PP[p.i] || [])[3] >= 3; }).map(function(p){ return p.name; });
      it.m = tx.m || null; it.bg = tx.bg || []; it.nb = tx.nb || 0; it.pairs = tx.p || [];
      it.threads = (tx.t || []).map(function(i){ return TH[i]; }).filter(Boolean);
      it.bc = (tb.bc || {})[it.prid || it.key] || null;
      return it;
    });
    var bySlug = new Map(), byKey = new Map();
    items.slice().sort(function(a, b){ return a.date.localeCompare(b.date) || a.key.localeCompare(b.key); }).forEach(function(it){
      var base = ctx.slug((it.date || 'undated') + ' ' + it.title.split(/\s+/).slice(0, 8).join(' ')), s = base, k = 2;
      while (bySlug.has(s)) s = base + '-' + (k++);
      it.old = s; it.slug = it.prid || s; bySlug.set(s, it); if (it.prid) bySlug.set(it.prid, it); });   /* RELCOPIES-v1: #press-releases/<prid>; the old date-title slug still finds it */
    items.forEach(function(it){ byKey.set(it.prid || it.key, it); byKey.set(it.key, it); });
    M = { v: ctx.version, items: items, bySlug: bySlug, byKey: byKey, R: M.R, thr: M.thr, tenure: M.tenure, nw: NW };
    return items;
  }

  /* RELRECS-v1 R1: the Bills tab's per-release line reads the same numbers (one definition of "Picked up") */
  window.AJGRelPick = function(ctx, key){ var its = prep(ctx), it = M.byKey && M.byKey.get(key);
    return it ? { picked: it.picked, related: it.related.length, copies: it.n } : null; };

  /* ---- full release text: fetched once, lazily ---- */
  function loadTexts(){
    if (FT.state !== 'idle') return;
    FT.state = 'loading';
    var p;
    try { p = fetch(TEXTS, { cache: 'force-cache' }); } catch(e){ p = Promise.reject(e); }
    p.then(function(r){ if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }).then(function(j){
      var src = (j && (j.rel || j.t)) || j || {}, m = new Map();
      Object.keys(src).forEach(function(u){ var v = src[u], s = typeof v === 'string' ? v : (v && v.body) || ''; if (s) m.set(u, s); });
      FT.map = m; FT.state = 'ready';
    }).catch(function(){ FT.state = 'failed'; }).then(function(){ fillLead(); redraw(); });
  }
  function redraw(){
    (M.items || []).forEach(function(it){ delete it.__tt; it.__td = null; });
    var c = cur.ctx, v = document.querySelector('#tbBody .tb-view[data-tb="releases"]:not([hidden])');
    if (!c || !v || !v.querySelector('.tt')) return;
    var a = document.activeElement, inp = v.querySelector('.tt-q'), had = a && a === inp, val = inp ? inp.value : '', pos = had ? inp.selectionStart : null;
    c.refresh();
    var n = document.querySelector('#tbBody .tb-view[data-tb="releases"]:not([hidden]) .tt-q');
    if (!n) return;
    if (n.value !== val){ n.value = val; n.dispatchEvent(new Event('input', { bubbles: true })); }
    if (had){ n.focus(); try { n.setSelectionRange(pos, pos); } catch(e){} }
  }
  function body(it){ return FT.map && it.url ? FT.map.get(it.url) || '' : ''; }
  function td(it, ctx){ return it.__td || (it.__td = ctx.fold(it.title + ' ' + it.dek)); }
  /* <= 20 words of the release text around the first body-only query word, matches marked (Clips' .ft-hit look) */
  function snippet(it, ctx){
    var ws = ctx.fold(cur.q).split(' ').filter(Boolean), b = body(it);
    if (!ws.length || !b || ws.every(function(w){ return td(it, ctx).indexOf(w) >= 0; })) return '';
    var only = ws.filter(function(w){ return td(it, ctx).indexOf(w) < 0; }), toks = b.split(/\s+/).filter(Boolean), ft = toks.map(ctx.fold);
    var at = ft.findIndex(function(t){ return only.some(function(w){ return t.indexOf(w) >= 0; }); });
    if (at < 0) return '';
    var a = Math.max(0, at - 8), z = Math.min(toks.length, a + 20); a = Math.max(0, z - 20);
    return '<div class="ft-hit">In the release text: “' + (a ? '…' : '') + toks.slice(a, z).map(function(t, k){
      return ws.some(function(w){ return ft[a + k].indexOf(w) >= 0; }) ? '<mark>' + ctx.esc(t) + '</mark>' : ctx.esc(t); }).join(' ') + (z < toks.length ? '…' : '') + '”</div>';
  }
  /* the release's first ~80 words under the header (wide screens; CSS hides it below 1100 px) */
  function fillLead(){
    var h = document.querySelector('#tbBody .rl-lead[data-rllead]'); if (!h || h.dataset.done) return;
    var it = M.byKey && M.byKey.get(h.dataset.rllead), b = it ? body(it) : '', e = cur.ctx ? cur.ctx.esc : function(s){ return s; };
    if (!b) return;
    /* REVIEW4-LEFTOVERS C12: saved releases repeat the title (and the dek) right after the date; lead with the first sentence that is neither */
    [it.title, it.dek].forEach(function(x){ x = String(x || '').trim(); if (x && b.indexOf(x) >= 0 && b.indexOf(x) < 400) b = (b.slice(0, b.indexOf(x)) + ' ' + b.slice(b.indexOf(x) + x.length)).replace(/\s+/g, ' ').trim(); });
    var ws = b.split(/\s+/).filter(Boolean), cut = ws.slice(0, 80).join(' ');
    h.dataset.done = '1';
    h.innerHTML = '<span class="rl-lead-t">“' + e(cut) + (ws.length > 80 ? ' …' : '') + '”</span> ' + (it.prid && hasCopy(it, cur.ctx) ? '<button type="button" class="linkbtn" data-relprev="' + e(it.prid) + '">Read the full release ›</button>' : '');
  }

  function dl(ctx, iso){ return iso ? ctx.dateLabel({ date: iso.slice(0, 10), prec: iso.length >= 10 ? 'day' : 'month' }) : 'No date'; }
  function host(u){ try { return new URL(u).hostname.replace(/^www\./, ''); } catch(x){ return ''; } }
  function chip(b, date, ctx){ return '<button type="button" class="bchip" data-bill="' + ctx.esc(b) + '" data-date="' + ctx.esc(String(date || '').slice(0, 10)) + '" title="Open the ' + ctx.esc(b) + ' page">' + ctx.esc(b) + '</button>'; }
  function chips(bills, date, ctx){ return bills.length ? '<span class="bchips">' + bills.map(function(b){ return chip(b, date, ctx); }).join('') + '</span>' : ''; }
  function outletA(name, ctx){ return ctx.pageLink('outlets', ctx.slug(name), name, name + ' in the Outlets tab'); }
  function relA(it, ctx, label){ return '<button type="button" class="linkbtn" data-tb-go="releases" data-tb-sub="' + ctx.esc(it.slug) + '" title="Open this release’s page">' + ctx.esc(label || it.title) + '</button>'; }
  function personA(name, key, ctx){ return '<button type="button" class="linkbtn" data-tb-go="releases" data-tb-p="' + ctx.esc(JSON.stringify((function(o){ o[key] = name; return o; })({}))) + '" title="Every release naming ' + ctx.esc(name) + '">' + ctx.esc(name) + '</button>'; }
  function zero(n, ctx){ return n ? ctx.fmt(n) : '<span class="sub" aria-label="none">–</span>'; }
  /* a tracker story row (Clips row style): headline opens the story panel, outlet -> outlet page, date, tag, links */
  function storyItem(e, ctx, order){
    var r = e.r, o = ctx.outlet(r.outlet, r.aid), t = '<button type="button" class="linkbtn" data-tbstory="' + ctx.esc(r.id) + '" data-tborder="' + ctx.esc(order) + '" title="Open the story">' + ctx.esc(r.hl || '(no headline)') + '</button>';
    return ctx.row({ title: t, meta: [outletA(o, ctx), ctx.esc(ctx.dateLabel(r)), tagHtml(e, ctx)], right: ctx.storyLinks(r) });
  }
  function tagHtml(e, ctx){ if (!e) return ''; var l = lagTxt(e.lag);
    return '<span class="rl-tag" data-ev="' + ctx.esc(e.type) + '" title="' + ctx.esc(labelOf(e.type) + (l ? ' · ' + l : '')) + '">' + ctx.esc(tagOf(e.type)) + '</span>' + (l ? '<span class="rl-lag">' + ctx.esc(l) + '</span>' : ''); }
  /* a release copy (a sheet row, not a tracker story): the saved copy opens in the viewer ("1 of N" over this release's copies) */
  function copyItem(q, it, ctx){
    var saved = q.kind === 'O' && q.sid && ctx.openSaved && ctx.hasSaved && ctx.hasSaved(q.sid), e = ctx.esc;
    var hl = e(q.hl || '(no headline in the sheet)');
    return ctx.row({ attrs: ' data-relcopy="' + e(q.aid) + '"', title: saved ? '<button type="button" class="linkbtn" data-relsaved="' + e(q.sid) + '" data-relaid="' + e(q.aid) + '" data-relof="' + e(it.slug) + '" title="Read this copy">' + hl + '</button>' : '<span>' + hl + '</span>',
      meta: [outletA(q.outlet, ctx), e(dl(ctx, q.date)), e(lagTxt(q.lag))], right: ctx.storyLinks({ plink: q.plink, link: q.link, pq: q.pq }) });
  }
  function evCount(it){
    var c = {}; it.related.forEach(function(x){ c[x.type] = (c[x.type] || 0) + 1; });
    return Object.keys(c).sort(function(a, b){ return rk(a) - rk(b); }).map(function(k){ return [k, c[k]]; });
  }

  /* RELRECS-v1 R3: releases per quarter, split picked up / not, over the releases the filters leave (Data's timeChart, TIMEAXIS-v1) */
  var CH = { show: 'n', res: null, ctx: null };
  function chartHtml(){
    return '<div class="card chartcard rl-chart"><h2 class="sec rl-ctitle">Releases by quarter</h2><div class="cap rl-ccap"></div><div class="legend rl-cleg"></div><div class="chart rl-cchart"></div><div class="rl-cnote cap" hidden></div>'
      + '<div class="an-controls rl-copts"><label>Show<select data-rlc="show"><option value="n">Number</option><option value="pct">Share of releases</option></select></label>'
      + '<label hidden><input type="checkbox" data-rlc="avg"></label><label hidden><select data-rlc="only"></select></label></div>'
      + '<details class="dt"><summary>Show the numbers</summary><div class="rl-ctable" style="overflow-x:auto"></div></details></div>';
  }
  function qEnd(y, q){ return y + '-' + String(q * 3).padStart(2, '0') + '-' + (q === 1 || q === 4 ? '31' : '30'); }
  function drawChart(el){
    var res = CH.res || [], ctx = CH.ctx, q = function(s){ return el.querySelector(s); }, note = q('.rl-cnote'), chart = q('.rl-cchart');
    if (!q('.rl-chart') || !ctx || !ctx.timeChart) return;
    var rows = res.filter(function(it){ return /^\d{4}/.test(it.date); }).map(function(it){
      return { id: it.key, date: it.date, prec: it.date.length >= 10 ? 'day' : 'year', year: +it.date.slice(0, 4), pickup: it.picked ? 'Picked up' : 'Not picked up' }; });
    var per = {}; rows.forEach(function(r){ per[r.date.slice(0, 4) + '-Q' + Math.ceil((+r.date.slice(5, 7) || 1) / 3)] = 1; });
    var np = Object.keys(per).length, parts = ['.rl-cchart', '.rl-cleg', '.rl-copts', '.dt', '.rl-ccap'];
    q('.rl-chart select[data-rlc="show"]').value = CH.show;
    if (np < 2){   /* CHARTRULE-v1: no chart that would be a single bar; a sentence instead */
      parts.forEach(function(k){ var x = q(k); if (x) x.hidden = true; });
      note.hidden = false;
      note.textContent = !rows.length ? 'No dated releases match these filters, so there is nothing to chart.' : 'All ' + ctx.pl(rows.length, 'release', 'releases') + ' here went out in ' + Object.keys(per)[0].replace('-', ' ') + ', so there is no chart.';
      return;
    }
    parts.forEach(function(k){ var x = q(k); if (x) x.hidden = false; }); note.hidden = true; note.textContent = '';
    var y0 = Math.min.apply(null, rows.map(function(r){ return r.year; })), pk = rows.filter(function(r){ return r.pickup === 'Picked up'; }).length, pct = CH.show === 'pct';
    ctx.timeChart(rows, { iv: 'quarter', bk: 'pickup', meas: 'stories', from: y0, pct: pct, avgOn: false, avgEl: q('[data-rlc="avg"]'), onlyEl: q('[data-rlc="only"]'),
      title: q('.rl-ctitle'), cap: q('.rl-ccap'), legend: q('.rl-cleg'), chart: chart, table: q('.rl-ctable'), quick: false, foot: 'Click to list this quarter’s releases',
      pick: function(b){ var m = /^(\d{4})-Q(\d)$/.exec(b); if (!m || !CH.ctx) return; var n = +m[2];
        CH.ctx.go('releases', Object.assign({}, CH.ctx.params, { date: 'c:' + m[1] + '-' + String(n * 3 - 2).padStart(2, '0') + '-01..' + qEnd(m[1], n) })); } });
    Array.prototype.forEach.call(el.querySelectorAll('.rl-ctable th'), function(th){ if (th.textContent === 'Other') th.textContent = 'Not picked up'; });
    q('.rl-ctitle').textContent = pct ? 'Share of releases picked up, by quarter' : 'Releases by quarter';
    q('.rl-ccap').textContent = ctx.fmt(pk) + ' of ' + ctx.pl(rows.length, 'dated release', 'dated releases') + ' (' + Math.round(100 * pk / rows.length) + '%) picked up. “Picked up” leaves out wire services and reposts. Click a bar to list that quarter’s releases.';
  }

  var list = {
    noun: ['release', 'releases'], title: 'Press releases',
    get cap(){
      var c = cur.ctx, np = (M.items || []).filter(function(it){ return !it.official; }).length;
      return 'Releases from Gabriel’s office and the Jewish Caucus. '
        + (M.tenure && c ? 'Jewish Caucus releases count from ' + c.esc(dl(c, M.tenure)) + ', when he became its chair. ' : '')
        + (np ? 'Also lists ' + np + ' releases outlets ran that were never posted officially. ' : '')
        + '“Picked up” = related stories that are not wire or reposts, plus copies at real outlets; “Ran it” = outlets that printed the release itself; “Related” = tracker stories tied to it by evidence. Search covers the full text of each release.';
    },
    placeholder: 'Search release titles and text',
    items: function(ctx){ cur.ctx = ctx; return prep(ctx); },
    key: function(it){ return it.key; },
    text: function(it){ return it.title + ' ' + it.dek + ' ' + (it.prid || '') + ' ' + body(it); },
    facets: [
      { key: 'date', label: 'Date range', type: 'date', date: function(it){ return it.date; } },
      { key: 'src', label: 'Source', vals: function(it){ return it.src; }, order: SRC_ORDER, open: true },
      { key: 'type', label: 'Type', vals: function(it){ return it.type; } },
      { key: 'iss', label: 'Issue', vals: function(it){ return it.topic; }, search: true, limit: 8 },
      { key: 'bill', label: 'Bills', vals: function(it){ return it.bills; }, search: true, limit: 8 },
      { key: 'quoted', label: 'Gabriel quoted', vals: function(it){ return it.quoted; }, order: ['Yes', 'No'] },
      { key: 'quiet', label: 'Pickup', type: 'one', hint: 'Releases with nothing picked up (no related story that is not wire or a repost, no copy at a real outlet) after this many days.', options: [7, 30].map(function(d){
        return { id: String(d), label: 'Nothing after ' + d + ' days', test: function(it, ctx){ var c = ctx && ctx.cut0 ? ctx.cut0(d) : ''; return !it.picked && it.date.length >= 10 && !!c && it.date < c; } }; }) },
      { key: 'pick', label: 'Ran it', type: 'one', any: 'Any', options: [
        { id: 'yes', label: 'At least 1', test: function(it){ return it.n > 0; } },
        { id: 'no', label: 'None', test: function(it){ return !it.n; } },
        { id: '1', label: '1', test: function(it){ return it.n === 1; } },
        { id: '2', label: '2–3', test: function(it){ return it.n >= 2 && it.n <= 3; } },
        { id: '4', label: '4+', test: function(it){ return it.n >= 4; } }] },
      { key: 'rel', label: 'Related stories', type: 'one', options: [
        { id: 'yes', label: 'Some', test: function(it){ return it.related.length > 0; } },
        { id: 'no', label: 'None', test: function(it){ return !it.related.length; } }] },
      { key: 'pos', label: 'Possibly related', type: 'one', options: [
        { id: 'yes', label: 'Some', test: function(it){ return it.possible.length > 0; } },
        { id: 'no', label: 'None', test: function(it){ return !it.possible.length; } }] },
      { key: 'joint', label: 'Joint with', vals: function(it){ return it.joint; }, search: true, limit: 8 },
      { key: 'named', label: 'Others named', vals: function(it){ return it.namedF; }, search: true, limit: 8 },
      { key: 'outlet', label: 'Outlet that ran it', vals: function(it){ return it.outlets; }, search: true, limit: 8 },
      { key: 'rout', label: 'Outlet, related stories', vals: function(it){ return it.relOutlets; }, search: true, limit: 8 },
      { key: 'rrep', label: 'Reporter, related stories', vals: function(it){ return it.relReporters; }, search: true, limit: 8 }
    ],
    columns: [
      { key: 'title', label: 'Release', sortable: false, val: function(it){ return it.title; }, cell: function(it, ctx){
          var meta = (it.type && it.type !== 'Press release' ? '<span class="rl-type">' + ctx.esc(it.type) + '</span>' : '') + (it.topic ? '<span>' + ctx.esc(it.topic) + '</span>' : '') + chips(it.bills, it.date, ctx);
          var pm = [ctx.esc(dl(ctx, it.date)), ctx.esc(it.src), it.picked ? 'Picked up ' + ctx.fmt(it.picked) : 'Not picked up', it.n ? 'Ran it ' + ctx.fmt(it.n) : '', it.related.length ? 'Related ' + ctx.fmt(it.related.length) : ''].filter(Boolean).join(' · ');
          return '<button type="button" class="linkbtn tt-open">' + ctx.esc(it.title) + '</button>' + (meta ? '<div class="sub rl-sub">' + meta + '</div>' : '') + '<div class="sub rl-pm">' + pm + '</div>' + snippet(it, ctx); } },
      { key: 'date', label: 'Date', dir: -1, cls: 'nw rl-dk', val: function(it){ return it.date; }, cell: function(it, ctx){ return ctx.esc(dl(ctx, it.date)); } },
      { key: 'src', label: 'Source', cls: 'rl-dk', val: function(it){ return it.src; } },
      { key: 'pk', label: 'Picked up', num: true, dir: -1, cls: 'rl-dk', val: function(it){ return it.picked; }, cell: function(it, ctx){ return zero(it.picked, ctx); } },
      { key: 'n', label: 'Ran it', num: true, dir: -1, cls: 'rl-dk', val: function(it){ return it.n; }, cell: function(it, ctx){ return zero(it.n, ctx); } },
      { key: 'rel', label: 'Related', num: true, dir: -1, cls: 'rl-dk', val: function(it){ return it.related.length; }, cell: function(it, ctx){ return zero(it.related.length, ctx); } }
    ],
    sort: { key: 'date', dir: -1 }, open: 'page', step: { desk: 100, phone: 25 },
    answer: function(res, st, ctx){
      cur.q = st.q; cur.ctx = ctx;
      if (st.q && FT.state === 'idle') loadTexts();
      if (st.q && FT.state === 'loading') return 'Searching full text…';
      if (!res.length) return '';
      var np = res.filter(function(it){ return it.n; }).length, nc = res.reduce(function(s, it){ return s + it.n; }, 0), pk = res.filter(function(it){ return it.picked; }).length;
      return ctx.pl(res.length, 'release', 'releases') + ' · ' + Math.round(100 * pk / res.length) + '% picked up (' + ctx.fmt(pk) + ' of ' + ctx.fmt(res.length) + ') · ' + ctx.fmt(np) + ' run by outlets (' + ctx.pl(nc, 'copy', 'copies') + ') · '
        + ctx.fmt(res.filter(function(it){ return it.related.length; }).length) + ' with related stories'
        + (FT.state === 'failed' && st.q ? ' · Full text could not be loaded; searched titles and deks.' : '');
    },
    empty: function(){ return 'No releases match.'; },
    copies: [{ label: 'Copy titles and links', sub: 'Date, title and official link, one release per line',
      text: function(res, st, ctx){ return res.map(function(it){ return dl(ctx, it.date) + ' – ' + it.title + (it.url ? ' – ' + it.url : ''); }).join('\n'); } }],
    extra: function(el, res, ctx){
      CH.res = res; CH.ctx = ctx;
      if (!el.firstChild){ el.innerHTML = chartHtml();
        el.addEventListener('change', function(e){ var t = e.target; if (t && t.dataset && t.dataset.rlc === 'show'){ CH.show = t.value; drawChart(el); } }); }
      drawChart(el);
    },
    csvName: function(st, ctx){ return 'AJG press releases ' + ctx.TODAY + '.csv'; },
    csvExtra: [['Type', function(it){ return it.type; }], ['Issue', function(it){ return it.topic; }], ['Bills', function(it){ return it.bills.join('; '); }],
      ['Gabriel quoted', function(it){ return it.quoted; }], ['Dek', function(it){ return it.dek; }], ['Official link', function(it){ return it.url; }],
      ['Joint with', function(it){ return it.joint.join('; '); }], ['Others named', function(it){ return it.named.map(function(p){ return p.name; }).join('; '); }],
      ['Milestone', function(it){ return it.m ? it.m[0] + ' ' + it.m[3] + ' (' + it.m[1] + ')' : ''; }],
      ['Outlets that ran it', function(it){ return it.outlets.join('; '); }],
      ['Reporters of related stories', function(it){ return it.relReporters.join('; '); }], ['Outlets of related stories', function(it){ return it.relOutlets.join('; '); }],
      ['Possibly related stories', function(it){ return it.possible.length; }], ['Later coverage stories', function(it){ return it.later.length; }],
      ['Bill stories the week before', function(it){ return it.bc ? it.bc[0] : ''; }], ['Bill stories the week after', function(it){ return it.bc ? it.bc[1] : ''; }],
      ['Bill stories after, not linked', function(it){ return it.bc ? it.bc[2] : ''; }],
      ['Release key', function(it){ return it.key; }], ['Release ID', function(it){ return it.prid; }], ['Saved copy', function(it){ return hasCopy(it, cur.ctx) ? 'Yes' : 'No'; }]]
  };

  /* "Other releases on this bill": the release's threads (same bill + session) minus itself, plus text pairs */
  function threadHtml(it, ctx){
    var e = ctx.esc, out = [], done = {};
    done[it.prid || it.key] = 1;
    var relRow = function(o, extra){ var lg = lagOf(it.date, o.date), ms = (M.thr && M.thr.x && (M.thr.x[o.prid || o.key] || {}).m) || null;
      return ctx.row({ title: relA(o, ctx), meta: [e(dl(ctx, o.date)), lg == null ? '' : e(lg === 0 ? 'same day' : Math.abs(lg) + (Math.abs(lg) === 1 ? ' day ' : ' days ') + (lg < 0 ? 'before' : 'after')),
        ms ? '<span class="rl-ms">' + e(ms[3]) + '</span>' : ''].concat(extra || []) }); };
    var groups = it.threads.map(function(th){
      var rows = (th[2] || []).map(function(m){ return Array.isArray(m) ? { id: m[0], how: m[1] } : { id: m, how: '' }; })
        .filter(function(m){ return !done[m.id] && M.byKey.get(m.id); });
      rows.forEach(function(m){ done[m.id] = 1; });
      if (!rows.length) return '';
      var head = th[0].map(function(b){ return chip(b, it.date, ctx); }).join('') + '<span class="sub"> ' + e(String(th[1] || '').replace('-', '–')) + ' session · ' + ctx.pl(rows.length, 'other release', 'other releases') + '</span>';
      return '<div class="rl-thr"><div class="rl-thr-h">' + head + '</div><div class="clip-list">' + rows.map(function(m){
        return relRow(M.byKey.get(m.id), m.how ? ['<span class="rl-tag" title="' + e(m.how === 'r' ? 'The bill was renumbered; joined by the release text' : 'Names no bill; joined by the release text') + '">matched by text</span>'] : []); }).join('') + '</div></div>';
    }).filter(Boolean);
    var pairs = it.pairs.filter(function(p){ return !done[p[0]] && M.byKey.get(p[0]); });
    if (pairs.length) groups.push('<div class="rl-thr"><div class="rl-thr-h"><span class="sub">Similar releases</span></div><div class="clip-list">' + pairs.map(function(p){
      return relRow(M.byKey.get(p[0]), ['<span class="rl-tag">' + (p[1] === 'f' ? 'Follow-up' : 'Similar text') + '</span>']); }).join('') + '</div></div>');
    if (!groups.length) return '';
    var n = groups.length, h = '<h3 class="tb-us-h">Other releases on this bill</h3>';
    if (it.nb) return '<details class="card pad tbe-extra rl-sec rl-det"><summary class="tb-us-h">Other releases on these ' + ctx.fmt(it.nb) + ' bills</summary>' + groups.join('') + '</details>';
    return '<div class="card pad tbe-extra rl-sec"><div class="tb-us">' + h + groups.join('') + '</div></div>';
  }
  function readBtn(it, ctx){
    if (hasCopy(it, ctx) && ctx.openSaved) return '<button type="button" class="btn primary rl-read" data-relprev="' + ctx.esc(it.prid) + '">Read release</button>';
    var q = it.copies.filter(function(q){ return q.kind === 'O' && q.sid && ctx.hasSaved && ctx.hasSaved(q.sid); })[0];
    return q ? '<button type="button" class="btn primary rl-read" data-relsaved="' + ctx.esc(q.sid) + '" data-relaid="' + ctx.esc(q.aid) + '" data-relof="' + ctx.esc(it.slug) + '">Read it as ' + ctx.esc(q.outlet) + ' ran it</button>' : '';
  }

  var page = {
    slug: function(it){ return it.slug; },
    find: function(sub, ctx){ prep(ctx); cur.ctx = ctx; loadTexts(); var it = M.bySlug.get(sub) || null;
      /* RELCOPIES-v1: an old date-title link redirects to #press-releases/<prid> */
      if (it && it.prid && sub !== it.prid && ctx.openPage) setTimeout(function(){ ctx.openPage(it.prid); }, 0);
      return it; },
    spec: function(it, ctx){
      var e = ctx.esc, R = M.R || {}, rows = it.related.map(function(x){ return x.r; });
      var hl = function(a, n){ return ctx.hlist ? ctx.hlist(a, n) : a.join(', '); };
      /* header: button row under the dek (UI review #1) */
      var btns = readBtn(it, ctx) + (it.url ? ctx.link(it.url, 'Official release', host(it.url)) : '') + (it.wc && +it.wc ? '<span class="sub rl-wc">' + ctx.fmt(+it.wc) + ' words</span>' : '');
      var dek = (it.dek ? '<div>' + e(it.dek) + '</div>' : '') + (btns ? '<div class="rl-btns">' + btns + '</div>' : '') + '<div class="rl-lead" data-rllead="' + e(it.prid || it.key) + '"></div>';
      /* facts */
      var named = it.named.filter(function(p){ return it.joint.indexOf(p.name) < 0; }).map(function(p){ var a = it.namedF.indexOf(p.name) >= 0 ? personA(p.name, 'named', ctx) : e(p.name); return p.title ? '<span title="' + e(p.title + ' ' + p.name) + '">' + a + '</span>' : a; });
      var fWho = [['Joint with', hl(it.joint.map(function(n){ return personA(n, 'joint', ctx); }), 3)], ['Others named', hl(named, 3)], ['Gabriel quoted', e(it.quoted)]];
      var ms = it.m ? chip(it.m[0], it.date, ctx) + ' ' + e(it.m[3]) + ' <span class="sub">' + e(dl(ctx, it.m[1])) + (it.m[4] === 0 ? ', same day' : it.m[4] > 0 ? ', ' + it.m[4] + ' day' + (it.m[4] === 1 ? '' : 's') + ' before the release' : ', the day after the release') + '</span>' : '';
      var fWhat = [['Issue', ctx.issueLink ? ctx.issueLink(it.topic) : e(it.topic)],
        ['Bills', chips(it.bills.filter(function(b){ return it.bg.indexOf(b) < 0; }), it.date, ctx) + (it.bg.length ? '<span class="sub rl-bg">Also mentions ' + e(it.bg.join(', ')) + '</span>' : '')], ['Milestone', ms]];
      var ab = it.bills.filter(function(b){ return it.bg.indexOf(b) < 0; }), bcl = it.bc && ab.length ? 'Bill coverage' : '', bcb = ab.length === 1 ? ab[0] : 'these bills';   /* rp-final: plain words, detail in the ⓘ */
      var fCov = [['Picked up', ctx.fmt(it.picked) + ' <span class="sub">(' + ctx.pl(it.related.length, 'related story', 'related stories') + ', ' + ctx.pl(it.n, 'copy', 'copies') + ')</span>'
          + info(ctx, 'Related stories that are not wire services or reposts of the release, plus copies at outlets that are not wire or distribution services.', 'Picked up')],
        ['Ran it', it.n ? ctx.pl(it.n, 'copy', 'copies') + (it.outlets.length !== it.n ? ' <span class="sub">' + ctx.pl(it.outlets.length, 'outlet', 'outlets') + '</span>' : '') + info(ctx, R.copy ? 'Outlets that ' + R.copy + '.' : '', 'Ran it') : '0'],
        ['Related stories', ctx.fmt(it.related.length) + (it.possible.length ? ' <span class="sub">+ ' + ctx.fmt(it.possible.length) + ' possibly</span>' : '')],
        ['Later coverage', it.later.length ? ctx.fmt(it.later.length) : '']];
      if (bcl) fCov.push([bcl, (it.bc[1] ? ctx.pl(it.bc[1], 'story', 'stories') : 'No stories') + ' on ' + e(bcb) + ' that week'
        + info(ctx, ctx.pl(it.bc[0], 'story', 'stories') + ' the week before, ' + ctx.pl(it.bc[1], 'story', 'stories') + ' that week'
          + (it.bc[2] ? ' (' + ctx.fmt(it.bc[2]) + ' not linked to this release)' : '') + '. ' + (R.bch ? cap1(R.bch) + '.' : ''), bcl)]);
      /* sections (UI review #5): Ran the release, Related stories heading, [list], Later coverage, Other releases, Possibly related */
      var cards = '';
      if (it.n) cards += '<div class="card pad tbe-extra rl-sec"><div class="tb-us"><h3 class="tb-us-h">Ran the release · ' + ctx.fmt(it.n) + info(ctx, R.copy ? 'Outlets that ' + R.copy + '.' : '', 'Ran the release') + '</h3><div class="clip-list">'
        + it.copies.map(function(q){ return copyItem(q, it, ctx); }).join('') + '</div></div></div>';
      var ec = evCount(it);
      cards += rows.length
        ? '<div class="rl-relh"><h3 class="tb-us-h">Related stories · ' + ctx.fmt(rows.length) + info(ctx, ruleLines(ec.map(function(x){ return x[0]; })), 'Related stories') + '</h3><div class="rl-brk">'
          + ec.map(function(x){ return ctx.fmt(x[1]) + ' ' + e(tagOf(x[0]).toLowerCase()); }).join(' · ') + '</div></div>'
        : '<div class="card pad tbe-extra rl-sec"><div class="tb-us"><h3 class="tb-us-h">Related stories · 0</h3><div class="note">No related stories.</div></div></div>';
      var below = '';
      /* RELLATER-v1 (Sammy 2026-10-29): Later coverage and Possibly related list like Related stories (same row renderer, no links) */
      var xTable = function(k){ return '<div class="tablewrap"><table class="db tbe-tab tbe-xtab"><thead><tr><th class="c-d">Date</th><th class="c-h">Story</th>'
        + '<th class="c-t">Issue / Bill</th><th class="c-rc">Reach</th><th class="c-r" title="Other outlets that ran the same story">Reprints</th></tr></thead><tbody class="tbe-xbody" data-tbx="' + k + '"></tbody></table></div>'; };
      if (it.later.length){ var lo = it.later.slice().sort(function(a, b){ return (a.lag || 0) - (b.lag || 0); }), lid = lo.map(function(x){ return x.r.id; }).join(',');
        below += '<div class="card pad tbe-extra rl-sec"><div class="tb-us"><h3 class="tb-us-h">Later coverage · ' + ctx.fmt(lo.length) + info(ctx, ruleLines(['laterquote', 'later']), 'Later coverage') + '</h3>' + xTable('later') + '</div></div>'; }
      below += threadHtml(it, ctx);
      if (it.possible.length){ var po = it.possible.map(function(x){ return x.r.id; }).join(',');
        below += '<details class="card pad tbe-extra rl-sec rl-det"><summary class="tb-us-h">Possibly related · ' + ctx.fmt(it.possible.length) + info(ctx, howOf('possible') ? cap1(howOf('possible')) + '.' : '', 'Possibly related') + '</summary>' + xTable('possible') + '</details>'; }
      var how = { label: 'How it’s related', opts: ec.map(function(x){ return [x[0], tagOf(x[0])]; }), of: function(r){ var x = it.ev.get(r.id); return x ? x.type : ''; } };
      return { kicker: [it.type || 'Press release', dl(ctx, it.date), it.src], title: it.title, dek: dek, noun: 'release', backLabel: 'All press releases',
        placeholder: 'Search ' + ctx.pl(rows.length, 'related story', 'related stories'), chart: false, list: rows.length ? undefined : false,
        groups: [{ key: 'who', label: 'Who', facts: fWho }, { key: 'what', label: 'What', facts: fWhat }, { key: 'coverage', label: 'Coverage', facts: fCov }],
        facts: fWho.concat(fWhat, fCov), cards: cards, below: below, rows: rows,
        xrows: { later: it.later.slice().sort(function(a, b){ return (a.lag || 0) - (b.lag || 0); }).map(function(x){ return x.r; }), possible: it.possible.map(function(x){ return x.r; }) },
        noRelBadge: true, rowTag: function(r){ return tagHtml(it.ev.get(r.id), ctx); }, rank: function(r){ var x = it.ev.get(r.id); return x ? rk(x.type) : RANK.length; }, how: how,
        after: function(root){
          var h = root && root.querySelector('.tbh-title');
          if (h && hasCopy(it, ctx) && ctx.openSaved){ h.dataset.relprev = it.prid; h.classList.add('rl-tlink'); h.setAttribute('role', 'button'); h.tabIndex = 0; h.title = 'Read the release';
            h.addEventListener('keydown', function(ev){ if (ev.key === 'Enter' || ev.key === ' '){ ev.preventDefault(); h.click(); } }); }
          fillLead(); } };
    }
  };

  /* RELCOPIES-v1: the release's own saved copy (articles/releases.json, keyed by Release ID) opens in the story panel's viewer.
     RELUI-v1: the viewer steps through [the release, its saved copies]; a copy opened from "Ran the release" steps through the copies */
  function hasCopy(it, ctx){ return !!(it && it.prid && (it.saved || (ctx && ctx.hasSaved && ctx.hasSaved(it.prid)))); }
  function relMeta(it){ return { aid: '', hl: it.title, outlet: it.src, date: it.date, plink: it.url, link: '', pq: '', kind: 'release' }; }
  function copyMeta(q){ return { aid: q.aid, hl: q.hl, outlet: q.outlet, date: q.date, plink: q.plink, link: q.link, pq: q.pq }; }
  function savedCopies(it, ctx){ return it.copies.filter(function(q){ return q.kind === 'O' && q.sid && ctx.hasSaved && ctx.hasSaved(q.sid); }); }
  document.addEventListener('click', function(ev){
    var b = ev.target.closest && ev.target.closest('[data-relprev]'), c = cur.ctx;
    if (!b || !c || !c.openSaved) return; ev.preventDefault(); ev.stopPropagation();
    var it = M.bySlug && M.bySlug.get(b.dataset.relprev);
    if (it) c.openSaved(it.prid, relMeta(it), [[it.prid, relMeta(it)]].concat(savedCopies(it, c).map(function(q){ return [q.sid, copyMeta(q)]; })));
  });
  document.addEventListener('click', function(ev){
    var b = ev.target.closest && ev.target.closest('[data-relsaved]'), c = cur.ctx;
    if (!b || !c || !c.openSaved) return; ev.preventDefault(); ev.stopPropagation();
    var it = (b.dataset.relof && M.bySlug && M.bySlug.get(b.dataset.relof)) || null, q = null;
    (it ? [it] : (M.items || [])).some(function(x){ return x.copies.some(function(y){ if (y.aid === b.dataset.relaid){ q = y; it = x; return true; } return false; }); });
    if (q) c.openSaved(q.sid, copyMeta(q), savedCopies(it, c).map(function(y){ return [y.sid, copyMeta(y)]; }));
  });

  AJGTabs.register({
    id: 'releases', list: list, page: page,
    legacy: function(p, ctx){
      var its = prep(ctx), q = {};
      if (p.id){ var it = its.filter(function(x){ return x.key === p.id || x.prid === p.id || x.sids.indexOf(p.id) >= 0; })[0]; if (it) return { params: {}, sub: it.prid || it.slug }; }
      if (/^\d{4}$/.test(p.year || '')) q.date = 'c:' + p.year + '-01-01..' + p.year + '-12-31';
      if (p.topic) q.iss = p.topic;
      if (p.pick === 'yes' || p.pick === 'no') q.pick = p.pick;
      return { params: q, sub: '' };
    }
  });
})();
