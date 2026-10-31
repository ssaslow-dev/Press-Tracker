/* Stub tab module (agent-tabs, TABS-v1 Phase A): shows how a tab plugs into the framework. NOT shipped: it lives in
   build/tests/tabs/ (tabs_assemble only takes build/tabs/<id>.js). It lists ISSUES with their stories, the way a
   Reporters or Outlets module lists people or outlets: two-level (units = stories, filtered by story facets, grouped into
   one item per issue, then item facets), a list with sortable columns, and an entity page per issue (#stub/<slug>).
   The harness can register it under other ids (window.__STUB_IDS) to test the menu, redirects and legacy links. */
(function(){ "use strict";
  var PTS = null;
  function make(id){
    var memo = { v: null, units: null };
    function units(ctx){   // every tracker story with a date (framework memoizes per ctx.version)
      return ctx.D.filter(function(r){ return r && r.date; });
    }
    function group(us, ctx){   // one item per issue over the given stories
      var m = new Map();
      us.forEach(function(r){ var t = String(r.topic || '').trim() || 'Unassigned', o = m.get(t);
        if (!o){ o = { key: ctx.slug(t), name: t, rs: [], neg: 0, last: '', lastId: '', langs: new Map() }; m.set(t, o); }
        o.rs.push(r); if (r.tone === 'Negative' || r.tone === 'Very negative') o.neg++;
        if (r.date > o.last){ o.last = r.date; o.lastId = r.id; }
        var l = ctx.langOf(r); o.langs.set(l, (o.langs.get(l) || 0) + 1); });
      return Array.from(m.values()).map(function(o){ o.stories = o.rs.length; o.tone = ctx.tone(o.rs); o.bucket = o.stories >= 100 ? '100+' : o.stories >= 10 ? '10–99' : '1–9'; return o; });
    }
    var list = {
      noun: ['issue', 'issues'], title: 'Stub: issues', placeholder: 'Search issues',
      cap: 'Framework demo. One row per issue over the stories that pass the story filters (date, language); story count and tone are item filters. Click an issue to open its page.',
      units: units, group: group, key: function(o){ return o.key; }, text: function(o){ return o.name; },
      facets: [
        { key: 'date', label: 'Date range', type: 'date', level: 'unit', def: '24m', date: function(r){ return r.date; }, hint: 'Stories dated in this range.' },
        { key: 'lang', label: 'Language', level: 'unit', vals: function(r){ return r.lang || 'English'; }, open: true },
        { key: 'outlet', label: 'Outlet', level: 'unit', search: true, limit: 6, vals: function(r){ return r.outlet; } },
        { key: 'size', label: 'Story count', type: 'one', options: [
          { id: 'big', label: '100 or more', test: function(o){ return o.stories >= 100; } },
          { id: 'mid', label: '10 to 99', test: function(o){ return o.stories >= 10 && o.stories < 100; } },
          { id: 'small', label: '1 to 9', test: function(o){ return o.stories < 10; } }] },
        { key: 'neg', label: 'Negative stories', vals: function(o){ return o.neg ? 'Some' : 'None'; }, order: ['Some', 'None'] }
      ],
      columns: [
        { key: 'name', label: 'Issue', val: function(o){ return o.name; }, cell: function(o, ctx){ return '<button class="linkbtn tt-open">' + ctx.esc(o.name) + '</button>'; } },
        { key: 'stories', label: 'Stories', num: true, dir: -1, val: function(o){ return o.stories; }, cell: function(o, ctx){ return ctx.fmt(o.stories); } },
        { key: 'neg', label: 'Negative', num: true, dir: -1, val: function(o){ return o.neg; } },
        { key: 'tone', label: 'Tone avg', num: true, dir: -1, sort: function(o){ return o.tone.avg; }, val: function(o){ return o.tone.text; } },
        { key: 'last', label: 'Last story', dir: -1, val: function(o){ return o.last; } }
      ],
      sort: { key: 'stories', dir: -1 }, open: 'page', step: { desk: 10, phone: 5 },
      answer: function(res, st, ctx){ window.__tbctx = ctx; return res.length ? ctx.pl(res.length, 'issue', 'issues') + ' match. Most covered: ' + res.slice().sort(function(a, b){ return b.stories - a.stories; })[0].name + '.' : ''; },
      copies: [{ label: 'Copy names', sub: 'One issue per line', text: function(res){ return res.map(function(o){ return o.name; }).join('\n'); } }],
      csvName: function(st, ctx){ return 'AJG stub issues ' + ctx.TODAY + '.csv'; }
    };
    var page = {
      slug: function(o, ctx){ return o.key; },
      find: function(sub, ctx){ var all = group(units(ctx), ctx);
        if (sub === 'tiny'){ var t = group(units(ctx).filter(function(r){ return r.topic === 'Guns'; }).slice(0, 2), ctx)[0]; t.name = 'Tiny (2 Guns stories)'; return t; }   // a small entity: no chart, a plain line
        return all.filter(function(o){ return o.key === sub; })[0] || null; },
      spec: function(o, ctx){
        return { kicker: 'Issue', title: o.name, noun: 'issue', backLabel: 'All issues',
          sub: ctx.pl(o.stories, 'story', 'stories') + ', latest ' + ctx.esc(o.last),
          facts: [['Stories', ctx.fmt(o.stories)], ['Negative', ctx.fmt(o.neg)], ['Tone average', o.tone.text || ''],
            ['Languages', Array.from(o.langs.keys()).map(ctx.esc).join(', ')],
            ['Latest story', o.lastId ? '<button class="linkbtn" data-tbstory="' + ctx.esc(o.lastId) + '">' + ctx.esc(o.last) + '</button>' : '']],
          rows: o.rs, clips: { topic: o.name } };
      }
    };
    return { id: id, label: id === 'stub' ? 'Stub' : null, list: list, page: page,
      legacy: function(p, ctx){ var q = {}; if (p.author) q.q = p.author; if (p.id) q.q = p.id; if (p.issue) q.q = p.issue; return { params: q, sub: p.sub || '' }; } };
  }
  var ids = (window.__STUB_IDS && window.__STUB_IDS.length) ? window.__STUB_IDS : ['stub'];
  ids.forEach(function(id){ var m = make(id); if (!m.label) delete m.label; AJGTabs.register(m); });
})();
