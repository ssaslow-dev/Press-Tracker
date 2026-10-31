/* Press desk › Pitch (REORG-v1, agent-reorg 2026-10-27; replaces the Insights "Reporter outreach list", same view id
   'reporters' so old links and the story panel's "Reporter in Pitch" links keep working).
   Question: who do I pitch on X? Reporters (people only: author kind 'person'; staff groups, boards, wires and
   organisations left out; Jesse Gabriel and 'Op-ed by Gabriel' stories left out; one entry per person via the tracker's
   authorKey + canon) who wrote at least one story mentioning him in the last 24 months (PITCH24-v1: Sammy 2026-10-27 "24 months";
   the 12/24 toggle is gone, an old win=12 link opens the 24-month list), optionally on one issue. Per reporter: outlets in the window (most stories first), stories in
   the window (on the issue when one is picked), negative stories among them, top 3 issues in the window, last story.
   Copy names copies "Name (Outlet)" for every row shown; CSV downloads them. No contact details exist in the data.
   Params: issue, author (highlights that reporter). Lists show 100 rows (25 on a phone) then more. */
(function(){ "use strict";
  var SKIP_TOPIC = {'': 1, 'Unassigned': 1};
  var NEG = {'Negative': 1, 'Very negative': 1};
  var memo = {};
  var st = {q: '', sort: 'stories', dir: -1, shown: 0, hl: '', want: null};
  var COLS = [['name', 'Reporter', 1], ['outlets', 'Outlet', 1], ['stories', 'Stories', -1], ['neg', 'Negative', -1], ['topics', 'Top issues', 1], ['last', 'Last story', -1]];

  function cutoff(ctx, win){ var d = new Date(ctx.TODAY + 'T12:00:00Z'); d.setUTCMonth(d.getUTCMonth() - win); return d.toISOString().slice(0, 10); }
  function byCount(m){ return Array.from(m.entries()).sort(function(a, b){ return b[1] - a[1] || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0); }).map(function(x){ return x[0]; }); }

  /* every person's stories in the window: [{p, r}] once per person per story */
  function people(ctx, win){
    var k0 = ctx.version + '|' + ctx.D.length + '|' + win;
    if (memo[k0]) return memo[k0];
    var cut = cutoff(ctx, win), P = new Map();
    ctx.D.forEach(function(r){
      if (!r || r.role === 'Op-ed by Gabriel' || !r.date || r.date.length < 10 || r.date <= cut) return;
      var seen = new Set();
      var titles = new Set(String(r.atitle || '').split(';').map(function(t){ return ctx.authorKey(t); }).filter(Boolean));
      (r.authors || []).forEach(function(a){
        a = String(a || '').trim(); if (!a || titles.has(ctx.authorKey(a))) return;
        if ((ctx.authorKind ? ctx.authorKind(a) : 'person') !== 'person') return;
        var k = ctx.authorKey(a); if (!k || k === 'jesse gabriel' || seen.has(k)) return; seen.add(k);
        var p = P.get(k); if (!p) { p = {key: k, name: ctx.canonAuthors([a])[0] || a, rs: []}; P.set(k, p); }
        p.rs.push(r);
      });
    });
    return (memo[k0] = P);
  }
  function compute(ctx, win, issue){
    var list = [];
    people(ctx, win).forEach(function(p){
      var rs = issue ? p.rs.filter(function(r){ return r.topic === issue; }) : p.rs;
      if (!rs.length) return;
      var out = new Map(), top = new Map(), neg = 0, last = null;
      rs.forEach(function(r){ if (r.outlet) out.set(r.outlet, (out.get(r.outlet) || 0) + 1); if (NEG[r.tone]) neg++; if (!last || r.date > last.date) last = r; });
      p.rs.forEach(function(r){ var t = String(r.topic || '').trim(); if (!SKIP_TOPIC[t]) top.set(t, (top.get(t) || 0) + 1); });
      var o = {key: p.key, name: p.name, stories: rs.length, neg: neg, outlets: byCount(out), topics: byCount(top).slice(0, 3),
        last: last ? last.date : '', lastId: last ? last.id : '', lastLabel: last ? ctx.dateLabel(last) : ''};
      o._s = ctx.fold([o.name, o.outlets.join(' '), o.topics.join(' ')].join(' | '));
      list.push(o);
    });
    list.sort(function(a, b){ return b.stories - a.stories || (b.last < a.last ? -1 : b.last > a.last ? 1 : 0) || a.name.localeCompare(b.name); });
    list.forEach(function(o, i){ o.rank = i + 1; });
    return list;
  }
  function issues(ctx, win){ var c = new Map(); people(ctx, win).forEach(function(p){ p.rs.forEach(function(r){ var t = String(r.topic || '').trim(); if (!SKIP_TOPIC[t]) c.set(t, (c.get(t) || 0) + 1); }); });
    return byCount(c); }
  function cmp(key, dir){
    return function(a, b){
      var x, y;
      if (key === 'name') { x = a.name.toLowerCase(); y = b.name.toLowerCase(); }
      else if (key === 'outlets' || key === 'topics') { x = (a[key][0] || '￿').toLowerCase(); y = (b[key][0] || '￿').toLowerCase(); }
      else { x = a[key]; y = b[key]; }
      return (x < y ? -1 : x > y ? 1 : 0) * dir || a.rank - b.rank;
    };
  }
  var WIN = 24;   // PITCH24-v1: fixed window (months)
  function P(ctx){ var p = ctx.params || {}; return {win: WIN, issue: p.issue || '', author: p.author || ''}; }
  function shown(ctx){
    var p = P(ctx), q = ctx.fold(st.q), list = compute(ctx, p.win, p.issue);
    var out = q ? list.filter(function(o){ return o._s.indexOf(q) >= 0; }) : list.slice();
    out.sort(cmp(st.sort, st.dir)); return out;
  }
  var phone = function(){ return (window.innerWidth || 1400) <= 640; };
  var STEP = function(){ return phone() ? 25 : 100; };

  var CSS = '.rpo .rpo-ctl{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:4px 0 12px}' +
    '.rpo .search{max-width:360px}.rpo .rpo-n{color:var(--ink-3);font-size:12.5px;margin-right:auto}' +
    '.rpo .rpo-ans{font-size:15px;font-weight:600;color:var(--ink);margin:6px 0 10px;max-width:90ch}' +
    '.rpo .seg.rpo-win{display:inline-flex}.rpo .seg.rpo-win button{flex:none;padding:5px 12px;white-space:nowrap}' +
    '.rpo table.db td{font-size:13px}.rpo td.num{text-align:right;font-variant-numeric:tabular-nums}' +
    '.rpo th.num button{text-align:right}.rpo .sub{color:var(--ink-3);font-size:12px}' +
    '.rpo tbody tr.hl{background:var(--sel);box-shadow:inset 3px 0 0 var(--accent)}' +
    '.rpo .rpo-sort{display:none}.rpo .rpo-more{display:flex;justify-content:center;padding:12px 0 2px}' +
    '.rpo td .linkbtn{text-align:left}.rpo td.nw{white-space:nowrap}.rpo td.neg b{color:var(--bad,#b4503c)}' +
    '.rpo td.nm .linkbtn{text-decoration:none;font-weight:600;color:var(--ink);text-align:left}' +
    '.rpo td.nm .linkbtn:hover{color:var(--accent);text-decoration:underline}' +
    '@media (max-width:760px){.rpo table.db thead{display:none}.rpo table.db,.rpo table.db tbody,.rpo table.db tr,.rpo table.db td{display:block;width:auto}' +
    '.rpo table.db tr{padding:10px 2px;border-bottom:1px solid var(--line-2)}.rpo table.db td{border:0;padding:2px 4px}' +
    '.rpo table.db td[data-l]::before{content:attr(data-l) ": ";color:var(--ink-3);font-size:11.5px;text-transform:uppercase;letter-spacing:.05em}' +
    '.rpo td.num{text-align:left}.rpo .search{max-width:none;flex:1 1 100%}.rpo .rpo-sort{display:block}}';

  function rowHtml(o, ctx){
    var e = ctx.esc;
    var outl = o.outlets.slice(0, 2).map(e).join('; ') + (o.outlets.length > 2 ? ' <span class="sub">+' + (o.outlets.length - 2) + ' more</span>' : '');
    return '<tr data-k="' + e(o.key) + '"' + (o.key === st.hl ? ' class="hl"' : '') + '>' +
      '<td class="nm"><button class="linkbtn" data-act="clips" title="Show ' + e(o.name) + '’s stories in Clips">' + e(o.name) + '</button></td>' +
      '<td data-l="Outlet" title="' + e(o.outlets.join('; ')) + '">' + outl + '</td>' +
      '<td class="num" data-l="Stories">' + ctx.fmt(o.stories) + '</td>' +
      '<td class="num neg" data-l="Negative">' + (o.neg ? '<b>' + ctx.fmt(o.neg) + '</b>' : '<span class="sub">0</span>') + '</td>' +
      '<td data-l="Top issues">' + (o.topics.length ? o.topics.map(e).join(', ') : '<span class="sub">—</span>') + '</td>' +
      '<td class="nw" data-l="Last story">' + (o.lastId ? '<button class="linkbtn" data-act="story" title="Open the latest story">' + e(o.lastLabel) + '</button>' : '') + '</td></tr>';
  }
  function drawTable(el, ctx){
    var rows = shown(ctx), body = el.querySelector('.rpo-body'), n = el.querySelector('.rpo-n'), p = P(ctx), total = compute(ctx, p.win, p.issue).length;
    if (!st.shown) st.shown = STEP();
    if (st.hl) { var at = rows.findIndex(function(o){ return o.key === st.hl; }); if (at >= st.shown) st.shown = at + 1; }
    var lim = Math.min(st.shown, rows.length);
    var ss = el.querySelector('select.rpo-sort'); if (ss) ss.value = st.sort;
    n.textContent = st.q ? ctx.fmt(rows.length) + ' of ' + ctx.pl(total, 'reporter', 'reporters') + ' match' : ctx.pl(total, 'reporter', 'reporters');
    if (!rows.length) { body.innerHTML = '<div class="empty">' + (st.q ? 'No reporters match “' + ctx.esc(st.q) + '”.' : 'No reporter wrote about him on this issue in this window.') + '</div>'; return; }
    var head = COLS.map(function(c){ var on = st.sort === c[0];
      return '<th' + (c[0] === 'stories' || c[0] === 'neg' ? ' class="num"' : '') + '><button data-sort="' + c[0] + '"' +
        (on ? ' data-dir="' + (st.dir > 0 ? '▲' : '▼') + '" aria-sort="' + (st.dir > 0 ? 'ascending' : 'descending') + '"' : '') + '>' + c[1] + '</button></th>'; }).join('');
    var rest = rows.length - lim;
    body.innerHTML = '<div class="tablewrap"><table class="db"><thead><tr>' + head + '</tr></thead><tbody>' +
      rows.slice(0, lim).map(function(o){ return rowHtml(o, ctx); }).join('') + '</tbody></table></div>' +
      (rest > 0 ? '<div class="rpo-more"><button class="btn" data-act="more">' + (phone() ? 'Show ' + Math.min(rest, STEP()) + ' more' : 'Show all ' + ctx.fmt(rows.length)) + '</button></div>' : '');
  }
  function names(rows){ return rows.map(function(o){ return o.name + (o.outlets[0] ? ' (' + o.outlets[0] + ')' : ''); }).join('\n'); }
  function csv(ctx){
    var p = P(ctx), rows = shown(ctx);
    var text = ctx.csv(rows, [['Reporter', 'name'], ['Outlets', function(o){ return o.outlets.join('; '); }],
      ['Stories (last ' + p.win + ' months' + (p.issue ? ', ' + p.issue : '') + ')', 'stories'], ['Negative stories', 'neg'],
      ['Top issues', function(o){ return o.topics.join('; '); }], ['Last story', 'last']]);
    return ctx.saveFile('AJG pitch list ' + p.win + ' months' + (p.issue ? ' ' + p.issue.replace(/[\\/:*?"<>|]+/g, '-') : '') + ' ' + (ctx.TODAY || '') + '.csv', text);
  }
  function answer(ctx, p, list){
    var on = p.issue ? ' on ' + p.issue : '';
    if (!list.length) return 'No reporter wrote about him' + on + ' in the last ' + p.win + ' months.';
    var top = list.slice(0, 3).map(function(o){ return o.name + (o.outlets[0] ? ', ' + o.outlets[0] : '') + ' (' + o.stories + ')'; });
    return ctx.pl(list.length, 'reporter', 'reporters') + ' wrote about him' + on + ' in the last ' + p.win + ' months. Most active: ' +
      (top.length < 2 ? top[0] : top.slice(0, -1).join('; ') + ' and ' + top[top.length - 1]) + '.';
  }

  var cur = null;
  AJGInsights.register({
    id: 'reporters',
    label: 'Pitch',
    render: function(el, ctx){
      cur = ctx;
      var p = P(ctx), want = p.author;
      st.hl = want ? ctx.authorKey(ctx.canonAuthors([want])[0] || want) : '';
      if (st.hl) st.q = '';
      var list = compute(ctx, p.win, p.issue), iss = issues(ctx, p.win);
      el.innerHTML = '<style>' + CSS + '</style><div class="in-sec rpo"><div class="card pad">' +
        '<h2 class="sec">Pitch: who do I pitch' + (p.issue ? ' on ' + ctx.esc(p.issue) : '') + '?</h2>' +
        '<div class="cap">Reporters (people only: no staff, board, wire or organisation bylines) who wrote about him in the last 24 months, most stories first. Names and outlets only; the tracker has no contact details. Click a name to see their stories in Clips, a date to open their latest story.</div>' +
        '<div class="rpo-ans">' + ctx.esc(answer(ctx, p, list)) + '</div>' +
        '<div class="an-controls" style="margin:4px 0 10px">' +
          '<label>Issue<select class="sel rpo-iss" aria-label="Issue"><option value="">All issues</option>' +
          iss.map(function(t){ return '<option value="' + ctx.esc(t) + '"' + (t === p.issue ? ' selected' : '') + '>' + ctx.esc(t) + '</option>'; }).join('') +
          (p.issue && iss.indexOf(p.issue) < 0 ? '<option selected value="' + ctx.esc(p.issue) + '">' + ctx.esc(p.issue) + '</option>' : '') + '</select></label></div>' +
        '<div class="rpo-ctl"><label class="search"><input type="search" placeholder="Search reporter, outlet, issue" aria-label="Search reporters" value="' + ctx.esc(st.q) + '"></label>' +
          '<select class="sel rpo-sort" aria-label="Sort by">' + COLS.map(function(c){ return '<option value="' + c[0] + '"' + (st.sort === c[0] ? ' selected' : '') + '>Sort: ' + c[1].toLowerCase() + '</option>'; }).join('') + '</select>' +
          '<span class="rpo-n"></span><button class="btn" data-act="names" title="Copy the names (and outlets) of every reporter shown">Copy names</button>' +
          '<button class="btn primary" data-act="csv" title="Download the rows shown as a CSV file">Download CSV</button></div>' +
        '<div class="rpo-body"></div></div></div>';
      if (want && !list.some(function(o){ return o.key === st.hl; })) {
        if (want !== st.want && ctx.toast) ctx.toast(want + ' has no story in the last ' + p.win + ' months' + (p.issue ? ' on ' + p.issue : '') + ' (people only).');
        st.hl = '';
      }
      st.shown = 0;
      drawTable(el, ctx);
      if (want && want !== st.want) { var tr = el.querySelector('tr.hl'); if (tr && tr.scrollIntoView) setTimeout(function(){ try { tr.scrollIntoView({block: 'center'}); } catch (e) {} }, 0); }
      st.want = want;
      var go = function(np){ var q = Object.assign({}, cur.params, np); Object.keys(q).forEach(function(k){ if (q[k] == null || q[k] === '') delete q[k]; });
        delete q.author; delete q.win; cur.setParams(q); cur.refresh(); };   // PITCH24-v1: no window param
      el.addEventListener('input', function(ev){ if (!ev.target.matches('input[type=search]')) return; st.q = ev.target.value; st.shown = 0; drawTable(el, cur); });
      el.addEventListener('change', function(ev){
        if (ev.target.matches('select.rpo-sort')) { var k = ev.target.value; st.sort = k; st.dir = COLS.filter(function(x){ return x[0] === k; })[0][2]; drawTable(el, cur); return; }
        if (ev.target.matches('select.rpo-iss')) go({issue: ev.target.value});
      });
      el.addEventListener('click', function(ev){
        var b = ev.target.closest('button'), tr = ev.target.closest('tbody tr'), c = cur;
        if (!b) return;
        if (b.dataset.sort) { var k = b.dataset.sort, def = COLS.filter(function(x){ return x[0] === k; })[0][2];
          if (st.sort === k) st.dir = -st.dir; else { st.sort = k; st.dir = def; } drawTable(el, c); return; }
        if (b.dataset.act === 'csv') { csv(c); return; }
        if (b.dataset.act === 'names') { var rs = shown(c); c.copy(names(rs), 'Copied ' + c.pl(rs.length, 'name', 'names'), b); return; }
        if (b.dataset.act === 'more') { st.shown = phone() ? st.shown + STEP() : 1e9; drawTable(el, c); return; }
        if (!tr) return;
        var p2 = P(c), o = compute(c, p2.win, p2.issue).filter(function(x){ return x.key === tr.dataset.k; })[0];
        if (!o) return;
        if (b.dataset.act === 'story') { c.openStory(o.lastId); return; }
        c.clips(p2.issue ? {author: o.name, topic: p2.issue} : {author: o.name});
      });
    }
  });
})();
