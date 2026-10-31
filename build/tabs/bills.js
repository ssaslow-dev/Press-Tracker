/* Bills tab (agent-tab-bills, TABS-v1, 2026-10-27). Replaces Press desk › Bills (build/insights/bill_timeline.js).
   Items = Gabriel's author-led bills (LegInfo role "author…": author or co-lead; coauthored bills and Committee on Budget
   trailer bills are not his) from ctx.bills(), one item per bill AND session (a number reused across sessions, e.g.
   AB 787 2021–22 / 2023–24, is two bills). Milestones + final status: block ins-bill_timeline (the sheet's "Bills" tab
   snapshot). Releases: block ins-release_pickup (bills mentioned), own session only (RELSES-v1). Stories = ctx.D; a story goes to the latest session of
   its bill number that started (Dec 1 of the year before) on or before its date, the rule Data and the old view use.
   Bill page (#bills/<slug>): header facts, LegInfo history link, milestone timeline with stories per week, milestone
   table, related releases, then the framework's coverage chart and story list. Nothing here jumps to Clips. */
(function(){ "use strict";
  var MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var KIND = { introduced: 'Introduced', committee: 'Committee vote', floor: 'Floor vote', signed: 'Signed by Governor', vetoed: 'Vetoed', chaptered: 'Chaptered', died: 'Died' };
  var KIND_ORDER = ['Introduced', 'Committee vote', 'Floor vote', 'Signed by Governor', 'Vetoed', 'Chaptered', 'Died'];
  var RULE = { introduced: 1, floor: 1, signed: 1, vetoed: 1, chaptered: 1, died: 1 };
  var FINAL = { signed: 'Signed by Governor', vetoed: 'Vetoed', chaptered: 'Chaptered', died: 'Died' };
  var STATUS_ORDER = ['Signed into law', 'Vetoed', 'Adopted', 'Pending', 'Died'];
  var ISSUER = { o: "Gabriel's office", b: 'Budget chair', c: 'Jewish Caucus' };
  var memo = { v: null, M: null }, CTX = null, GEO = new Map();

  /* RELSES-v1: how a listed release relates to the bill, when it doesn't simply name it */
  var relHow = function(r){ return r.later ? '<span class="note" title="A release from a later session that names the bill in its title (a law taking effect, an anniversary)">Later release</span>' : r.how === 'i' ? '<span class="note" title="The release names no bill; it continues this bill’s thread by text">Matched by text</span>' : r.how === 'r' ? '<span class="note" title="Announced under another bill number; joined to this bill’s thread by text">Renumbered bill</span>' : r.bg ? '<span class="note" title="Names the bill as background (the bill was already done)">Background mention</span>' : ''; };
  var bkey = function(b){ return String(b || '').toUpperCase().replace(/[^A-Z0-9]/g, ''); };
  /* RELSES-v2 (rp-final 2026-10-28, coordinator): does a release TITLE name the bill ("AB 418", "A.B. 418", "Assembly Bill 418")? */
  var BILLW = { AB: 'Assembly Bill', SB: 'Senate Bill', ACR: 'Assembly Concurrent Resolution', ACA: 'Assembly Constitutional Amendment', AJR: 'Assembly Joint Resolution', SCR: 'Senate Concurrent Resolution', SJR: 'Senate Joint Resolution', HR: 'House Resolution' };
  var titleNames = function(title, k){ var m = /^([A-Z]+)(\d+)$/.exec(k); if (!m) return false;
    var pre = m[1].split('').join('\\.?\\s?') + '\\.?' + (BILLW[m[1]] ? '|' + BILLW[m[1]] : '');
    return new RegExp('(^|[^A-Za-z0-9])(' + pre + ')\\s*(No\\.?\\s*)?' + m[2] + '(?![0-9])', 'i').test(String(title || '')); };
  var isAuthor = function(role){ return /^author/i.test(String(role || '')); };
  var sesStart = function(s){ var y = +String(s).slice(0, 4); return y ? (y - 1) + '-12-01' : '0000'; };
  /* SESSION-v1 (restored from the v18 Bills view's "All dates | Session only" toggle): a session runs Dec 1 before its first
     year to Nov 30 of its second (the extraordinary session "2025-2026 (1st Ex. Sess.)" uses the same window) */
  var sesEnd = function(s){ var y = +String(s).slice(5, 9) || (+String(s).slice(0, 4) + 1); return y + '-11-30'; };
  var sesLabel = function(s){ var m = String(s).match(/^(\d{4})-\d{2}(\d{2})(.*)$/); return m ? m[1] + '–' + m[2] + (m[3].trim() ? ' ' + m[3].trim() : '') : String(s); };
  var dayLabel = function(iso){ iso = String(iso || ''); if (iso.length < 10) return iso.length === 7 ? MON[+iso.slice(5, 7) - 1] + ' ' + iso.slice(0, 4) : iso; return MON[+iso.slice(5, 7) - 1] + ' ' + (+iso.slice(8, 10)) + ', ' + iso.slice(0, 4); };
  var weekOf = function(iso){ var d = new Date(iso.slice(0, 10) + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() - (d.getUTCDay() + 6) % 7); return d.toISOString().slice(0, 10); };
  var addD = function(iso, n){ var d = new Date(iso + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
  var cap1 = function(s){ s = String(s || ''); return s.charAt(0).toUpperCase() + s.slice(1); };
  /* billsinfo status when the milestone block has no final status */
  function statusText(s){
    s = String(s || '').trim(); if (!s) return '';
    if (/^chaptered$/i.test(s)) return 'Signed into law'; if (/^vetoed$/i.test(s)) return 'Vetoed';
    var m = s.match(/^(Assembly|Senate)\s*-\s*Died\s*-\s*(.+)$/); if (m) return 'Died in ' + m[1] + ' ' + m[2];
    m = s.match(/^(Assembly|Senate)\s*-\s*Died$/); if (m) return 'Died in ' + m[1];
    m = s.match(/^(Assembly|Senate)\s*-\s*(.+)$/); if (m) return 'Last in ' + m[1] + ' ' + m[2];
    return s;
  }
  /* facet group of a final status; "held" / "inactive file" / "last in …" only stay open in the current session */
  function statusCat(st, ses, cur){
    if (/^Signed|^Chaptered/i.test(st)) return 'Signed into law';
    if (/^Vetoed/i.test(st)) return 'Vetoed';
    if (/^Adopted/i.test(st)) return 'Adopted';
    if (/^Died/i.test(st)) return 'Died';
    return String(ses).slice(0, 9) === cur ? 'Pending' : 'Died';
  }
  /* LegInfo bill history (bill_id = session years + 0 or the extraordinary-session number + house + number) */
  function legUrl(bill, ses){
    var s = String(ses).match(/^(\d{4})-(\d{4})(?:.*?(\d)\w*\s+Ex)?/), b = String(bill).toUpperCase().match(/^([A-Z]+?)(?:X\d+)?[\s-]*(\d+)$/);
    if (!s || !b) return '';
    return 'https://leginfo.legislature.ca.gov/faces/billHistoryClient.xhtml?bill_id=' + s[1] + s[2] + (s[3] || '0') + b[1] + b[2];
  }
  var numKey = function(it){ var m = String(it.bill).match(/^([A-Z]+)\D*?(\d+)$/i); return m ? m[1] + ' ' + String(m[2]).padStart(5, '0') + ' ' + it.ses : it.bill + ' ' + it.ses; };

  function build(ctx){
    CTX = ctx;
    if (memo.M && memo.v === ctx.version) return memo.M;
    var info = (ctx.bills() || []).filter(function(b){ return b && b.bill && b.session; });
    var sesBy = new Map();
    info.forEach(function(b){ var k = bkey(b.bill), a = sesBy.get(k) || sesBy.set(k, []).get(k); if (a.indexOf(String(b.session)) < 0) a.push(String(b.session)); });
    sesBy.forEach(function(a){ a.sort(); });
    var pickSes = function(k, date){ var ss = sesBy.get(k) || []; if (!ss.length) return ''; var d = date.length < 10 ? date.slice(0, 7) + '-15' : date;
      return ss.filter(function(s){ return sesStart(s) <= d; }).pop() || ss[0]; };
    var blk = ctx.block('bill_timeline'), ms = new Map();
    if (blk && Array.isArray(blk.b)) blk.b.forEach(function(x){ ms.set(bkey(x[0]) + '|' + x[1], { url: x[2] || '', fin: x[4] || '',
      ev: (x[3] || []).map(function(e){ return { date: e[0], kind: e[1], label: e[2] }; }).sort(function(a, b){ return a.date < b.date ? -1 : a.date > b.date ? 1 : 0; }) }); });
    var cur = (function(){ var y = +String(ctx.TODAY).slice(0, 4); var a = y % 2 ? y : y - 1; return a + '-' + (a + 1); })();
    var by = new Map(), items = [];
    info.forEach(function(b){
      var co = !isAuthor(b.role);   /* COAUTH-v1 (coordinator 2026-10-28): coauthored bills are listed only when stories tie them to him */
      var key = bkey(b.bill) + '|' + b.session; if (by.has(key)) return;
      var m = ms.get(key) || null, ev = m ? m.ev : [];
      var fin = ev.filter(function(e){ return FINAL[e.kind]; }).pop();
      var status = (m && m.fin) || (fin ? FINAL[fin.kind] : statusText(b.status)) || '';
      var it = { key: key, bill: String(b.bill), ses: String(b.session), sesL: sesLabel(b.session), title: String(b.title || '').trim().replace(/\.$/, ''),
        role: String(b.role), ev: ev, hasMs: !!m, status: status, cat: statusCat(status, b.session, cur), url: (m && m.url) || legUrl(b.bill, b.session),
        rs: [], rels: [], co: co, budget: !!(b.budgetAct || b.budget_act) };   /* v23-BUDGET */
      it.slug = ctx.slug(it.bill + ' ' + it.sesL);
      by.set(key, it); items.push(it);
    });
    (ctx.D || []).forEach(function(r){ if (!r || !r.date) return; var seen = {};
      (r.bills || []).forEach(function(b){ var k = bkey(b); if (seen[k]) return; seen[k] = 1; var it = by.get(k + '|' + pickSes(k, r.date)); if (it) it.rs.push(r); }); });
    /* RELSES-v1 (rp-clips 2026-10-28, RELPLAN): a bill page lists only releases from that bill's own session: the release is in
       rp-threads' thread for the bill + session (tab-releases thr.th, incl. releases that joined by text: "i" inherited /
       "r" renumbered), or it names the bill and its date falls in that session (Dec of an even year = the next session, the
       relthread rule). A later-session release naming an old bill in passing (AB 418 2023-24 in the 2025-26 food-safety
       releases) is no longer listed. Without thr: the date rule alone. bg = thr.x[..].bg (named as background). */
    var rp = ctx.block('release_pickup'), tr = ctx.block('releases'), thr = tr && tr.thr, thIn = new Map(), thX = (thr && thr.x) || {};
    var ses9 = function(s){ return String(s).slice(0, 9); };
    var dateSes = function(d){ var y = +String(d).slice(0, 4); if (!y) return ''; if (String(d).slice(5, 7) === '12' && y % 2 === 0) y++; var a = y % 2 ? y : y - 1; return a + '-' + (a + 1); };
    if (thr && Array.isArray(thr.th)) thr.th.forEach(function(t){ (t[2] || []).forEach(function(row){ var id = Array.isArray(row) ? row[0] : row, how = Array.isArray(row) ? row[1] : '';
      (t[0] || []).forEach(function(b){ var k = bkey(b) + '|' + t[1] + '|' + id; if (!thIn.has(k) || !how) thIn.set(k, how); }); }); });
    var cols = (rp && rp.cols) || [], iP = cols.indexOf('prid');
    if (rp && Array.isArray(rp.rel)) rp.rel.forEach(function(x){ var date = String(x[1] || ''), id = (iP >= 0 && x[iP]) || x[0], xx = thX[id] || {}, named = {};
      if (!date) return;
      (x[4] || []).forEach(function(b){ named[bkey(b)] = 1; });
      var cand = Object.keys(named); thIn.forEach(function(v, k){ var p = k.split('|'); if (p[2] === id && !(p[0] in named)) { named[p[0]] = 0; cand.push(p[0]); } });
      cand.forEach(function(k){ var hit = 0, row = function(how, bg, later){ return { key: x[0], date: date, iss: x[2], title: String(x[3] || ''), issue: x[5] || '', picks: (x[8] || []).length, url: x[9] || '', how: how, bg: bg, later: later }; };
        (sesBy.get(k) || []).forEach(function(s){ var it = by.get(k + '|' + s); if (!it) return;
          var tk = k + '|' + ses9(s) + '|' + id, inTh = thIn.has(tk), how = inTh ? thIn.get(tk) : '';
          if (!inTh && !(named[k] && dateSes(date) === ses9(s))) return;
          var bg = !inTh && (xx.bg || []).some(function(b){ return bkey(b) === k; });
          hit = 1; it.rels.push(row(how, bg, false)); });
        /* RELSES-v2 (rp-final, coordinator correction): a later-session release whose TITLE names the bill ("new law takes effect",
           a signing anniversary) is still listed on the bill's latest earlier session, labelled "Later release"; body-only
           background mentions stay out */
        if (!hit && named[k] && titleNames(x[3], k)){ var ds = dateSes(date), prev = (sesBy.get(k) || []).filter(function(s){ return ses9(s) < ds && by.get(k + '|' + s); }).sort().pop();
          if (prev) by.get(k + '|' + prev).rels.push(row('', false, true)); } }); });
    items = items.filter(function(it){ if (it.co && !it.rs.length){ by.delete(it.key); return false; } return true; });   // COAUTH-v1
    items.forEach(function(it){
      it.rs.sort(function(a, b){ return a.date < b.date ? -1 : a.date > b.date ? 1 : 0; });
      it.rels.sort(function(a, b){ return a.date < b.date ? 1 : a.date > b.date ? -1 : 0; });
      it.n = it.rs.length; it.nrel = it.rels.length; it.nrelS = it.rels.filter(function(r){ return !r.later; }).length;   /* nrelS: own session (the list link) */
      it.first = it.n ? it.rs[0].date : ''; it.lastS = it.n ? it.rs[it.n - 1] : null;
      var lastM = it.ev.length ? it.ev[it.ev.length - 1] : null; it.lastM = lastM;
      it.last = [it.lastS ? it.lastS.date : '', lastM ? lastM.date : ''].sort().pop() || '';
      var intro = it.ev.filter(function(e){ return e.kind === 'introduced'; })[0]; it.intro = intro ? intro.date : '';
      var iss = new Set(); it.rs.forEach(function(r){ if (r.topic) iss.add(r.topic); }); it.rels.forEach(function(r){ if (r.issue) iss.add(r.issue); }); it.issues = Array.from(iss);
      var ki = new Set(); it.ev.forEach(function(e){ if (KIND[e.kind]) ki.add(KIND[e.kind]); }); it.kinds = Array.from(ki);
      it.dates = it.ev.map(function(e){ return e.date; }).concat(it.rs.map(function(r){ return r.date; }));
      var start = sesStart(it.ses); it.plot = []; it.early = []; it.vague = []; it.wk = new Map();
      it.rs.forEach(function(r){ (r.prec !== 'day' || r.date.length < 10) ? it.vague.push(r) : r.date < start ? it.early.push(r) : it.plot.push(r); });
      it.plot.forEach(function(r){ var w = weekOf(r.date); (it.wk.get(w) || it.wk.set(w, []).get(w)).push(r); });
      it.peak = null; Array.from(it.wk.keys()).sort().forEach(function(w){ var n = it.wk.get(w).length; if (!it.peak || n > it.peak.n) it.peak = { w: w, n: n }; });
    });
    memo.v = ctx.version; memo.M = { items: items, by: by, ses: sesBy, hasBlock: !!blk, hasRel: !!rp };
    return memo.M;
  }

  /* ---- milestone timeline: stories per week (Monday weeks) with LegInfo milestones ---- */
  function drawTL(host, it, ctx){
    var W = Math.max(300, host.clientWidth || 700), small = W < 600, H = small ? 210 : 260;
    var m = { l: 36, r: 8, t: 50, b: 24 }, iw = W - m.l - m.r, ih = H - m.t - m.b;
    var ev = it.ev.filter(function(e){ return e.kind !== 'other'; });
    if (!it.plot.length){ host.innerHTML = '<div class="empty">' + (it.n ? 'No day-dated stories in this session to plot.' : 'No stories about this bill yet.') + ' The milestones are listed below.</div>'; GEO.delete(it.slug); return; }
    /* CHARTRULE-v1: one week of stories and no milestone to place them against is a single bar: a sentence instead */
    var wks = {}; it.plot.forEach(function(r){ if (r.date && r.date.length >= 10) wks[weekOf(r.date)] = 1; });
    if (!ev.length && Object.keys(wks).length <= 1){ var w1 = Object.keys(wks)[0]; host.innerHTML = '<div class="cap tbe-cnote">' + (w1 ? 'All ' + ctx.pl(it.plot.length, 'story', 'stories') + ' ran in the week of ' + dayLabel(w1) + ', so there is no chart.' : 'No day-dated stories to chart.') + '</div>'; GEO.delete(it.slug); return; }
    var lo = null, hi = null, ext = function(d){ if (!d || d.length < 10) return; var w = weekOf(d); if (!lo || w < lo) lo = w; if (!hi || w > hi) hi = w; };
    var sesOnly = host.dataset.range === 'session', s0 = weekOf(sesStart(it.ses)), s1 = weekOf(sesEnd(it.ses));
    /* RELDOTS-v1 (Sammy 2026-10-30, thread 0838b290: "add relevant press releases to these graphs as dots"): the bill's own-session
       releases (it.rels, not "later") as accent dots on the week they went out, sitting on that week's bar; hover = title, date,
       outlets that ran it; click opens the release page */
    var relDots = (it.rels || []).filter(function(r){ return !r.later && r.date && r.date.length >= 10; });
    it.plot.forEach(function(r){ ext(r.date); }); ev.forEach(function(e){ ext(e.date); }); relDots.forEach(function(r){ ext(r.date); });
    if (sesOnly){ lo = s0; hi = s1; }   // SESSION-v1: the bill's two-year session, whole
    var weeks = []; for (var w = lo; w <= hi; w = addD(w, 7)) weeks.push(w);
    var counts = weeks.map(function(x){ return (it.wk.get(x) || []).length; });
    var ymax = ctx.niceMax(Math.max.apply(null, counts), 'count'), band = iw / weeks.length;
    var bw = Math.min(24, Math.max(1, band - (band > 5 ? 2 : band > 2.5 ? 1 : 0.3)));
    var y = function(v){ return m.t + ih - (v / ymax) * ih; }, xw = function(x){ return m.l + ((Date.parse(x) - Date.parse(lo)) / 6048e5) * band; };
    var xd = function(d){ return xw(weekOf(d)) + band * (((new Date(d + 'T00:00:00Z').getUTCDay() + 6) % 7 + 0.5) / 7); };
    var svg = ctx.axis('<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + ctx.esc(it.bill) + ' stories per week with milestones">', W, H, m, ymax);
    counts.forEach(function(v, i){ if (v) svg += '<path d="' + ctx.barPath(m.l + i * band + (band - bw) / 2, y(0), y(v), bw, true) + '" fill="var(--bar)"></path>'; });
    svg += '<line class="base" x1="' + m.l + '" x2="' + (W - m.r) + '" y1="' + y(0) + '" y2="' + y(0) + '"></line>';
    /* TIMEAXIS-v1 (rp-final, Sammy e10d15f0): the shared time axis (07_charts.js timeAxis via ctx): years with quarter ticks over 24
       months, quarters for 7-24, months for 6 or less; label caps 8 / 5 (phone). A month's tick = its first day (clamped to the first week). */
    var xm = function(k){ var d = k + '-01'; return Math.max(m.l, xd(d < lo ? lo : d)); };
    if (ctx.timeAxis) svg += ctx.timeAxis(lo.slice(0, 7), hi.slice(0, 7), xm, { W: W, y0: y(0), yText: H - 6 });
    var shown = ev.filter(function(e){ return e.date.length >= 10 && weekOf(e.date) >= lo && weekOf(e.date) <= hi; });
    var lastFloor = shown.filter(function(e){ return e.kind === 'floor'; }).pop(), rows = [-1e9, -1e9];
    shown.forEach(function(e){
      var x = xd(e.date).toFixed(1);
      if (RULE[e.kind]) svg += '<line x1="' + x + '" x2="' + x + '" y1="' + (m.t - 24) + '" y2="' + y(0) + '" stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3"></line>';
      else svg += '<circle cx="' + x + '" cy="' + (m.t - 18) + '" r="3.5" fill="var(--ink-3)" stroke="var(--panel)" stroke-width="2"></circle>';
      var lab = e.kind === 'introduced' ? 'Introduced' : FINAL[e.kind] ? FINAL[e.kind] : e === lastFloor ? 'Final floor vote' : '';
      if (lab){ var tw = lab.length * 6.3 + 6, right = +x + tw > W - m.r, lx = right ? +x - tw : +x, row = rows.findIndex(function(end){ return lx > end + 4; });
        if (row >= 0){ rows[row] = lx + tw; svg += '<text class="peak" x="' + (right ? +x - 3 : +x + 3) + '" y="' + (row ? 26 : 12) + '" text-anchor="' + (right ? 'end' : 'start') + '">' + lab + '</text>'; } }
    });
    var taken = [];
    var rshown = relDots.filter(function(r){ var w = weekOf(r.date); return w >= lo && w <= hi; }).sort(function(a, b){ return a.date < b.date ? -1 : a.date > b.date ? 1 : 0; }), stack = {};
    rshown.forEach(function(r){ var w = weekOf(r.date), i = weeks.indexOf(w), k = stack[w] = (stack[w] || 0) + 1;
      r._cx = xd(r.date); r._cy = m.t - 6;   /* RELDOTS-v4 (Sammy 2026-10-30): own row just below the milestone dots, at the release's own day */
      /* RELDOTS-v3/v4: releases on the same day step right so they never cover each other */
      while (taken.some(function(x){ return Math.abs(x - r._cx) < 9; })) r._cx += 9; taken.push(r._cx);
      svg += '<circle class="rel-dot" cx="' + r._cx.toFixed(1) + '" cy="' + r._cy.toFixed(1) + '" r="4" fill="var(--s2)" stroke="var(--panel)" stroke-width="2"></circle>'; });
    weeks.forEach(function(x, i){ svg += '<rect class="hit' + (counts[i] ? '' : ' nc') + '" data-blw="' + i + '" x="' + (m.l + i * band) + '" y="' + m.t + '" width="' + band + '" height="' + ih + '"></rect>'; });
    rshown.forEach(function(r, i){ var rx = ctx.rels ? ctx.rels().byKey.get(r.key) : null, sub = rx && rx.sub ? rx.sub : '';
      svg += '<rect class="hit' + (sub ? '' : ' nc') + '" data-blp="' + i + '"' + (sub ? ' data-tb-go="releases" data-tb-sub="' + ctx.esc(sub) + '"' : '') + ' x="' + (r._cx - 7).toFixed(1) + '" y="' + (r._cy - 7).toFixed(1) + '" width="14" height="14"></rect>'; });
    shown.forEach(function(e, i){ var x = xd(e.date); svg += '<rect class="hit nc" data-blm="' + i + '" x="' + (x - 6) + '" y="0" width="12" height="' + (m.t - 12) + '"></rect>'; });
    host.innerHTML = svg + '</svg>';
    GEO.set(it.slug, { it: it, weeks: weeks, shown: shown, ymax: ymax, rels: rshown });
  }
  function drawPending(){
    var ctx = CTX; if (!ctx) return;
    document.querySelectorAll('#tbBody .chart[data-blc]:not([data-bld])').forEach(function(h){
      var it = memo.M && memo.M.items.filter(function(x){ return x.slug === h.dataset.blc; })[0]; if (!it) return;
      h.dataset.bld = '1'; try { drawTL(h, it, ctx); } catch(e){ console.error(e); h.innerHTML = '<div class="empty">The timeline could not be drawn.</div>'; }
    });
  }
  /* SESSION-v1 toggle */
  document.addEventListener('click', function(e){
    var b = e.target.closest && e.target.closest('.bl-range [data-blr]'); if (!b) return;
    var sec = b.closest('.rp-sec'), h = sec && sec.querySelector('.chart[data-blc]'); if (!h) return;
    e.preventDefault(); e.stopPropagation(); h.dataset.range = b.dataset.blr; h.removeAttribute('data-bld');
    sec.querySelectorAll('.bl-range [data-blr]').forEach(function(x){ x.setAttribute('aria-pressed', String(x === b)); }); drawPending();
  }, true);
  document.addEventListener('click', function(e){
    var t = e.target.closest && e.target.closest('.chart[data-blc] .hit[data-blw]'); if (!t || !CTX) return;
    var g = GEO.get(t.closest('.chart').dataset.blc); if (!g) return;
    var w = g.weeks[+t.dataset.blw]; if (!(g.it.wk.get(w) || []).length) return;
    e.preventDefault(); e.stopPropagation(); CTX.hideTip();
    var p = CTX.params; delete p.pg; p.when = 'c:' + w + '..' + addD(w, 6); CTX.setParams(p); CTX.refresh();
    CTX.toast('Showing the week of ' + dayLabel(w));
    setTimeout(function(){ var tb = document.querySelector('#tbBody .tb-view:not([hidden]) .tbe-tab'); if (tb && tb.scrollIntoView) tb.scrollIntoView({ block: 'start' }); }, 30);
  }, true);
  document.addEventListener('mousemove', function(e){
    var t = e.target.closest && e.target.closest('.chart[data-blc] .hit'); if (!CTX) return;
    var host = e.target.closest && e.target.closest('.chart[data-blc]'); if (!host){ return; }
    if (!t){ CTX.hideTip(); return; }
    var g = GEO.get(host.dataset.blc); if (!g) return; var esc = CTX.esc;
    if (t.dataset.blp != null){ var rl = (g.rels || [])[+t.dataset.blp]; if (!rl) return; CTX.showTip(e, '<div class="th">' + esc(rl.title) + '</div><div class="row"><span class="l">Press release</span><b>' + dayLabel(rl.date) + '</b></div><div class="row"><span class="l">Outlets that ran it</span><b>' + CTX.fmt(rl.picks || 0) + '</b></div>' + (t.dataset.tbGo ? '<div class="foot">Click to open the release</div>' : '')); return; }
    if (t.dataset.blm != null){ var ev = g.shown[+t.dataset.blm]; CTX.showTip(e, '<div class="th">' + esc(ev.label) + '</div><div class="row"><span class="l">Date</span><b>' + dayLabel(ev.date) + '</b></div>'); return; }
    var w = g.weeks[+t.dataset.blw], n = (g.it.wk.get(w) || []).length;
    var msw = g.shown.filter(function(x){ return weekOf(x.date) === w; }).map(function(x){ return '<div class="row"><span class="l">' + dayLabel(x.date).replace(/, \d{4}$/, '') + '</span><b>' + esc(x.label) + '</b></div>'; }).join('');
    CTX.showTip(e, '<div class="th">Week of ' + dayLabel(w) + '</div><div class="row"><span class="l">Stories</span><b>' + CTX.fmt(n) + '</b></div>' + msw + (n ? '<div class="foot">Click to list these stories below</div>' : ''));
  });
  document.addEventListener('mouseleave', function(e){ if (CTX && e.target && e.target.matches && e.target.matches('.chart[data-blc]')) CTX.hideTip(); }, true);

  /* ---- the search tab ---- */
  var list = {
    noun: ['bill', 'bills'], title: 'Bills', placeholder: 'Search bill numbers and titles',
    cap: 'Bills Gabriel authored or co-led (LegInfo), one row per bill and session, with final status and the stories that mention them. Coauthored bills are listed (marked Coauthored) when a story is tagged with them. Click a bill to open its page.',
    items: function(ctx){ return build(ctx).items; },
    key: function(it){ return it.key; },
    text: function(it){ var m = it.bill.match(/^([A-Z]+)\D*?(\d+)$/i); return it.bill + ' ' + it.bill.replace(/[\s-]+/g, '') + (m ? ' ' + m[1] + m[2] + ' ' + m[2] : '') + ' ' + it.title + ' ' + it.sesL; },
    facets: [
      { key: 'ses', label: 'Session', open: true, vals: function(it){ return it.sesL; }, order: function(a, b){ return a < b ? 1 : a > b ? -1 : 0; } },
      { key: 'fin', label: 'Final status', open: true, vals: function(it){ return it.cat; }, order: STATUS_ORDER,
        hint: 'From LegInfo. Pending = still alive in the current session.' },
      { key: 'iss', label: 'Issue', search: true, limit: 8, vals: function(it){ return it.issues; }, sw: function(v){ return CTX ? CTX.colorFor('topic', v) : ''; },
        hint: 'Issues of the bill’s stories and press releases.' },
      { key: 'mst', label: 'Milestone reached', vals: function(it){ return it.kinds; }, order: KIND_ORDER, hint: 'Bills with this step in their LegInfo history.' },
      { key: 'date', label: 'Activity', type: 'date', date: function(it){ return it.dates; }, any: 'Any time', hint: 'Bills with a milestone or a story in this range.' },
      { key: 'cov', label: 'Has coverage', vals: function(it){ return it.n ? 'Yes' : 'No'; }, order: ['Yes', 'No'], hint: 'At least one story in the tracker mentions the bill.' },
      { key: 'role', label: 'Role', vals: function(it){ return it.co ? 'Coauthored' : 'Author or co-lead'; }, order: ['Author or co-lead', 'Coauthored'], hint: 'Coauthored bills are listed only when a story is tagged with them.' },
      { key: 'rel', label: 'Has press release', vals: function(it){ return it.nrel ? 'Yes' : 'No'; }, order: ['Yes', 'No'], hint: 'An official release names the bill.' },
      /* v23-BUDGET (Sammy, V23Q): the Budget Act and budget bills he carries as Budget chair are hidden unless asked for */
      { key: 'bud', label: 'Budget Act bills', type: 'one', any: 'Show Budget Act bills', def: 'hide', options: [
        { id: 'hide', label: 'Left out', test: function(it){ return !it.budget; } },
        { id: 'only', label: 'Only these', test: function(it){ return it.budget; } }],
        hint: 'Budget Act and budget bills Gabriel carries as Budget chair. Hidden by default.' }
    ],
    columns: [
      { key: 'bill', label: 'Bill', sort: numKey, val: function(it){ return it.bill; }, cls: 'nw', cell: function(it, ctx){ return '<button class="linkbtn tt-open">' + ctx.esc(it.bill) + '</button>' + (it.co ? ' <span class="sub">Coauthored</span>' : ''); } },
      { key: 'title', label: 'Title', val: function(it){ return it.title; } },
      { key: 'ses', label: 'Session', dir: -1, sort: function(it){ return it.ses; }, val: function(it){ return it.sesL; }, cls: 'nw' },
      { key: 'status', label: 'Final status', val: function(it){ return it.status; } },
      { key: 'n', label: 'Stories', num: true, dir: -1, val: function(it){ return it.n; }, cell: function(it, ctx){ return ctx.fmt(it.n); } },
      { key: 'last', label: 'Last activity', dir: -1, val: function(it){ return it.last; }, cls: 'nw', cell: function(it){ return it.last ? dayLabel(it.last) : '—'; } }
    ],
    sort: { key: 'n', dir: -1 }, step: { desk: 100, phone: 25 }, open: 'page',
    csvExtra: [['Role', function(it){ return it.role; }], ['Introduced', function(it){ return it.intro; }], ['First story', function(it){ return it.first; }],
      ['Press releases', function(it){ return it.nrel; }], ['Issues', function(it){ return it.issues.join('; '); }], ['LegInfo history', function(it){ return it.url; }]],
    answer: function(res, st, ctx){ if (!res.length) return ''; var top = res.slice().sort(function(a, b){ return b.n - a.n; })[0];
      return ctx.pl(res.length, 'bill', 'bills') + ' match' + (res.length === 1 ? 'es' : '') + '. ' + (top.n ? 'Most covered: ' + top.bill + ' (' + top.sesL + '), ' + ctx.pl(top.n, 'story', 'stories') + '.' : 'None has coverage.'); },
    empty: function(){ return 'No bills match these filters.'; },
    copies: [{ label: 'Copy bill list', sub: 'One bill per line: number, session, title, stories',
      text: function(res, st, ctx){ return res.map(function(it){ return it.bill + ' (' + it.sesL + '): ' + it.title + ' – ' + ctx.pl(it.n, 'story', 'stories'); }).join('\n'); } }],
    csvName: function(st, ctx){ return 'AJG bills ' + ctx.TODAY + '.csv'; }
  };

  /* SESSION-v1 (Sammy, preview: "add back the legislative session view"): the bill's coverage by legislative stage, from its
     LegInfo milestones: before introduction, the house of origin (to its floor vote), the second house (to its floor vote or
     concurrence), on to the Governor (to the final action), after it. A bill that died stops at that date. Day-dated stories only. */
  function stages(it){
    var ev = it.ev.filter(function(e){ return e.date && e.date.length >= 10; }); if (!ev.length) return null;
    var origin = /^S/i.test(it.bill) ? 'Senate' : 'Assembly', other = origin === 'Senate' ? 'Assembly' : 'Senate';
    var intro = (ev.filter(function(e){ return e.kind === 'introduced'; })[0] || {}).date || '';
    var fl1 = (ev.filter(function(e){ return e.kind === 'floor' && e.label.indexOf(origin + ' floor') === 0; })[0] || {}).date || '';
    var fl2 = (ev.filter(function(e){ return e.kind === 'floor' && (e.label.indexOf(other + ' floor') === 0 || /concurrence/i.test(e.label)) && (!fl1 || e.date >= fl1); }).pop() || {}).date || '';
    var fin = ev.filter(function(e){ return FINAL[e.kind]; })[0] || null, end = fin ? fin.date : '';
    var cuts = [['Before introduction', '', intro], ['In the ' + origin, intro, fl1 || end], ['In the ' + other, fl1, fl2 || end], ['To the Governor', fl2, end && (fin.kind === 'signed' || fin.kind === 'vetoed' || fin.kind === 'chaptered') ? end : ''],
      ['After ' + (fin ? (fin.kind === 'died' ? 'it died' : fin.kind === 'vetoed' ? 'the veto' : 'it was signed') : 'the last milestone'), end, '']];
    var rs = it.rs.filter(function(r){ return r.prec === 'day' && r.date && r.date.length >= 10; }), out = [];
    cuts.forEach(function(c, i){ var a = c[1], z = c[2];
      if (i > 0 && !a) return;                          // the stage never started (no floor vote yet, never sent on)
      if (i === 3 && (!fl2 || !z)) return;
      var n = rs.filter(function(r){ return (i === 0 ? (!z || r.date < z) : r.date > a || (i === 1 && r.date >= a)) && (i === 4 || !z || r.date <= z); }).length;
      out.push({ label: c[0], from: i === 0 ? '' : a, to: i === 4 ? '' : z, n: n }); });
    return out.length ? { rows: out, vague: it.rs.length - rs.length } : null;
  }
  /* ---- the bill page ---- */
  function extraHtml(it, ctx){
    var esc = ctx.esc, out = '';
    var notes = [];
    if (it.early.length) notes.push(ctx.pl(it.early.length, 'story', 'stories') + ' dated before this session');
    if (it.vague.length) notes.push(ctx.pl(it.vague.length, 'story', 'stories') + ' dated only to the month or year');
    out += '<div class="rp-sec"><div><h2 class="sec">Milestones and coverage</h2><div class="cap">Stories per week that mention ' + esc(it.bill) + ', with its LegInfo milestones. Hover for details; click a week to list its stories below.</div></div>'
      + (it.ev.length ? '<div class="legend"><span class="it"><svg width="12" height="10" aria-hidden="true"><rect width="12" height="10" rx="2" fill="var(--bar)"></rect></svg>Stories per week</span><span class="it"><svg width="14" height="12" aria-hidden="true"><line x1="7" x2="7" y1="0" y2="12" stroke="var(--ink-3)" stroke-dasharray="3 3"></line></svg>Introduced, floor vote, final action</span><span class="it"><svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="3.5" fill="var(--ink-3)"></circle></svg>Committee vote</span>' + (it.nrelS ? '<span class="it"><svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="4.5" fill="var(--s2)"></circle></svg>Press release</span>' : '') + '</div>' : '')
      + '<div class="an-controls"><div class="seg bl-range" role="group" aria-label="Date range"><button type="button" data-blr="all" aria-pressed="true">All dates</button><button type="button" data-blr="session" aria-pressed="false">Session only</button></div>'
      + '<span class="cap bl-ses">' + esc(it.sesL) + ' session: ' + dayLabel(sesStart(it.ses)) + ' to ' + dayLabel(sesEnd(it.ses)) + ' · ' + ctx.pl(it.rs.filter(function(r){ return r.date >= sesStart(it.ses) && r.date.slice(0, 10) <= sesEnd(it.ses); }).length, 'story', 'stories') + ' in it</span></div>'
      + '<div class="chart" data-blc="' + esc(it.slug) + '"></div>'
      + (notes.length && it.plot.length ? '<div class="note">Not plotted: ' + notes.join('; ') + '.</div>' : '')
      + (function(){ var sg = it.n ? stages(it) : null; if (!sg) return '';   /* no coverage: nothing to count by stage */
          return '<details class="dt"><summary>Coverage by stage (' + esc(it.sesL) + ' session)</summary><div class="tablewrap"><table><thead><tr><th>Stage</th><th>Dates</th><th>Stories</th></tr></thead><tbody>'
            + sg.rows.map(function(x){ return '<tr><td>' + esc(x.label) + '</td><td>' + (x.from && x.to ? dayLabel(x.from) + ' – ' + dayLabel(x.to) : x.from ? 'From ' + dayLabel(x.from) : x.to ? 'Until ' + dayLabel(x.to) : '') + '</td><td>' + ctx.fmt(x.n) + '</td></tr>'; }).join('')
            + '</tbody></table></div>' + (sg.vague ? '<div class="note">' + ctx.pl(sg.vague, 'story', 'stories') + ' dated only to the month or year not counted.</div>' : '') + '</details>'; })()
      + (it.ev.length ? '<details class="dt"><summary>Milestones (' + it.ev.length + ')</summary><div class="tablewrap"><table><thead><tr><th>Milestone</th><th>Date</th><th>Stories that week</th></tr></thead><tbody>'
        + it.ev.map(function(e){ return '<tr><td>' + esc(e.label) + '</td><td>' + dayLabel(e.date) + '</td><td>' + ctx.fmt(e.date.length >= 10 ? (it.wk.get(weekOf(e.date)) || []).length : 0) + '</td></tr>'; }).join('')
        + '</tbody></table></div></details>' : '<div class="note">' + (memo.M && memo.M.hasBlock ? 'No LegInfo milestones for this bill in the Bills tab snapshot.' : 'Milestones not loaded yet.') + '</div>')
      + '</div>';
    out += '<div class="rp-sec"><div><h2 class="sec">Press releases</h2><div class="cap">' + (it.nrel ? 'Official releases from the ' + esc(it.sesL) + ' session that name ' + esc(it.bill) + ' (or continue its thread), newest first, with how many outlets ran each.' + (it.nrel > it.nrelS ? ' Later releases that name it in the title are marked.' : '') : 'No official release from this session names this bill.') + '</div></div>'
      + (it.nrel ? '<div class="clip-list">' + it.rels.map(function(r){
          /* RELREVERSE-v1 (rp-reverse): the title opens the release page (link rules: release -> its page); the official link stays on the right */
          var rx = ctx.rels ? ctx.rels().byKey.get(r.key) : null, pg = rx && rx.sub ? ctx.pageLink('releases', rx.sub, r.title + ' ›', 'Open the release page') : '';
          var t = pg ? '<span class="ct">' + pg + '</span>' : r.url ? '<span class="lkw">' + ctx.cpBtn(r.url) + '<a class="ct" href="' + esc(r.url) + '" target="_blank" rel="noopener">' + esc(r.title) + '</a></span>' : '<span class="ct">' + esc(r.title) + '</span>';
          if (ctx.row) return ctx.row({ title: pg || '<span>' + esc(r.title) + '</span>',   /* ROWLIST-v1; LINKUI: the release link (copy icon on its left) is on the right */
            meta: [dayLabel(r.date), esc(ISSUER[r.iss] || ''), r.picks ? ctx.pl(r.picks, 'outlet ran it', 'outlets ran it') : 'No pickups', r.issue ? esc(r.issue) : '', relHow(r)],
            right: r.url ? '<div class="dlinks"><span class="lkw">' + ctx.cpBtn(r.url) + '<a href="' + esc(r.url) + '" target="_blank" rel="noopener"><b>Release</b> ↗</a></span></div>' : '<span class="note">Not posted</span>' });
          return '<div class="clip">' + t + '<div class="cm"><span>' + dayLabel(r.date) + '</span><span>' + esc(ISSUER[r.iss] || '') + '</span><span>' + (r.picks ? ctx.pl(r.picks, 'outlet ran it', 'outlets ran it') : 'No pickups') + '</span>' + (r.issue ? '<span>' + esc(r.issue) + '</span>' : '') + (relHow(r) ? '<span>' + relHow(r) + '</span>' : '') + '</div></div>'; }).join('') + '</div>' : '')
      + '</div>';
    return out;
  }
  function find(sub, ctx){
    var M = build(ctx), s = String(sub || '');
    var hit = M.items.filter(function(it){ return it.slug === s; })[0]; if (hit) return hit;
    var c = M.items.filter(function(it){ return ctx.slug(it.bill) === s; }).sort(function(a, b){ return b.n - a.n || (a.ses < b.ses ? 1 : -1); });
    return c[0] || null;
  }
  var page = {
    slug: function(it){ return it.slug; },
    find: find,
    /* LINKSCOPE-v1: this bill in Clips; a number reused across sessions also carries this session's dates (the story rule:
       from this session's start to the next session's start) */
    scope: function(it, ctx){ var M = build(ctx), ss = M.ses.get(bkey(it.bill)) || [], i = ss.indexOf(it.ses), sc = { sel: { bills: [it.bill] }, label: it.bill + ' (' + it.sesL + ')' };
      if (ss.length > 1 && i >= 0) sc.when = [i > 0 ? sesStart(it.ses) : '', i < ss.length - 1 ? addD(sesStart(ss[i + 1]), -1) : '', it.bill + ' ' + it.sesL + ' session'];
      return sc; },
    spec: function(it, ctx){
      var esc = ctx.esc;
      setTimeout(drawPending, 0);
      /* RELLIST-v1 (rp-reverse 2026-10-28): the count opens the Press releases list filtered to this bill (facet "bill"); a
         number reused across sessions also gets that session's dates (facet "date", c:from..to), as the bill's Clips scope */
      var relsLink = function(it, ctx){ if (!it.nrelS) return ctx.fmt(it.nrel) + (it.nrel ? ' <span class="note">later</span>' : '');
        var ss = (memo.M && memo.M.ses.get(bkey(it.bill))) || [], i = ss.indexOf(it.ses), p = { bill: it.bill };
        if (ss.length > 1 && i >= 0) p.date = 'c:' + (i > 0 ? sesStart(it.ses) : '') + '..' + (i < ss.length - 1 ? addD(sesStart(ss[i + 1]), -1) : '');
        else p.date = 'c:' + sesStart(it.ses) + '..' + sesEnd(it.ses);   /* RELSES-v1: the list matches the page (own session only) */
        return '<button type="button" class="linkbtn" data-tb-go="releases" data-tb-sub="" data-tb-p="' + esc(JSON.stringify(p)) + '" title="List this session’s releases in Press releases">' + ctx.fmt(it.nrelS) + ' ›</button>' + (it.nrel > it.nrelS ? ' <span class="note">+ ' + ctx.fmt(it.nrel - it.nrelS) + ' later</span>' : ''); };
      var lastS = it.lastS ? '<button class="linkbtn" data-tbstory="' + esc(it.lastS.id) + '">' + esc(ctx.dateLabel(it.lastS)) + '</button>' : '';
      /* HEADER-v2: kicker bill · session · status; clusters Bill (LegInfo facts) / Coverage / Links */
      var billF = [['Session', esc(it.sesL)], ['Role', esc(cap1(it.role))], ['Final status', esc(it.status)], ['Introduced', it.intro ? dayLabel(it.intro) : ''],
          ['Last milestone', it.lastM ? esc(it.lastM.label) + ' <span class="sub">' + dayLabel(it.lastM.date) + '</span>' : '']];
      var covF = [['Stories', ctx.fmt(it.n)], ['Latest story', lastS], ['Busiest week', it.peak ? dayLabel(it.peak.w) + ' <span class="sub">' + ctx.pl(it.peak.n, 'story', 'stories') + '</span>' : ''],
          ['Press releases', relsLink(it, ctx)]];
      var linkF = [['LegInfo', ctx.link(it.url, 'LegInfo history')]];
      return { kicker: ['Bill', it.sesL + ' session', it.status || ''], title: it.bill + (it.title ? ': ' + it.title : ''), noun: 'bill', backLabel: 'All bills', placeholder: 'Search the ' + ctx.pl(it.n, 'story', 'stories') + ' on ' + it.bill,
        dek: (it.role ? esc(cap1(it.role)) + (it.role === 'author' || /author/i.test(it.role) ? ' of the bill' : '') : '') + (it.n ? (it.role ? '. ' : '') + ctx.pl(it.n, 'story', 'stories') + ' in the tracker mention' + (it.n === 1 ? 's' : '') + ' it' + (it.lastS ? ', the latest on ' + esc(ctx.dateLabel(it.lastS)) : '') + '.' : (it.role ? '. ' : '') + 'No tracker story mentions it.'),
        groups: [{ key: 'what', label: 'Bill', facts: billF }, { key: 'coverage', label: 'Coverage', facts: covF }, { key: 'links', label: 'Links', facts: linkF }], groupLabels: false,   /* NOGLABEL-v1 */
        facts: billF.concat(covF, linkF),
        extra: extraHtml(it, ctx), rows: it.rs,
        /* EMBEDROWS-v1: who covered the bill and where, as the Reporters and Outlets tabs list them (over this bill's stories) */
        embeds: (function(){ var ids = {}; it.rs.forEach(function(r){ ids[r.id] = 1; });
          return [{ tab: 'reporters', title: 'Reporters', cap: 'The Reporters tab’s rows for the people who wrote about ' + esc(it.bill) + ' (' + esc(it.sesL) + '), counted over those stories.', unit: function(u){ return !!ids[u.id]; }, cols: ['name', 'outlets', 'stories', 'last', 'tone', 'neg'] },
            { tab: 'outlets', title: 'Outlets', cap: 'The Outlets tab’s rows for the outlets that ran stories on ' + esc(it.bill) + ' (' + esc(it.sesL) + '), as originals or reprints.', unit: function(u){ return !!ids[u.r.id]; }, cols: ['name', 'n', 'orig', 'reps', 'last', 'tone', 'neg'] }]; })() };
    }
  };

  /* BILL-SLUG-v1 (for the integrator's ctx.billLink(bill, {date})): the #bills/<slug> page of a bill number.
     slug = ctx.slug(<bill as LegInfo lists it> + ' ' + <session label>), e.g. 'ab-418-2023-24', 'ab-787-2021-22',
     'abx1-4-2025-26-1st-ex-sess'. Session: with a date (story/release date, YYYY-MM[-DD]) the latest session of that number
     that started (Dec 1 of the year before) on or before it, else its earliest (same rule as the story counts); without a
     date the session with the most stories, then the latest. Returns '' when that bill/session is not an author-led bill
     of his (coauthored, unknown): show plain text then. find() also accepts the bare 'ab-418' (most covered session). */
  function billSlug(bill, opts, ctx){
    ctx = ctx || CTX; if (!ctx) return '';
    var M = build(ctx), k = bkey(bill), date = String((opts && opts.date) || '').slice(0, 10);
    if (date && /^\d{4}-\d{2}/.test(date)){
      var ss = M.ses.get(k) || []; if (!ss.length) return '';
      var d = date.length < 10 ? date.slice(0, 7) + '-15' : date, s = ss.filter(function(x){ return sesStart(x) <= d; }).pop() || ss[0];
      var it = M.by.get(k + '|' + s); return it ? it.slug : '';
    }
    var c = M.items.filter(function(it){ return bkey(it.bill) === k; }).sort(function(a, b){ return b.n - a.n || (a.ses < b.ses ? 1 : -1); });
    return c.length ? c[0].slug : '';
  }

  AJGTabs.register({
    id: 'bills', list: list, page: page, billSlug: billSlug,
    /* old links: #bill_timeline / #insights/bill_timeline / #press-desk/bills with bill, s (session), range */
    legacy: function(p, ctx){
      if (!p.bill) return { params: {}, sub: '' };
      var M = build(ctx), k = bkey(p.bill), c = M.items.filter(function(it){ return bkey(it.bill) === k; });
      var s = c.filter(function(it){ return p.s && (it.ses === p.s || it.ses.slice(0, 9) === String(p.s).slice(0, 9)); })[0];
      var pick = s || c.slice().sort(function(a, b){ return b.n - a.n || (a.ses < b.ses ? 1 : -1); })[0];
      return pick ? { params: {}, sub: pick.slug } : { params: { q: String(p.bill), cov: '~' }, sub: '' };
    }
  });
})();
