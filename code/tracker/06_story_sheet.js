/* ---------- story sheet ---------- */
async function openViewer(id, order){ S._hits = [];
  const r = byId.get(id); if (!r) return;
  S.openId = id; if (order) S._sheetOrder = order;
  // a clip clicked from a list always opens in the side panel; next/prev keeps the current view
  if (order || $('#sheet').hidden) $('#sheet').classList.remove('wide');
  document.querySelectorAll('#tbody tr').forEach(tr => tr.classList.toggle('on', tr.dataset.id===id));
  const host = u => { try { return new URL(u).hostname.replace(/^www\./,''); } catch(e){ return ''; } };
  const links = linksOf(r).map(linkA);  // LINKS-v1
  const ord = S._sheetOrder || [], i = ord.indexOf(id);
  const sheet = $('#sheet');
  sheet.innerHTML = `
    <div class="sheet-top">
      <span class="pos">${i>=0 ? `${fmt(i+1)} of ${fmt(ord.length)}` : ''}</span>
      <button class="iconbtn" data-wide aria-pressed="${sheet.classList.contains('wide')}" aria-label="Full-page view" title="${sheet.classList.contains('wide') ? 'Back to the side panel' : 'Full-page view: details on the left, the article on the right'}">${sheet.classList.contains('wide') ? IC.shrink : IC.exp}</button>
      <button class="iconbtn" data-nav="-1" aria-label="Previous story" title="Previous (←)" ${i<=0?'disabled':''}>${IC.l}</button>
      <button class="iconbtn" data-nav="1" aria-label="Next story" title="Next (→)" ${i<0||i>=ord.length-1?'disabled':''}>${IC.r}</button>
      <button class="iconbtn" data-close aria-label="Close" title="Close (Esc)">${IC.x}</button>
    </div>
    <div class="sheet-meta">
      <div class="kick"><span>${dateLabel(r)}</span><span>${r.pub ? `<button class="linkbtn kick-out" data-pub="${esc(r.pub)}" title="See every clip from ${esc(r.pub)}">${esc(r.outlet)}</button>` : esc(r.outlet)}</span></div>
      <h2>${esc(r.hl)}</h2>
      ${r.hl_en ? `<div class="hl-en sh-hl-en">${esc(r.hl_en)}</div>` : ''}
      ${r.lang ? '<div class="trbox" id="trbox"></div>' : ''}
      ${links.length ? `<div class="dlinks">${links.join('')}<button class="linkbtn" data-editstory>Edit details</button></div>` : '<div class="note">No direct link on file for this story yet. <button class="linkbtn" data-editstory>Edit details</button></div>'}
      <div class="factline">${[fl('topic', r.topic), r.bills.length ? r.bills.map(b => `<button class="linkbtn" data-bill="${esc(b)}" title="${esc(billName(b) ? b+': '+billName(b)+'. ' : '')}See every clip on ${esc(b)}">${esc(b)}</button>`).join(', ') : '', reachTags(r).map(v => fl('reach', v)).join(' · '), fl('media', r.media), r.authors.length ? `By ${r.authors.map(a => `<button class="linkbtn" data-author="${esc(a)}" title="See every clip by ${esc(a)}">${esc(a)}</button>`).join(', ')}${r.atitle ? ` <span class="atitle">(${esc(r.atitle)})</span>` : ''}` : '', r.pick ? pl(r.pick,'reprint') : 'No reprints'].filter(x => String(x).trim()).map(x => `<span>${x}</span>`).join('')}</div>
      ${r.role!=='Mentioned in story' || r.depth==='List-only' || r.quoted==='Yes' || hasHtml(r.id) || r.lang || NOTES.has(r.id) || rated(r) || relsOf(r.id).length ? `<div class="sh-badges">${badges(r, true)}</div>` : ''}
      ${alsoNames(r).length||alsoMissing(r)?`<div class="also"><b class="t-strong">Reprinted in:</b> ${alsoNames(r).map(n => `<button class="linkbtn" data-ranin="${esc(bareName(n))}" title="See every clip that ran in ${esc(bareName(n))}">${esc(n)}</button>`).join('; ')}${alsoMissing(r)?`${alsoNames(r).length?'; ':''}${pl(alsoMissing(r),'other outlet')} not identified`:''}</div>`:''}
      ${repLinks(r)}
      ${insEntry(r)}
      ${relLine(r)}
      <div class="tonebox"><span class="sw" style="background:${colorFor('tone',r.tone)}"></span><span>${rated(r) ? `<b>Tone: ${esc(r.tone)}.</b> ${esc(r.twhy)}${r.tauto?' <span class="note">Rated by Claude from the saved copy.</span>':''}` : (local.has(r.id) ? '<b>Tone: not rated yet.</b> <span class="tone-status"></span>' : '<b>Tone: not rated yet.</b>')}</span><select class="tsel" data-tset aria-label="Change the tone"><option value="">${rated(r) ? 'Change' : 'Set tone'}</option>${TONE_ORDER.slice(0,5).map(t => `<option${t===r.tone?' disabled':''}>${t}</option>`).join('')}</select></div>
      <div class="notebox"><label class="eyebrow" for="tnote">Team note</label><textarea id="tnote" rows="2" placeholder="Anything the team should know.">${esc((NOTES.get(r.id)||{}).text||'')}</textarea><span class="note" id="tnoteMeta">${NOTES.has(r.id) ? `Last edited ${esc(NOTES.get(r.id).at||'')}` : 'Notes are shared with everyone who opens the tracker.'}</span></div>
    </div>
    <div class="doc" id="doc"></div>`;
  sheet.hidden = false; $('#scrim').hidden = false;
  if (r.lang) drawTr(id);
  if (!sheet.contains(document.activeElement)){ sheet.tabIndex = -1; sheet.style.outline = 'none'; sheet.focus({preventScroll:true}); }
  const html = viewFix(safeImgs(await fillImgs(await getHtml(id))), r);   // PHOTOS-v2: no remote or missing photo reaches the viewer
  if (S.openId !== id) return;
  const doc = $('#doc');
  const pdf = pdfOf(html), dl = sheet.querySelector('.dlinks');
  if (pdf && pdf.url && dl) dl.insertAdjacentHTML('afterbegin', `<span class="lkw">${cpBtn(pdf.url)}<a href="${esc(pdf.url)}" target="_blank" rel="noopener"><b>${pdf.text ? 'ProQuest PDF' : 'Full print edition (PDF)'} ↗</b><span>${pdf.pages ? pl(pdf.pages, 'page') : 'PDF'}</span></a></span>`);
  if (html){
    const f = document.createElement('iframe');
    f.setAttribute('sandbox','allow-same-origin allow-popups allow-popups-to-escape-sandbox');
    f.title = 'Saved copy: ' + r.hl;
    f.srcdoc = '<base target="_blank"><meta name="referrer" content="no-referrer"><style>@import url("https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@600;700&family=Public+Sans:ital,wght@0,400;0,600;1,400&display=swap");html{background:#fff}body{font:var(--fs-h3)/1.65 "Public Sans",system-ui,sans-serif;color:#1b1f24;max-width:680px;margin:28px auto;padding:0 22px}img,video,iframe{max-width:100%;height:auto}figure{margin:18px 0}mark.jg-hit{background:#ffe9a6;color:inherit;border-radius:2px;padding:0 1px}mark.jg-hit.cur{background:#ffb400;box-shadow:0 0 0 2px #132a4a}img:not([src]),img[src=""]{display:none}figcaption{font:var(--fs-md)/1.4 "Public Sans",system-ui,sans-serif;color:#5b6570}h1,h2,h3{font-family:"Roboto Slab",Georgia,serif;font-weight:700;color:#132a4a}h1{font-size:var(--fs-stat);line-height:1.2}a{color:#1f5f99}.src{font:var(--fs-sm)/1.5 "Public Sans",system-ui,sans-serif;color:#5b6570;border-bottom:1px solid #e3e7eb;padding-bottom:10px;margin-bottom:14px}' + PDF_CSS + '</style>' + html.replace(/<\/?a\b[^>]*>|<area\b[^>]*>/gi, '');  // no hyperlinks in saved copies, including ones added in this browser
    const meta = sheet.querySelector('.sheet-meta');
    if (meta && matchMedia('(max-width: 640px)').matches){
      meta.classList.add('fold');
      const t = document.createElement('button'); t.type = 'button'; t.className = 'linkbtn meta-tog'; t.textContent = 'Show details ▾';
      t.onclick = () => { const f = meta.classList.toggle('fold'); t.textContent = f ? 'Show details ▾' : 'Hide details ▴'; };
      meta.querySelector('h2').after(t);
    }
    const bar = document.createElement('div'); bar.className = 'finder'; bar.id = 'finder';
    bar.innerHTML = `<span class="fl"><span class="sw"></span><span class="long">Highlighting mentions of </span><b>Gabriel</b></span><span class="fc" id="fcount">Searching…</span><button class="iconbtn" data-hit="-1" aria-label="Previous mention" title="Previous mention (Shift+Enter)" disabled>${IC.l}</button><button class="iconbtn" data-hit="1" aria-label="Next mention" title="Next mention (Enter)" disabled>${IC.r}</button>`;
    bar.onmousedown = e => e.preventDefault();
    bar.onclick = e => { const b = e.target.closest('[data-hit]'); if (b) stepHit(+b.dataset.hit); };
    doc.appendChild(bar);
    // the English translation sits right under the highlighting bar, above the saved page
    const tb = $('#trbox'); if (tb){ tb.classList.add('in-doc'); doc.appendChild(tb); }
    f.onload = () => { hideBroken(f); markHits(f); };
    doc.appendChild(f);
  } else {
    doc.innerHTML = `<div class="ph"><div class="ph-paper">
      <div class="lbl">Saved copy not added yet</div>
      <h3>${esc(r.hl)}</h3>
      <div class="by">${esc(r.pub)} · ${dateLabel(r)}</div>
      ${[96,100,88,100,72,0,100,94,60].map(w=> w? `<div class="bar" style="width:${w}%"></div>` : '<div style="height:10px"></div>').join('')}
      <div class="ph-note">The full ${r.av && r.av.type !== 'Web story' ? 'transcript' : 'article'} will show here once its saved page is added. Until then, use the links above to ${r.av && r.av.type !== 'Web story' ? 'watch or listen at the source' : 'read it at the source'}.</div>
    </div></div>`;
  }
}
/* PHOTOS-v2 (agent-v20-photos 2026-10-28): the viewer's srcdoc iframe inherits the page CSP (img-src self/data/blob), so a
   remote photo can never load. Copies are built with their photos embedded (make_copies --img-cache) and unloadable ones
   dropped; this is the viewer-side backstop for older copies and pages added in this browser: every <img> whose src is not
   data:/blob:/a published local file (pdf/…, img/…) is removed with the wrapper it leaves empty (captions stay), remote
   srcset/<source> are stripped, and an embedded photo that still fails to decode is hidden the same way after load. */
const IMG_OK = /^(?:data:image\/|blob:|(?:pdf|img)\/[^:]+$)/i;
function pruneEmpty(el, stop){
  while (el && el !== stop && el.parentNode && !(el.textContent || '').trim() && !el.querySelector('img,video,iframe,svg,picture,canvas,audio,table')){
    const p = el.parentNode; p.removeChild(el); el = p;
  }
}
function dropImg(img, stop){ const p = img.parentNode; if (!p) return; p.removeChild(img); pruneEmpty(p, stop); }
function safeImgs(html){
  if (!html || !/<img\b|<source\b/i.test(html)) return html;
  let d; try { d = new DOMParser().parseFromString(html, 'text/html'); } catch(e){ return html; }
  let n = 0;
  d.querySelectorAll('source').forEach(s => { if (s.hasAttribute('srcset') || s.hasAttribute('src')){ const p = s.parentNode; s.remove(); n++; if (p) pruneEmpty(p, d.body); } });
  d.querySelectorAll('img').forEach(img => {
    ['srcset','sizes','data-srcset','data-src','loading'].forEach(a => { if (img.hasAttribute(a)){ img.removeAttribute(a); n++; } });
    const src = (img.getAttribute('src') || '').trim();
    if (!IMG_OK.test(src)){ dropImg(img, d.body); n++; }
  });
  if (!n) return html;
  const head = d.head ? d.head.innerHTML : '';
  return `<html><head>${head}</head><body>${d.body ? d.body.innerHTML : ''}</body></html>`;
}
function hideBroken(f){
  const d = f.contentDocument; if (!d || !d.body) return;
  d.querySelectorAll('img').forEach(img => {
    const gone = () => dropImg(img, d.body);
    if (img.complete){ if (!img.naturalWidth) gone(); } else img.addEventListener('error', gone, { once: true });
  });
}
/* PDF clippings (pdfpage.py, or added in this browser): each page is an image with its words laid over it, invisible
   but selectable, so search, highlighting and Claude's reading all use the PDF's own text */
const PDF_CSS = 'body:has(.jg-pdf){max-width:1040px;margin:16px auto;padding:0 14px;background:#eef1f4}html:has(.jg-pdf){background:#eef1f4}.pdf-cap{font:var(--fs-md)/1.4 "Public Sans",system-ui,sans-serif;color:#5b6570;margin:0 0 10px}.jg-pdf .pg{position:relative;container-type:inline-size;margin:0 0 16px;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.18)}.jg-pdf .pg img{display:block;width:100%;height:auto}.jg-pdf .tl{position:absolute;inset:0}.jg-pdf .tl span{position:absolute;color:transparent;white-space:pre;line-height:1;overflow:hidden}.jg-pdf .tl span::selection,.jg-pdf .tl span ::selection{background:rgba(31,95,153,.3)}.jg-pdf mark.jg-hit{background:transparent;color:transparent;padding:0;box-shadow:none}.jg-pdf .tl span:has(mark.jg-hit){background:rgba(255,200,0,.42);border-radius:2px}.jg-pdf .tl span:has(mark.cur){background:rgba(255,150,0,.55);box-shadow:0 0 0 2px #132a4a}';
/* a PDF added in this browser gets the same layout, built with PDF.js: the pages that name Gabriel as images, words on top */
const PDFJS = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/';
let pdfLib = null;
function loadPdfJs(){
  return pdfLib || (pdfLib = new Promise((res, rej) => { const sc = document.createElement('script'); sc.src = PDFJS + 'pdf.min.js';
    sc.onload = () => { const L = window.pdfjsLib; if (!L) return rej(new Error('PDF.js did not load')); L.GlobalWorkerOptions.workerSrc = PDFJS + 'pdf.worker.min.js'; res(L); };
    sc.onerror = () => { pdfLib = null; rej(new Error('PDF.js did not load')); }; document.head.appendChild(sc); }));
}
async function pdfFileToHtml(file, r){
  const L = await loadPdfJs(), pdf = await L.getDocument({ data: new Uint8Array(await file.arrayBuffer()) }).promise, pages = [];
  for (let p = 1; p <= pdf.numPages; p++){
    const pg = await pdf.getPage(p), vp = pg.getViewport({ scale: 1 }), tc = await pg.getTextContent(), words = [];
    tc.items.forEach(it => { if (!it.str || !it.str.trim()) return;
      const [a, b, c, d, e, f] = it.transform, fh = Math.hypot(c, d) || Math.hypot(a, b) || it.height || 10, len = it.str.length, [x, y] = vp.convertToViewportPoint(e, f);
      // each text run is split into words, placed by their share of the run's width
      it.str.replace(/\S+/g, (wd, off) => { words.push({ x: x + it.width * off / len, y: y - fh * 0.85, w: it.width * wd.length / len, h: fh, t: wd }); return wd; });
      if (it.hasEOL) words.push(null); });
    pages.push({ p, pg, W: vp.width, H: vp.height, words });
  }
  const named = pages.filter(x => x.words.some(w => w && /Gabriel/.test(w.t)));
  const show = (named.length ? named : pages.slice(0, 4)).slice(0, 8), secs = [];
  for (const x of show){
    const vp = x.pg.getViewport({ scale: 2 }), cv = document.createElement('canvas'); cv.width = vp.width; cv.height = vp.height;
    await x.pg.render({ canvasContext: cv.getContext('2d'), viewport: vp }).promise;
    const P = (v, t) => (v / t * 100).toFixed(3) + '%';
    const tl = x.words.map(w => w ? `<span style="left:${P(w.x, x.W)};top:${P(w.y, x.H)};width:${P(w.w, x.W)};height:${P(w.h, x.H)};font-size:${(w.h / x.W * 85).toFixed(3)}cqw">${esc(w.t)}</span>` : '\n').join(' ');
    secs.push(`<section class="pg" data-page="${x.p}" style="aspect-ratio:${Math.round(x.W)}/${Math.round(x.H)}"><img src="${cv.toDataURL('image/jpeg', 0.72)}" alt="Page ${x.p}"><div class="tl">${tl}</div></section>`);
  }
  const which = show.map(x => x.p).join(', ');
  return `<html><head><title>${esc(r.hl)}</title><meta name="jg-pdf" content="" data-pages="${pdf.numPages}" data-shown="${which}"></head><body><div class="jg-pdf"><p class="pdf-cap">Print edition: page${show.length > 1 ? 's' : ''} ${which} of ${pdf.numPages}${named.length ? '' : ' (Gabriel isn’t named in the text layer, so the first pages are shown)'}</p>${secs.join('')}</div></body></html>`;
}
const pdfOf = html => { const m = /<meta name="jg-pdf" content="([^"]*)"(?: data-pages="(\d+)")?(?: data-shown="([^"]*)")?/.exec(html || ''); return m ? { url: m[1], pages: +m[2] || 0, text: m[3] === 'text' } : null; };
/* highlight Gabriel in a saved copy and step through the hits like find-in-page */
const HIT_RX = /\b(?:Jesse\s+)?Gabriel\b/gi;
function markHits(f){
  const d = f.contentDocument; if (!d || !d.body) return;
  const walk = d.createTreeWalker(d.body, NodeFilter.SHOW_TEXT, { acceptNode: n => /^(SCRIPT|STYLE|NOSCRIPT|TEXTAREA|TITLE)$/.test(n.parentNode.nodeName) || !/\bGabriel\b/i.test(n.nodeValue) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT });
  const nodes = []; while (walk.nextNode()) nodes.push(walk.currentNode);
  nodes.forEach(n => {
    const frag = d.createDocumentFragment(), t = n.nodeValue; let last = 0;
    t.replace(HIT_RX, (m, off) => { frag.append(t.slice(last, off)); const k = d.createElement('mark'); k.className = 'jg-hit'; k.textContent = m; frag.append(k); last = off + m.length; return m; });
    frag.append(t.slice(last)); n.replaceWith(frag);
  });
  S._hits = [...d.querySelectorAll('mark.jg-hit')].filter(m => m.getClientRects().length); S._hit = -1;
  d.addEventListener('keydown', hitKeys);
  const c = $('#fcount'); if (!c) return;
  c.textContent = S._hits.length ? pl(S._hits.length, 'mention') : 'No mentions found';
  document.querySelectorAll('#finder [data-hit]').forEach(b => b.disabled = !S._hits.length);
}
function stepHit(step){
  const h = S._hits || []; if (!h.length) return;
  if (S._hit >= 0) h[S._hit].classList.remove('cur');
  S._hit = S._hit < 0 ? (step > 0 ? 0 : h.length-1) : (S._hit + step + h.length) % h.length;
  const m = h[S._hit]; m.classList.add('cur'); m.scrollIntoView({block:'center', behavior:'smooth'});
  $('#fcount').textContent = `${fmt(S._hit+1)} of ${fmt(h.length)}`;
}
function hitKeys(e){ if (e.key==='Enter' && (S._hits||[]).length){ e.preventDefault(); stepHit(e.shiftKey ? -1 : 1); } else if (e.key==='Escape') closeViewer(); }
function closeViewer(){ S._hits = []; S.openId = null; $('#sheet').hidden = true; if (!$('#rail').classList.contains('open')) $('#scrim').hidden = true; document.querySelectorAll('#tbody tr.on').forEach(t=>t.classList.remove('on')); }
function navViewer(step){
  const ord = S._sheetOrder || []; let i = ord.indexOf(S.openId);
  if (i < 0) return; i = Math.min(ord.length-1, Math.max(0, i+step));
  if (S.tab==='db'){ const p = Math.floor(i / S.per); if (p !== S.page){ S.page = p; renderTable(filtered()); } }
  openViewer(ord[i]);
}


/* de9c2baa backstop + INCL-v1 chip / toggle styles */
try { document.head.insertAdjacentHTML('beforeend', '<style>.factline>span:empty{display:none}.badge.listonly{background:var(--panel-2);color:var(--ink-2);border:1px solid var(--line)}table.db{border-collapse:separate!important;border-spacing:0!important}.lo-toggle{display:flex;gap:6px;align-items:center;font-size:var(--fs-md);color:var(--ink-2);padding:8px 0}.lo-toggle .muted{color:var(--ink-3)}</style>'); } catch(e){}
