/* CLEAN_HTML_JS — JavaScript port of code/clean_html.py (T37, agent-code 2026-10-27). Same algorithm, same rules JSON
   (code/clean_rules.json, embedded in the tracker as <script id="cleanrules">). The tracker's Update button runs it on
   every page TinyFish fetches before keeping it, and uses it to skip finds whose only Gabriel mention is outside the
   article (comments, teasers, tags). Per-file overrides (clean_overrides.json) are library-only and not used here.
   Keep in step with clean_html.py: tests in build/test_clean/ compare the two on the same files. */
const CleanHTML = (() => {
  const BLOCK = new Set(['address','article','aside','blockquote','body','caption','center','dd','details','dialog','dir','div','dl','dt',
    'fieldset','figcaption','figure','footer','form','h1','h2','h3','h4','h5','h6','header','hgroup','hr','html','li','main','menu','nav',
    'ol','p','pre','section','summary','table','tbody','td','tfoot','th','thead','tr','ul','legend','option','select','button']);
  const SKIP = new Set(['script','style','template','noscript','head','title','meta','link','iframe','object','svg','math','canvas',
    'audio','video','source','track','textarea','input']);
  const MEDIA_TAGS = ['img','picture','video','audio','iframe','svg','canvas','object','embed'];
  const MEDIA = new Set(MEDIA_TAGS.concat(['table','hr']));
  const WS = /[ \t\n\r\f\v\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+/g;
  const CJK = /[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff]/g;
  const WORD = /[A-Za-z0-9\u00c0-\u024f\u0370-\u03ff\u0400-\u04ff\u0530-\u058f\u0590-\u05ff\u0600-\u06ff\u0e00-\u0e7f\u1e00-\u1eff]+/g;
  const HDR_OD = /^(.{1,140}?) · ((?:\d{4}(?:-\d\d){0,2})|undated|n\.d\.)$/;
  const HDR_URL = /^https?:\/\/\S+$/;
  const HDR_SAVED = /^Saved \d{4}-\d\d-\d\d\b.*$/;
  const GAB_DEFAULT = '(?<![A-Za-z])(?<![Ss][Aa][Nn] )[Gg][Aa](?:-\\s*)?[Bb][Rr][Ii][Ee][Ll](?![A-Za-z])|가브리엘|Габриэл|Габриел|גבריאל|加布里埃[尔爾]|加布尔|加布里爾|加布里尔|蓋博|盖博|جسی گابریل|گابریل|Ջեսի Գաբրիել|Գաբրիել';   // INCL-v1: same source as clean_html.py / clean_rules.json
  const norm = t => String(t || '').replace(WS, ' ').trim();
  const nwords = t => { t = String(t || ''); return ((t.replace(CJK, ' ').match(WORD) || []).length) + ((t.match(CJK) || []).length); };
  const lkey = t => t.toLowerCase().replace(/\d+/g, '#');
  const RX = new Map();
  function rx(p, anchored){
    const k = (anchored ? '^' : '~') + p; let r = RX.get(k);
    if (!r){ let src = p, fl = ''; if (src.startsWith('(?i)')){ fl = 'i'; src = src.slice(4); }
      r = new RegExp(anchored ? '^(?:' + src + ')$' : src, fl + (anchored ? '' : 'g')); RX.set(k, r); }
    return r;
  }
  const full = (p, t) => rx(p, true).test(t);
  const search = (p, t) => { const r = rx(p, false); r.lastIndex = 0; return r.test(t); };
  // sha1 (12 hex) of a string's UTF-8 bytes, for the image rules
  function sha12(str){
    const b = new TextEncoder().encode(str), l = b.length, n = ((l + 8 >> 6) + 1) * 16, w = new Int32Array(n);
    for (let i = 0; i < l; i++) w[i >> 2] |= b[i] << (24 - (i % 4) * 8);
    w[l >> 2] |= 0x80 << (24 - (l % 4) * 8); w[n - 1] = l * 8;
    let h0 = 0x67452301, h1 = 0xEFCDAB89, h2 = 0x98BADCFE, h3 = 0x10325476, h4 = 0xC3D2E1F0; const x = new Int32Array(80);
    for (let i = 0; i < n; i += 16){
      let a = h0, bb = h1, c = h2, d = h3, e = h4;
      for (let j = 0; j < 80; j++){
        x[j] = j < 16 ? w[i + j] : ((x[j-3] ^ x[j-8] ^ x[j-14] ^ x[j-16]) << 1) | ((x[j-3] ^ x[j-8] ^ x[j-14] ^ x[j-16]) >>> 31);
        const f = j < 20 ? (bb & c) | (~bb & d) : j < 40 ? bb ^ c ^ d : j < 60 ? (bb & c) | (bb & d) | (c & d) : bb ^ c ^ d;
        const k = j < 20 ? 0x5A827999 : j < 40 ? 0x6ED9EBA1 : j < 60 ? 0x8F1BBCDC : 0xCA62C1D6;
        const t = (((a << 5) | (a >>> 27)) + f + e + k + x[j]) | 0; e = d; d = c; c = (bb << 30) | (bb >>> 2); bb = a; a = t;
      }
      h0 = h0 + a | 0; h1 = h1 + bb | 0; h2 = h2 + c | 0; h3 = h3 + d | 0; h4 = h4 + e | 0;
    }
    return [h0, h1, h2, h3, h4].map(v => (v >>> 0).toString(16).padStart(8, '0')).join('').slice(0, 12);
  }
  const imgKey = src => sha12(String(src || '').replace(/&amp;/g, '&').trim());
  const isEl = n => n && n.nodeType === 1;
  const isText = n => n && n.nodeType === 3;
  const tag = n => (n.localName || n.nodeName || '').toLowerCase();
  function nodeText(n){
    if (isText(n)) return n.data;
    if (isEl(n)){ if (SKIP.has(tag(n))) return ''; let s = ''; for (const c of n.childNodes) s += nodeText(c); return s; }
    return '';
  }
  function hasBlock(el, cache){
    if (cache.has(el)) return cache.get(el);
    let r = false;
    for (const c of el.childNodes){ if (isEl(c) && !SKIP.has(tag(c)) && (BLOCK.has(tag(c)) || tag(c) === 'br' || hasBlock(c, cache))){ r = true; break; } }
    cache.set(el, r); return r;
  }
  function extractBlocks(root){
    const out = [], cache = new Map();
    const flush = (run, parent) => { const t = norm(run.map(nodeText).join('')); if (t) out.push({ i: out.length, nodes: run.slice(), text: t, tag: isEl(parent) ? tag(parent) : '', el: parent, hdr: null, why: null, pat: null }); run.length = 0; };
    const walk = el => {
      const run = [];
      for (const c of Array.from(el.childNodes)){
        if (isText(c)) run.push(c);
        else if (isEl(c)){
          const t = tag(c);
          if (t === 'br'){ run.push(c); flush(run, el); }
          else if (SKIP.has(t)) run.push(c);
          else if (BLOCK.has(t) || hasBlock(c, cache)){ flush(run, el); walk(c); }
          else run.push(c);
        }
      }
      flush(run, el);
    };
    walk(root); return out;
  }
  function markHeader(blocks, body){
    const first = Array.from(body.childNodes).find(isEl);
    if (!first || tag(first) !== 'div') return;
    const inside = blocks.filter(b => b.el === first);
    const kinds = inside.map(b => HDR_SAVED.test(b.text) ? 'saved' : HDR_URL.test(b.text) ? 'url' : HDR_OD.test(b.text) ? 'od' : null);
    if (kinds.length && kinds.some(Boolean) && kinds.every(Boolean)) inside.forEach((b, k) => { b.hdr = kinds[k]; });
  }
  function normOutlet(s){
    s = String(s || '').normalize('NFKD').toLowerCase().trim().replace(/[\u0300-\u036f]/g, '');
    s = s.replace(/,\s*the$|^the\s+/, '');
    return s.replace(/[^a-z0-9\u0080-\uffff]+/g, ' ').trim();
  }
  function hostOf(url){ return String(url || '').trim().toLowerCase().replace(/^[a-z]+:\/\//, '').split('/')[0].split(':')[0].replace(/^www\./, ''); }
  function siteRules(rules, url, outlet){
    const host = hostOf(url), on = normOutlet(outlet), byHost = [], byOutlet = [];
    for (const [key, s] of Object.entries(rules.sites || {})){
      if (host && (s.hosts || []).some(h => host === h || host.endsWith('.' + h))) byHost.push(key);
      else if (on && (s.outlets || []).some(o => normOutlet(o) === on)) byOutlet.push(key);
    }
    return byHost.length ? byHost : byOutlet;
  }
  const KINDS = ['kill','lkill','tail','ltail','strip','section','cut','drop','img'];
  function merged(rules, keys){
    const g = rules.generic || {}, m = {};
    KINDS.forEach(k => { m[k] = (g[k] || []).map(p => [p, 'generic']); });
    m.head = []; m.allow_long = false; m.allow_big = false; const skip = new Set();
    for (const key of keys){
      const s = rules.sites[key];
      KINDS.forEach(k => { (s[k] || []).forEach(p => m[k].push([p, key])); });
      if (s.head) m.head.push([s.head, key]);
      m.allow_long = m.allow_long || !!s.allow_long; m.allow_big = m.allow_big || !!s.allow_big;
      (s.skip_generic || []).forEach(p => skip.add(p));
    }
    if (skip.size) ['kill','tail','strip','section','drop'].forEach(k => { m[k] = m[k].filter(([p, src]) => !(src === 'generic' && skip.has(p))); });
    return m;
  }
  function dropMatch(el, d){
    if (d.tag && !full(d.tag, tag(el))) return false;
    if (d.attr){ const v = el.getAttribute && el.getAttribute(d.attr); if (v === null || v === undefined) return false; if (!search(d.re, String(v))) return false; }
    return true;
  }
  const isTeaser = (t, maxw) => nwords(t) <= maxw && !/[.!?。！？]["”’)]?$/.test(t);
  function decide(blocks, m){
    const body = blocks.filter(b => !b.hdr); if (!body.length) return [];
    for (const [d, src] of m.drop){
      for (const b of body){
        if (b.why) continue;
        let p = b.el;
        while (p && isEl(p) && !['body','html'].includes(tag(p))){ if (dropMatch(p, d)){ b.why = 'drop:' + src; b.pat = JSON.stringify(d); break; } p = p.parentNode; }
        if (!b.why) for (const n of b.nodes) if (isEl(n) && dropMatch(n, d) && nodeText(n).trim() && norm(nodeText(n)) === b.text){ b.why = 'drop:' + src; b.pat = JSON.stringify(d); break; }
      }
    }
    for (const [h, src] of m.head){
      const j = h === 'h1' ? body.findIndex(b => b.tag === 'h1') : body.findIndex(b => full(h, b.text));
      if (j > 0) body.slice(0, j).forEach(b => { if (!b.why){ b.why = 'head:' + src; b.pat = h; } });
    }
    let start = body.findIndex(b => b.tag === 'h1' && !b.why); if (start < 0) start = 0;
    for (const [c, src] of m.cut){
      const a = c[0], z = c[1], inc = c.length > 2 ? c[2] : false;
      let k = start ? start + 1 : 0;
      while (k < body.length){
        if (full(a, body[k].text)){
          let e = null;
          if (z){ e = null; for (let q = k + 1; q < body.length; q++) if (full(z, body[q].text)){ e = q; break; } if (e === null){ k++; continue; } }
          const end = e === null ? body.length : (inc ? e + 1 : e);
          body.slice(k, end).forEach(b => { if (!b.why){ b.why = 'cut:' + src; b.pat = JSON.stringify(c); } });
          k = end;
        } else k++;
      }
    }
    let cutAt = null;
    for (let k = start ? start + 1 : 1; k < body.length && !cutAt; k++){
      const t = body[k].text;
      for (const [p, src] of m.tail) if (full(p, t)){ cutAt = [k, 'tail:' + src, p]; break; }
      if (!cutAt && m.ltail.length){ const lk = lkey(t); for (const [p, src] of m.ltail) if (full(p, lk)){ cutAt = [k, 'tail:' + src, 'L:' + p]; break; } }
    }
    if (cutAt) body.slice(cutAt[0]).forEach(b => { if (!b.why){ b.why = cutAt[1]; b.pat = cutAt[2]; } });
    for (const [s, src] of m.section){
      const pat = typeof s === 'string' ? s : s[0], maxw = typeof s === 'string' ? 25 : s[1];
      let k = start ? start + 1 : 0;
      while (k < body.length){
        if (!body[k].why && full(pat, body[k].text)){
          body[k].why = 'section:' + src; body[k].pat = pat; let q = k + 1;
          while (q < body.length && isTeaser(body[q].text, maxw) && !body[q].hdr){ if (!body[q].why){ body[q].why = 'section:' + src; body[q].pat = pat; } q++; }
          k = q;
        } else k++;
      }
    }
    for (const b of body){
      if (b.why) continue;
      for (const [p, src] of m.kill) if (full(p, b.text)){ b.why = 'kill:' + src; b.pat = p; break; }
      if (!b.why && m.lkill.length){ const lk = lkey(b.text); for (const [p, src] of m.lkill) if (full(p, lk)){ b.why = 'kill:' + src; b.pat = 'L:' + p; break; } }
    }
    const edits = [];
    for (const b of body){ if (b.why) continue; for (const [p, src] of m.strip) if (search(p, b.text)) edits.push([b, p, src]); }
    return edits;
  }
  function stripBlock(b, pattern){
    let done = false;
    for (const n of b.nodes.slice()) if (isEl(n) && n.parentNode && !SKIP.has(tag(n)) && norm(nodeText(n)) && full(pattern, norm(nodeText(n)))){ n.remove(); done = true; }
    if (done){ b.nodes = b.nodes.filter(n => n.parentNode); return true; }
    const texts = [];
    const collect = n => { if (isText(n)) texts.push(n); else if (isEl(n) && !SKIP.has(tag(n))) for (const c of n.childNodes) collect(c); };
    b.nodes.forEach(n => { if (n.parentNode) collect(n); });
    const raw = texts.map(t => t.data).join(''); const r = rx(pattern, false); r.lastIndex = 0;
    const spans = []; let mm; while ((mm = r.exec(raw))){ if (mm[0].length) spans.push([mm.index, mm.index + mm[0].length]); else r.lastIndex++; }
    if (!spans.length) return false;
    let pos = 0;
    for (const t of texts){
      const s0 = t.data, a = pos; pos += s0.length; let keep = '';
      for (let k = 0; k < s0.length; k++){ const g = a + k; if (!spans.some(([x, y]) => x <= g && g < y)) keep += s0[k]; }
      if (keep !== s0){ t.data = keep; done = true; }
    }
    return done;
  }
  function normUrl(u){
    u = String(u == null ? '' : u).trim(); if (!u.startsWith('http')) return '';
    u = u.toLowerCase().replace(/^https?:\/\/(www\.)?/, '').split('#')[0];
    const host = u.split('/')[0]; if (!/newsbank|oclc|google\.|proquest/.test(host)) u = u.split('?')[0];
    return u.replace(/\/+$/, '');
  }
  function headerDecision(b, sheet, aliases){
    if (b.hdr === 'saved') return ['keep', 'saved line (no column)'];
    if (!sheet) return ['keep', 'no sheet row'];
    if (b.hdr === 'url'){
      const links = ['Publisher link','NewsBank article link','ProQuest link','Link'].map(c => sheet[c]).filter(Boolean).map(normUrl);
      if (!links.length) return ['fill', { column: 'Publisher link', value: b.text }];
      return links.includes(normUrl(b.text)) ? ['remove', 'url = sheet'] : ['conflict', { column: 'Publisher link', sheet: sheet['Publisher link'] || '', file: b.text }];
    }
    const m = b.text.match(HDR_OD), o = m[1].trim(), d = m[2];
    const so = String(sheet.Outlet || ''), sd = String(sheet.Date || '').slice(0, 10);
    if (!so || !sd) return ['fill', { column: !so ? 'Outlet' : 'Date', value: !so ? o : d }];
    const same = normOutlet(o) === normOutlet(so) || ((aliases || {})[normOutlet(o)] || []).includes(normOutlet(so));
    if (same && (d === sd || (d.length < 10 && sd.startsWith(d)))) return ['remove', 'outlet+date = sheet'];
    return ['conflict', { column: 'Outlet/Date', sheet: so + ' \u00b7 ' + sd, file: b.text }];
  }
  const gabProse = (G, t) => G.test(t) && nwords(t) > 5 && nwords(t) <= 1500 && !/^\s*(window\.|var |\{|\[)/.test(t);
  function outsidePhase(blocks, f, G){
    const art = blocks.filter(b => !b.hdr); if (!art.length) return;
    if (G && f.tail_safe){   // T45: tail markers after the last paragraph naming Gabriel
      let lg = -1; art.forEach((b, k) => { if (gabProse(G, b.text)) lg = k; });
      if (lg >= 0){ let ts = -1; for (let k = lg + 1; k < art.length; k++) if (f.tail_safe.some(p => full(p, art[k].text))){ ts = k; break; }
        if (ts >= 0) art.slice(ts).forEach(b => { if (!b.why || b.why.startsWith('kill:')){ b.why = 'find:tail_safe'; b.pat = art[ts].text.slice(0, 80); } }); }
    }
    let h1 = art.findIndex(b => b.tag === 'h1'); if (h1 < 0) h1 = 0;
    const maxw = f.teaser_words || 70, minpos = f.min_position == null ? 0.5 : f.min_position, minw = f.min_words_before == null ? 150 : f.min_words_before;
    for (let i = h1 ? h1 + 1 : 1; i < art.length; i++){
      const t = art[i].text;
      const strong = (f.comments_strong || []).some(p => full(p, t));
      const weak = !strong && (f.comments || []).some(p => full(p, t));
      const rel = !strong && !weak && (f.related || []).some(p => full(p, t));
      if (!(strong || weak || rel)) continue;
      if (nwords(art.slice(0, i).filter(b => !b.why).map(b => b.text).join(' ')) < minw) continue;
      if ((weak || rel) && i < minpos * art.length) continue;
      if (rel){ const rest = art.slice(i + 1).map(b => nwords(b.text));
        if (!rest.length || Math.max(...rest) > maxw || rest.filter(n => n <= (f.short_words || 6)).length < 0.5 * rest.length) continue; }
      art.slice(i).forEach(b => { if (!b.why || b.why.startsWith('kill:')){ b.why = 'find:outside'; b.pat = t.slice(0, 80); } });
      return;
    }
  }
  function simT(a, b){
    a = normOutlet(a); b = normOutlet(b); if (!a || !b) return 0;
    if (a.includes(b) || b.includes(a)) return Math.min(a.length, b.length) >= 0.6 * Math.max(a.length, b.length) ? 1 : 0.8;
    const A = new Set(a.split(' ')), B = new Set(b.split(' ')); let n = 0; A.forEach(x => { if (B.has(x)) n++; });
    return n / new Set([...A, ...B]).size;
  }
  function articleH1(art, title){
    const h1s = []; art.forEach((b, i) => { if (b.tag === 'h1') h1s.push(i); }); if (!h1s.length) return null;
    let best = h1s[0]; if (title) h1s.forEach(i => { if (simT(art[i].text, title) > simT(art[best].text, title)) best = i; });
    const matched = !!title && simT(art[best].text, title) >= 0.6, ah = matched ? best : h1s[0];
    const before = art.slice(0, ah).reduce((s, b) => s + nwords(b.text), 0), total = art.reduce((s, b) => s + nwords(b.text), 0) || 1;
    if (before > 300 && before > 0.25 * total) return null;
    if (!matched && art.slice(0, ah).some(b => nwords(b.text) >= 30 && /[.!?。！？]/.test(b.text))) return null;
    return ah;
  }
  function findPhase(blocks, f, G, res, title){
    const art = blocks.filter(b => !b.hdr && !b.why); if (!art.length) return;
    const drop = new Map(), h1s = []; art.forEach((b, i) => { if (b.tag === 'h1') h1s.push(i); });
    const ah = articleH1(art, title || '');
    if (ah !== null && f.head === 'h1') for (let i = 0; i < ah; i++) drop.set(i, 'find:head');
    const first = ah !== null ? ah : 0;
    (f.section || []).forEach(sec => art.forEach((b, i) => { if (full(sec[0], b.text)){ if (!drop.has(i)) drop.set(i, 'find:section');
      for (let k = i + 1; k < Math.min(art.length, i + 1 + sec[2]); k++){ if (nwords(art[k].text) > sec[1]) break; if (!drop.has(k)) drop.set(k, 'find:section'); } } }));
    const ti = art.findIndex((b, i) => i > first && (f.tail || []).some(p => full(p, b.text)));
    if (ti >= 0) for (let i = ti; i < art.length; i++) if (!drop.has(i)) drop.set(i, 'find:tail');
    const rt = f.repeat_title || 0;
    art.forEach((b, i) => {
      if ((f.kill || []).some(p => full(p, b.text)) && !drop.has(i)) drop.set(i, 'find:kill');
      if (rt && ah !== null && i !== ah && b.text === art[ah].text && i < ah + rt && !drop.has(i)) drop.set(i, 'find:title');
    });
    const kept = [];
    [...drop.keys()].sort((a, b) => a - b).forEach(i => {
      if (f.protect_gabriel !== false && G.test(art[i].text)){ kept.push(art[i].text.slice(0, 120)); return; }
      art[i].why = drop.get(i); art[i].pat = drop.get(i);
    });
    if (kept.length) res.find_kept_gabriel = kept;
  }
  function tidyEmpty(body){
    let n = 0;
    body.querySelectorAll('input,button,select,textarea').forEach(t => { t.remove(); n++; });
    for (let k = 0; k < 3; k++) body.querySelectorAll('li,ul,ol,figure,figcaption,section,i').forEach(t => {
      if (t.isConnected && !t.textContent.trim() && !t.querySelector('img,picture,video,iframe,svg,table')){ t.remove(); n++; } });
    return n;
  }
  function inTree(n, root){ return n && root.contains(n); }
  function pruneEmpty(parents, doc){
    const todo = parents.slice(), seen = new Set();
    while (todo.length){
      const el = todo.pop();
      if (!el || seen.has(el) || !el.parentNode || !isEl(el) || ['body','html','head'].includes(tag(el))) continue;
      seen.add(el);
      if (norm(nodeText(el)) || MEDIA.has(tag(el)) || el.querySelector(Array.from(MEDIA).join(','))) continue;
      const par = el.parentNode; el.replaceWith(doc.createTextNode(' ')); todo.push(par);
    }
  }
  function serialize(doc, original){
    const dt = doc.doctype ? '<!DOCTYPE ' + doc.doctype.name + '>' : (/^\s*<!doctype/i.test(original) ? '<!DOCTYPE html>' : '');
    return dt + doc.documentElement.outerHTML;
  }
  /* clean one page: same result fields as clean_page() in clean_html.py */
  function cleanPage(html, opt){
    opt = opt || {}; const rules = opt.rules || {}; const mode = opt.mode || 'find';
    const res = { status: 'unchanged', flags: [], removed: [], stripped: [], header: { removed: [], kept: [], fills: [], conflicts: [] }, sites: [] };
    const doc = new DOMParser().parseFromString(String(html || ''), 'text/html');
    const body = doc.body || doc.documentElement;
    const blocks = extractBlocks(body); markHeader(blocks, body);
    const G = new RegExp(rules.gabriel || GAB_DEFAULT);
    const bodyText = blocks.filter(b => !b.hdr).map(b => b.text).join(' ');
    res.words_before = nwords(bodyText);
    res.gabriel_before = G.test(blocks.map(b => b.text).join(' '));
    const keys = siteRules(rules, opt.url, opt.outlet); res.sites = keys;
    const m = merged(rules, keys), limits = rules.limits || {};
    const longW = limits.long_block_words || 40, maxFrac = limits.max_removed_frac || 0.35;
    const allowLong = m.allow_long, allowBig = m.allow_big;
    let edits = decide(blocks, m);
    const safe = new Set();
    if (mode === 'find' && rules.find){
      outsidePhase(blocks, rules.find, G);
      const body0 = blocks.filter(b => !b.hdr); let lg = -1; body0.forEach((b, k) => { if (gabProse(G, b.text)) lg = k; });
      if (lg >= 0) body0.forEach((b, k) => { if (k > lg && b.why && (b.why.startsWith('tail:') || b.why.startsWith('find:tail_safe'))) safe.add(b); });
    }
    for (const b of blocks) if (b.why && !allowLong && b.why !== 'find:outside' && !safe.has(b) && nwords(b.text) >= longW && /[.!?。！？]/.test(b.text)){ b.keep_why = 'long_block:' + b.why; b.why = null; if (!res.flags.includes('long_block')) res.flags.push('long_block'); }
    const keptText = blocks.filter(b => !b.why && !b.hdr).map(b => b.text).join(' ');
    if (res.gabriel_before && G.test(bodyText) && !G.test(keptText)){
      res.flags.push('gabriel_outside_article');
      res.gabriel_outside = blocks.filter(b => b.why && G.test(b.text)).map(b => ({ rule: b.why, text: b.text.slice(0, 300) }));
      if (mode === 'library') blocks.forEach(b => { if (b.why && G.test(b.text)){ b.keep_why = 'gabriel:' + b.why; b.why = null; } });
    }
    if (!res.gabriel_before) res.flags.push('no_gabriel');
    const hdrRemove = [];
    for (const b of blocks) if (b.hdr){
      const [act, det] = headerDecision(b, opt.sheet, rules.outlet_aliases);
      if (act === 'remove'){ hdrRemove.push(b); res.header.removed.push(b.text); }
      else { res.header.kept.push(b.text); if (act === 'fill') res.header.fills.push(det); else if (act === 'conflict') res.header.conflicts.push(det); }
    }
    const gone = blocks.filter(b => b.why && !b.hdr && b.why !== 'find:outside' && !safe.has(b)).reduce((s, b) => s + nwords(b.text), 0);
    if (res.words_before && gone / res.words_before > maxFrac && !allowBig){
      res.flags.push('big_removal'); res.would_remove = Math.round(gone / res.words_before * 1000) / 1000;
      blocks.forEach(b => { if (b.why && b.why !== 'find:outside' && !safe.has(b)){ b.keep_why = 'big_removal:' + b.why; b.why = null; } }); edits = [];
    }
    // TinyFish-format page chrome (rules.find; agent-retry post-pass folded in): mode find only, never a block naming Gabriel
    if (mode === 'find' && rules.find) findPhase(blocks, rules.find, G, res, String((opt.sheet || {}).Headline || '') || (doc.title || ''));
    let changed = false; const parents = [];
    const keptEls = new Set();
    blocks.forEach(b => { if (!b.why && b.el){ let p = b.el; while (p){ keptEls.add(p); p = p.parentNode; } } });
    let tailMedia = [];
    blocks.forEach(b => { if (b.why && ['tail','cut','section'].includes(b.why.split(':')[0]) && b.el && !['body','html','main','article'].includes(tag(b.el)) && !keptEls.has(b.el))
      tailMedia = tailMedia.concat(Array.from(b.el.querySelectorAll(MEDIA_TAGS.join(',')))); });
    for (const b of blocks) if (b.why){
      res.removed.push({ rule: b.why, text: b.text.slice(0, 300) });
      const keepMedia = b.why.startsWith('kill:');
      for (const n of b.nodes){
        if (!n.parentNode) continue;
        if (keepMedia && isEl(n) && (MEDIA_TAGS.includes(tag(n)) || n.querySelector(MEDIA_TAGS.join(',')))){
          if (!MEDIA_TAGS.includes(tag(n))){ const w = doc.createTreeWalker(n, 4); const ts = []; while (w.nextNode()) ts.push(w.currentNode); ts.forEach(t => t.remove()); }
          continue;
        }
        parents.push(n.parentNode); n.remove();
      }
      changed = true;
    }
    for (const e of tailMedia) if (e.parentNode){ parents.push(e.parentNode); e.remove(); changed = true; }
    for (const b of hdrRemove){ b.nodes.forEach(n => { if (n.parentNode){ parents.push(n.parentNode); n.remove(); } }); changed = true; }
    const imgs = new Map(m.img.map(([k, src]) => [k, src]));
    if (imgs.size) for (const im of Array.from(body.querySelectorAll('img'))){
      const k = imgKey(im.getAttribute('src') || '');
      if (imgs.has(k) && im.parentNode){ res.removed.push({ rule: 'img:' + imgs.get(k), text: '[img ' + k + ']' }); parents.push(im.parentNode); im.remove(); changed = true; }
    }
    for (const [b, p, src] of edits){ if (b.why) continue; const before = b.text; if (stripBlock(b, p)){ res.stripped.push({ rule: 'strip:' + src, pattern: p, text: before.slice(0, 300) }); changed = true; } }
    if (mode === 'find' && rules.find && rules.find.tidy && tidyEmpty(body)) changed = true;
    if (changed){ pruneEmpty(parents, doc); res.html = serialize(doc, html); res.status = 'cleaned'; }
    else { res.html = String(html || ''); res.status = res.flags.includes('big_removal') ? 'flagged' : 'unchanged'; }
    const after = changed ? extractBlocks(new DOMParser().parseFromString(res.html, 'text/html').body) : blocks;
    res.words_after = nwords(after.filter(b => !(changed ? HDR_SAVED.test(b.text) : b.hdr)).map(b => b.text).join(' '));
    res.gabriel_after = G.test(after.map(b => b.text).join(' '));
    return res;
  }
  const STUB = /subscribe to (continue|read)|already a subscriber|sign in to (continue|read)|create a free account to|verify you are human|access denied|just a moment|enable javascript and cookies|page not found|404 not found|this page (isn't|is not) available|you have reached your (free )?(article|story) limit|subscriber\? click here to log ?in|log ?in\/register your account/i;
  /* verdict for a find: ok | skip (Gabriel only outside the article) | error (not the article / no body / no Gabriel / stub) */
  /* AUTO-v1: the stub test comes first; paywall / login / bot-wall reasons are BLOCKED (BLOCKED_REASONS), others RETRY */
  const STUB_PAY = /subscribe to (continue|read)|already a subscriber|sign in to (continue|read)|create a free account to|you have reached your (free )?(article|story) limit|subscriber\? click here to log ?in|log ?in\/register your account/i;
  const STUB_BOT = /verify you are human|access denied|just a moment|enable javascript and cookies/i;
  const BLOCKED_REASONS = ['paywall or login page', 'blocked by the site (bot check or access denied)'];
  function pageCheck(res){
    if (res.flags.includes('gabriel_outside_article')) return ['skip', 'Gabriel is named only outside the article (comments, teasers or tags)'];
    const t = norm(extractBlocks(new DOMParser().parseFromString(res.html, 'text/html').body).map(b => b.text).join(' '));
    if (nwords(t) < 250 && STUB.test(t)) return ['error', STUB_PAY.test(t) ? BLOCKED_REASONS[0] : STUB_BOT.test(t) ? BLOCKED_REASONS[1] : 'error page (not found)'];
    if (!res.gabriel_before) return ['error', 'no Gabriel on the page (not the article)'];
    if ((res.words_after || 0) < 60) return ['error', 'no article body (under 60 words)'];
    return ['ok', ''];
  }
  /* AUTO-v1: Jesse Gabriel only (other Gabriels: Ugarte, Petek, San Gabriel … -> 'other'); listing pages never added */
  function jesseCheck(text, rules){
    rules = rules || {}; const t = String(text || '');
    if (rules.jesse && search(rules.jesse, t)){   // search() resets the 'g' regex's lastIndex
      // INCL-v1: another Jesse/Jessie Gabriel (BakerHostetler lawyer) unless a title/context that is his is present
      if (rules.other_jesse && search(rules.other_jesse, t) && !(rules.jesse_strong && search(rules.jesse_strong, t))) return 'other';
      return 'jesse';
    }
    const G = new RegExp(rules.gabriel || GAB_DEFAULT), other = !!(rules.other_gabriel && search(rules.other_gabriel, t));
    if (G.test(t)){ if (!other && rules.jesse_context && search(rules.jesse_context, t)) return 'jesse'; return other ? 'other' : 'unclear'; }
    return other ? 'other' : 'none';
  }
  function skipUrl(url, rules){ const u = String(url || '').trim(); return ((rules || {}).skip_urls || []).find(p => search(p, u)) || null; }
  /* the text of a cleaned page, as tfStrip() gives it (for the Update button's checks) */
  function blocksText(html){ return extractBlocks(new DOMParser().parseFromString(String(html || ''), 'text/html').body).map(b => b.text).join('\n'); }
  return { cleanPage, pageCheck, blocksText, jesseCheck, skipUrl, BLOCKED_REASONS, extractBlocks, decide, merged, siteRules, nwords, norm, imgKey, sha12 };
})();
/* CLEAN_HTML_JS end */
