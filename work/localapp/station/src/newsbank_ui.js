/* NEWSBANKPDF-v1: the "Add NewsBank PDFs" card. This is a fragment of station.js (build_station.py puts it where station.js has the marker),
   so it shares $, esc, S, sha256Hex, fmtN, nowIso, toastMsg and realClaude with it. Everything here runs in the browser:
   pdf.js (Apache-2.0) reads each batch PDF's text and positions, nbparse.js finds the stories (each ends with its "Citation (apa Style)" block),
   pdf-lib (MIT) copies a story's pages into a PDF of its own, and the tracker's own functions (src/newsbank.js, run inside the tracker's scope)
   check, classify and propose rows. The PDFs are held in this tab only; nothing is uploaded or stored online. */
const NBS = S.nb = { items: [], files: [], shas: new Map(), pdfs: new Map(), added: new Set(), busy: false, libs: false, bytesPending: 0, lastRun: null, seenWarn: [] };
const NB_PDF_CAP = 180 * 1024 * 1024;       // the PC takes up to 256 MB a zip: stop adding before an update could pass it
const NB_STORY_PDF_CAP = 24 * 1024 * 1024;  // the PC refuses a story PDF over 32 MB
const NB_FILE_CAP = 400 * 1024 * 1024;      // one batch PDF read into memory
const nbText = id => { const el = document.getElementById(id); return el ? el.textContent.replace(/<\\\/script/gi, '<' + '/script') : ''; };
function nbRunScript(id, code) { const s = document.createElement('script'); s.id = id; s.textContent = code; document.head.appendChild(s); }
async function nbLoadLibs() {
  if (NBS.libs) return;
  // pdf.js with its worker in this page (a "fake worker"): the artifact page cannot start a worker from another address, so the worker's code is run
  // here first and pdf.js finds it as globalThis.pdfjsWorker. Order matters: the worker, then the library.
  nbRunScript('vendor-pdfjs-worker-run', nbText('vendor-pdfjs-worker'));
  nbRunScript('vendor-pdfjs-run', nbText('vendor-pdfjs'));
  nbRunScript('vendor-pdflib-run', nbText('vendor-pdflib'));
  if (!window.pdfjsLib || !window.pdfjsWorker || !window.PDFLib) throw new Error('the PDF libraries did not start');
  pdfjsLib.GlobalWorkerOptions.workerSrc = 'data:text/javascript,';    // never used: the worker above is found first
  NBS.libs = true;
}
function nbUiErr(msg) { const e = $('#nbMsg'); e.textContent = msg || ''; e.hidden = !msg; }

/* ---------- reading one batch ---------- */
async function nbReadPages(bytes, say) {
  const doc = await pdfjsLib.getDocument({ data: bytes.slice(), isEvalSupported: false, useSystemFonts: false, verbosity: 0, stopAtErrors: false, enableXfa: false, disableAutoFetch: true, disableStream: true }).promise;
  const pages = [];
  for (let p = 1; p <= doc.numPages; p++) {
    const pg = await doc.getPage(p), tc = await pg.getTextContent(), v = pg.getViewport({ scale: 1 });
    pages.push({ page: p, height: v.height, lines: NBParse.linesFromItems(tc.items) });
    if (p % 5 === 0) { say('page ' + p + ' of ' + doc.numPages); await new Promise(r => setTimeout(r, 0)); }
  }
  await doc.destroy();
  return pages;
}
/* a story's pages as a PDF of its own: exact page range; a page shared with a neighbouring story is cropped to this story's band (and the band is
   written into the file's info so the PC reads only that text); links, actions and annotations are dropped */
async function nbStoryPdf(src, st, meta) {
  const { PDFDocument, PDFName, PDFString } = PDFLib;
  const out = await PDFDocument.create({ updateMetadata: false });
  const idx = []; for (let p = st.firstPage; p <= st.lastPage; p++) idx.push(p - 1);
  // strip BEFORE copying: copyPages brings along every object a page points to, and pdf-lib saves objects nothing points to any more, so a key removed
  // only from the copy would leave its (Launch, JavaScript ...) objects behind in the file. The source is held in memory only and is never saved.
  idx.forEach(i => { const pn = src.getPage(i).node; ['Annots', 'AA', 'Metadata', 'PieceInfo', 'B', 'Thumb'].forEach(k => pn.delete(PDFName.of(k))); });
  const copies = await out.copyPages(src, idx);
  const bands = [];
  copies.forEach((pg, i) => {
    ['Annots', 'AA', 'Metadata', 'PieceInfo', 'B', 'Thumb'].forEach(k => pg.node.delete(PDFName.of(k)));
    const band = st.bands[i], mb = pg.getMediaBox();
    if (band && !band.full) {
      const bottom = Math.max(mb.y, band.bottom), top = Math.min(mb.y + mb.height, band.top);
      if (top - bottom > 20) { pg.setCropBox(mb.x, bottom, mb.width, top - bottom); bands.push({ i, top: Math.round(top * 10) / 10, bottom: Math.round(bottom * 10) / 10 }); }
    }
    out.addPage(pg);
  });
  out.setTitle(meta.title || (meta.label || 'NewsBank') + ' story'); out.setSubject((meta.label || 'NewsBank') + ' ' + (meta.docref || '')); out.setProducer('AJG Update station (pdf-lib 1.17.1)'); out.setCreator('AJG Update station');
  out.setCreationDate(new Date()); out.setModificationDate(new Date());
  const info = out.getInfoDict();
  info.set(PDFName.of('AJGSource'), PDFString.of(String(meta.source || '').slice(0, 200)));
  if (bands.length) info.set(PDFName.of('AJGBands'), PDFString.of(JSON.stringify(bands)));
  return await out.save({ useObjectStreams: false });
}

function nbBatchWarn(r) {
  const w = [];
  if (r.noheader) w.push(r.noheader + ' of its stories have no readable header (details come from the citation).');
  if (r.tail.length) w.push('text after the last citation was left out: ' + r.tail.slice(0, 2).join(' / ').slice(0, 120));
  return w;
}

async function nbReadFile(file) {
  const rec = { name: file.name, bytes: file.size, status: 'reading', note: '', stories: 0 };
  NBS.files.push(rec); nbDrawFiles();
  const say = t => { rec.note = t; nbDrawFiles(); };
  try {
    if (file.size > NB_FILE_CAP) throw new Error('the file is over ' + (NB_FILE_CAP >> 20) + ' MB');
    const bytes = new Uint8Array(await file.arrayBuffer());
    if (String.fromCharCode.apply(null, bytes.subarray(0, 5)) !== '%PDF-') throw new Error('not a PDF file');
    const sha = await sha256Hex(bytes);
    rec.sha = sha;
    if (NBS.shas.has(sha)) { rec.status = 'same'; rec.note = 'identical to “' + NBS.shas.get(sha) + '”, already added: skipped'; return; }
    NBS.shas.set(sha, file.name);
    await nbLoadLibs();
    say('reading the text');
    const pages = await nbReadPages(bytes, say);
    const split = NBParse.splitBatch(pages);
    rec.pages = pages.length;
    if (!split.stories.length) throw new Error('no “Citation (apa Style)” block found: download the batch again with the citation format on APA (training deck, step 4)');
    say('splitting ' + split.stories.length + ' stories');
    const src = await PDFLib.PDFDocument.load(bytes, { updateMetadata: false });
    let noheader = 0;
    for (const st of split.stories) {
      const p = NBParse.parseStory(st);
      if (p.how === 'citation') noheader++;
      const key = sha.slice(0, 8) + '#' + st.index;
      const screen = window.__nb.screen(p);
      const it = { key, p, screen, batch: { name: file.name, sha256: sha, index: st.index, firstPage: st.firstPage, lastPage: st.lastPage, sharedFirst: st.sharedFirst, sharedLast: st.sharedLast, bands: st.bands.filter(b => !b.full).map(b => ({ page: b.page, top: b.top, bottom: b.bottom })) },
        include: screen.status === 'new' || screen.status === 'reprint', pdf: null, fileId: '' };
      if (screen.status === 'print_page') window.__nb.remember(p, key);
      if ((screen.status === 'new' || screen.status === 'reprint')) {
        window.__nb.remember(p, key);
        if (!p.thin) {
          try {
            const pdfBytes = await nbStoryPdf(src, st, { title: p.headline, docref: p.docref, source: file.name + ' #' + st.index });
            if (pdfBytes.length > NB_STORY_PDF_CAP) { screen.why += ' (its PDF is over ' + (NB_STORY_PDF_CAP >> 20) + ' MB: added without a saved copy)'; }
            else { it.fileId = 'nb-' + (await sha256Hex(new TextEncoder().encode(p.docref_key || key))).slice(0, 16); it.pdf = { bytes: pdfBytes.length, sha256: await sha256Hex(pdfBytes) }; NBS.pdfs.set(it.fileId, { bytes: pdfBytes, sha256: it.pdf.sha256 }); NBS.bytesPending += pdfBytes.length; }
          } catch (e) { screen.why += ' (its PDF could not be made: ' + (e && e.message ? e.message : e) + ')'; it.pdfError = String(e && e.message || e); }
        }
      }
      NBS.items.push(it);
      if (st.index % 4 === 0) { say('story ' + st.index + ' of ' + split.stories.length); await new Promise(r => setTimeout(r, 0)); }
    }
    rec.stories = split.stories.length; rec.noheader = noheader; rec.tail = split.tail;
    rec.status = 'ok'; rec.warn = nbBatchWarn({ stories: split.stories, noheader, tail: split.tail });
    rec.note = split.stories.length + ' stories, ' + pages.length + ' pages' + (split.stories.some(s => s.sharedFirst) ? '; some stories start mid-page' : '');
  } catch (e) {
    rec.status = 'error'; rec.note = 'could not be read: ' + (e && e.message ? e.message : e);
    if (rec.sha && NBS.shas.get(rec.sha) === file.name) NBS.shas.delete(rec.sha);
  }
}
let nbQueue = Promise.resolve();
function nbAddFiles(files) {
  const list = [...files].filter(f => f);
  if (!list.length) return;
  nbUiErr('');
  if (!S.loaded) { nbUiErr('Load the for Update file first (step 1): stories are checked against it and the files are named from it.'); return; }
  nbQueue = nbQueue.then(async () => {
    NBS.reading = true; nbDrawAll();
    for (const f of list) { await nbReadFile(f); nbDrawAll(); }
    NBS.reading = false; nbDrawAll();
  });
}

/* ---------- the list on the page ---------- */
const NB_LABEL = { new: 'New', reprint: 'Reprint', known: 'Already in the tracker', dup_batch: 'Twice in these PDFs', print_page: 'Print page', skipped: 'Left out', reprint_in_batch: 'Reprint of another in these PDFs' };
function nbDrawFiles() {
  $('#nbFiles').innerHTML = NBS.files.map(f => '<li class="nb-file nb-' + f.status + '"><b>' + esc(f.name) + '</b> ' + esc(f.status === 'reading' ? 'reading… ' + f.note : f.note)
    + (f.warn && f.warn.length ? '<ul>' + f.warn.map(w => '<li class="nb-w">' + esc(w) + '</li>').join('') + '</ul>' : '') + '</li>').join('');
}
function nbCounts() {
  const c = {}; NBS.items.forEach(it => { const k = NBS.added.has(it.key) ? 'added' : it.screen.status; c[k] = (c[k] || 0) + 1; }); return c;
}
function nbDrawAll() {
  nbDrawFiles();
  const items = NBS.items, c = nbCounts();
  $('#nbTbl').hidden = !items.length;
  const pick = items.filter(it => (it.screen.status === 'new' || it.screen.status === 'reprint') && !NBS.added.has(it.key) && it.include);
  const rows = items.slice().sort((a, b) => (NBS.added.has(a.key) ? 3 : { new: 0, reprint: 0, print_page: 1, known: 2, dup_batch: 2 }[a.screen.status] ?? 2) - (NBS.added.has(b.key) ? 3 : { new: 0, reprint: 0, print_page: 1, known: 2, dup_batch: 2 }[b.screen.status] ?? 2));
  $('#nbBody').innerHTML = rows.slice(0, 600).map(it => {
    const st = NBS.added.has(it.key) ? (NBS.lastItems && NBS.lastItems[it.key] || { status: 'added' }).status : it.screen.status, p = it.p, can = (it.screen.status === 'new' || it.screen.status === 'reprint') && !NBS.added.has(it.key);
    const note = (NBS.lastItems && NBS.lastItems[it.key] && NBS.lastItems[it.key].why) || it.screen.why, flags = (p.flags || []).length ? ' <span class="nb-flag" title="' + esc(p.flags.join('; ')) + '">check</span>' : '';
    const lk = NBS.lastItems && NBS.lastItems[it.key] && NBS.lastItems[it.key].link ? ' · <a href="' + esc(NBS.lastItems[it.key].link) + '" target="_blank" rel="noopener noreferrer">own page</a>' : '';
    return '<tr class="nb-r nb-' + esc(st) + '"><td>' + (can ? '<input type="checkbox" data-nbk="' + esc(it.key) + '"' + (it.include ? ' checked' : '') + ' aria-label="Include">' : '') + '</td><td>' + esc(NB_LABEL[st] || st) + (it.screen.of ? ' <small>' + esc(it.screen.of) + '</small>' : '') + '</td><td>' + esc(p.date || '') + '</td><td>' + esc(p.outlet_clean || '') + '</td><td>' + esc(p.headline || '(no headline read)') + flags + lk + '</td><td class="nb-note">' + esc(note || '') + (it.pdf ? '' : (can ? ' <em>(no saved copy)</em>' : '')) + '</td></tr>';
  }).join('') + (rows.length > 600 ? '<tr><td colspan="6">… and ' + fmtN(rows.length - 600) + ' more (the update includes them all).</td></tr>' : '');
  const parts = [];
  if (c.new) parts.push(fmtN(c.new) + ' new'); if (c.reprint) parts.push(fmtN(c.reprint) + ' reprint' + (c.reprint === 1 ? '' : 's')); if (c.known) parts.push(fmtN(c.known) + ' already in the tracker');
  if (c.dup_batch) parts.push(fmtN(c.dup_batch) + ' repeated in these PDFs'); if (c.print_page) parts.push(fmtN(c.print_page) + ' print page' + (c.print_page === 1 ? '' : 's')); if (c.added) parts.push(fmtN(c.added) + ' added to the update');
  const sm = $('#nbSummary'); sm.hidden = !items.length; sm.textContent = items.length ? fmtN(NBS.files.filter(f => f.status === 'ok').length) + ' PDF' + (NBS.files.filter(f => f.status === 'ok').length === 1 ? '' : 's') + ', ' + fmtN(items.length) + ' stories: ' + parts.join(', ') + '.' : '';
  const add = $('#nbAdd'); add.textContent = pick.length ? 'Add ' + fmtN(pick.length) + (pick.length === 1 ? ' story' : ' stories') + ' to the update' : 'Add to the update';
  add.disabled = !pick.length || NBS.busy || NBS.reading || (S.pq && S.pq.busy) || trackerBusy();
  $('#nbLinksRow').hidden = !items.length;
}
async function nbAdd() {
  if (NBS.busy || (S.pq && S.pq.busy)) return;
  const take = NBS.items.filter(it => !NBS.added.has(it.key) && (it.screen.status === 'new' || it.screen.status === 'reprint' || it.screen.status === 'print_page'));
  const chosen = take.filter(it => it.screen.status === 'print_page' || it.include);
  if (!chosen.some(it => it.screen.status !== 'print_page')) return;
  NBS.busy = true; nbDrawAll(); const prog = $('#nbProg'), warn = $('#nbWarn'); prog.hidden = false; warn.hidden = true; warn.innerHTML = '';
  const say = (m, f) => { prog.textContent = m; };
  try {
    const pending = [...NBS.pdfs.values(), ...(S.pq ? S.pq.pdfs.values() : [])].reduce((a, x) => a + x.bytes.length, 0);
    if (pending > NB_PDF_CAP) throw new Error('The PDFs in this tab add up to ' + fmtN(Math.round(pending / 1048576)) + ' MB, over the ' + (NB_PDF_CAP >> 20) + ' MB one update can hold. Add some now, download the update folder, then reload this page for the rest.');
    let sample = null, mcp = null;
    try { sample = realClaude && realClaude.use ? await claudeForTracker.use('sample') : null; } catch (e) { sample = null; }
    try { mcp = realClaude && realClaude.use ? await realClaude.use('mcp') : null; } catch (e) { mcp = null; }
    const wl = [];
    if (!sample) wl.push('Claude is not available on this page, or you did not allow it: tone, topic, language and translation could not be filled in. The rows are marked and need checking. Allow Claude from the page’s Permissions menu and reload to rate them.');
    const wantLinks = $('#nbLinks').checked;
    if (wantLinks && !mcp) wl.push('TinyFish is not available on this page: the publishers’ own links were not looked up. Connect TinyFish in claude.ai (Settings, Connectors), allow it for this page and reload, or untick the box and add the stories without the links.');
    S.sampleDeniedFlag = false;
    const res = await window.__nb.run(chosen, { say, links: wantLinks && !!mcp, sample, mcp, mark: (c, id) => { S.noMirror.add(c + '.' + id); } });
    NBS.lastItems = Object.assign(NBS.lastItems || {}, Object.fromEntries(res.items.map(x => [x.key, x])));
    res.items.forEach(x => NBS.added.add(x.key));
    chosen.filter(it => it.screen.status === 'print_page').forEach(it => NBS.added.add(it.key));
    NBS.lastRun = res;
    if (sample && S.sampleDeniedFlag) wl.unshift('Claude was not allowed for this page, so tone, topic, language and translation could not be filled in. The rows are marked and need checking. Allow Claude from the page’s Permissions menu and reload to rate them.');
    if (res.errors && res.errors.length) res.errors.forEach(e => wl.push(e));
    const nl = res.links.found;
    prog.textContent = 'Added: ' + fmtN(res.counts.stories) + ' new ' + (res.counts.stories === 1 ? 'story' : 'stories') + ', ' + fmtN(res.counts.reprint_rows) + ' reprint row' + (res.counts.reprint_rows === 1 ? '' : 's') + ' (' + fmtN(res.counts.rows) + ' spreadsheet rows)'
      + (res.links.searched ? '; publisher’s own page found for ' + fmtN(nl) + ' of ' + fmtN(res.links.searched) : '') + (res.counts.left ? '; ' + fmtN(res.counts.left) + ' left out (listed below)' : '') + '. Download the update folder in step 3.';
    res.left.forEach(x => wl.push('Left out: ' + x.hl + ' (' + x.outlet + ', ' + x.date + '): ' + x.why));
    if (!res.saved) wl.push('The run could not be kept in this tab: the rows are in the list but will not be in the update folder.');
    if (wl.length) { warn.innerHTML = wl.map(x => '<li>' + esc(x) + '</li>').join(''); warn.hidden = false; }
  } catch (e) {
    prog.textContent = plainErr(e);
  } finally { NBS.busy = false; nbDrawAll(); updatePackUi(); }
}
function nbWire() {
  const inp = $('#nbFile'), drop = $('#nbDrop');
  inp.addEventListener('change', () => { nbAddFiles(inp.files); inp.value = ''; });
  ['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', e => { nbAddFiles(e.dataTransfer && e.dataTransfer.files ? e.dataTransfer.files : []); });
  drop.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); inp.click(); } });
  $('#nbBody').addEventListener('change', e => { const k = e.target && e.target.getAttribute && e.target.getAttribute('data-nbk'); if (!k) return; const it = NBS.items.find(x => x.key === k); if (it) { it.include = e.target.checked; nbDrawAll(); } });
  $('#nbAdd').addEventListener('click', () => { nbAdd(); });
  ['dragover', 'drop'].forEach(ev => window.addEventListener(ev, e => { if (!e.target.closest || !e.target.closest('#nbDrop')) e.preventDefault(); }));
}
