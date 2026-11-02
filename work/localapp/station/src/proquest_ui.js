/* PROQUESTPDF-v1: the "Add ProQuest PDFs" card. A fragment of station.js (build_station.py puts it where station.js has the PQ_UI marker), right after
   the NewsBank card's fragment, so it shares $, esc, S, sha256Hex, fmtN and the NewsBank card's helpers (nbLoadLibs, nbReadPages, nbStoryPdf, NBS caps)
   with it. One ProQuest article per PDF, many PDFs at once. Everything runs in the browser: pdf.js reads the text, pqparse.js reads the details block,
   the tracker's own functions (src/newsbank.js nbRun + src/proquest.js) check, rate and propose rows. The PDFs are held in this tab only. */
const PQS = S.pq = { items: [], files: [], shas: new Map(), pdfs: new Map(), added: new Set(), busy: false, reading: false, lastRun: null, lastItems: null };
function pqUiErr(msg) { const e = $('#pqMsg'); e.textContent = msg || ''; e.hidden = !msg; }

async function pqReadFile(file) {
  const rec = { name: file.name, bytes: file.size, status: 'reading', note: '' };
  PQS.files.push(rec); pqDrawFiles();
  const say = t => { rec.note = t; pqDrawFiles(); };
  try {
    if (file.size > NB_FILE_CAP) throw new Error('the file is over ' + (NB_FILE_CAP >> 20) + ' MB');
    const bytes = new Uint8Array(await file.arrayBuffer());
    if (String.fromCharCode.apply(null, bytes.subarray(0, 5)) !== '%PDF-') throw new Error('not a PDF file');
    const sha = await sha256Hex(bytes); rec.sha = sha;
    if (PQS.shas.has(sha)) { rec.status = 'same'; rec.note = 'identical to “' + PQS.shas.get(sha) + '”, already added: skipped'; return; }
    PQS.shas.set(sha, file.name);
    await nbLoadLibs();
    say('reading the text');
    let pages;
    try { pages = await nbReadPages(bytes, say); }
    catch (e) { throw new Error(/password/i.test(String(e && (e.name + ' ' + e.message))) ? 'the PDF is password-protected' : 'the PDF could not be opened (' + (e && e.message ? e.message : e) + ')'); }
    const p = PQParse.parsePdf(pages);
    rec.pages = pages.length;
    const key = sha.slice(0, 8) + '#1';
    const it = { key, p, batch: { name: file.name, sha256: sha, index: 1, firstPage: 1, lastPage: pages.length }, include: false, pdf: null, fileId: '' };
    if (p.status !== 'ok') {
      it.screen = { status: p.status === 'not_proquest' ? 'refused' : 'needs_look', why: p.problems.join(' ') };
    } else {
      it.screen = window.__pq.screen(p);
      it.include = it.screen.status === 'new' || it.screen.status === 'reprint';
      if (it.include) {
        window.__pq.remember(p, key);
        try {
          const src = await PDFLib.PDFDocument.load(bytes, { updateMetadata: false });
          const pdfBytes = await nbStoryPdf(src, { firstPage: 1, lastPage: pages.length, bands: [] }, { title: p.headline, docref: p.docid, source: file.name, label: 'ProQuest' });
          if (pdfBytes.length > NB_STORY_PDF_CAP) { it.screen.why += ' (its PDF is over ' + (NB_STORY_PDF_CAP >> 20) + ' MB: the text copy is saved, the PDF itself is not)'; }
          else {
            it.fileId = 'pq-' + (await sha256Hex(new TextEncoder().encode(p.docref_key || (p.headline + '|' + p.date + '|' + p.outlet_clean)))).slice(0, 16);
            it.pdf = { bytes: pdfBytes.length, sha256: await sha256Hex(pdfBytes) }; PQS.pdfs.set(it.fileId, { bytes: pdfBytes, sha256: it.pdf.sha256 });
          }
        } catch (e) { it.screen.why += ' (its PDF could not be copied: ' + (e && e.message ? e.message : e) + '; the text copy is saved without it)'; it.pdfError = String(e && e.message || e); }
      }
    }
    PQS.items.push(it);
    rec.status = 'ok'; rec.stories = 1;
    rec.note = p.status === 'ok' ? pages.length + ' page' + (pages.length === 1 ? '' : 's') + ': ' + (p.headline || '').slice(0, 80) : pages.length + ' page' + (pages.length === 1 ? '' : 's') + ': ' + (it.screen.status === 'refused' ? 'not a ProQuest article PDF' : 'needs a look');
  } catch (e) {
    rec.status = 'error'; rec.note = 'could not be read: ' + (e && e.message ? e.message : e);
    if (rec.sha && PQS.shas.get(rec.sha) === file.name) PQS.shas.delete(rec.sha);
  }
}
let pqQueue = Promise.resolve();
function pqAddFiles(files) {
  const list = [...files].filter(f => f);
  if (!list.length) return;
  pqUiErr('');
  if (!S.loaded) { pqUiErr('Load the “for Update” file in step 1 first: stories are checked against it.'); return; }
  pqQueue = pqQueue.then(async () => {
    PQS.reading = true; pqDrawAll();
    for (const f of list) { await pqReadFile(f); pqDrawAll(); }
    PQS.reading = false; pqDrawAll();
  });
}

const PQ_LABEL = Object.assign({}, NB_LABEL, { needs_look: 'Needs a look', refused: 'Not a ProQuest article PDF' });
function pqDrawFiles() {
  $('#pqFiles').innerHTML = PQS.files.map(f => '<li class="nb-file nb-' + f.status + '"><b>' + esc(f.name) + '</b> ' + esc(f.status === 'reading' ? 'reading… ' + f.note : f.note) + '</li>').join('');
}
function pqDrawAll() {
  pqDrawFiles();
  const items = PQS.items, c = {};
  items.forEach(it => { const k = PQS.added.has(it.key) ? 'added' : it.screen.status; c[k] = (c[k] || 0) + 1; });
  $('#pqTbl').hidden = !items.length;
  const pick = items.filter(it => (it.screen.status === 'new' || it.screen.status === 'reprint') && !PQS.added.has(it.key) && it.include);
  const rank = it => PQS.added.has(it.key) ? 4 : { new: 0, reprint: 0, needs_look: 1, refused: 1, known: 2, dup_batch: 2 }[it.screen.status] ?? 2;
  const rows = items.slice().sort((a, b) => rank(a) - rank(b));
  $('#pqBody').innerHTML = rows.slice(0, 600).map(it => {
    const st = PQS.added.has(it.key) ? (PQS.lastItems && PQS.lastItems[it.key] || { status: 'added' }).status : it.screen.status, p = it.p, can = (it.screen.status === 'new' || it.screen.status === 'reprint') && !PQS.added.has(it.key);
    const note = (PQS.lastItems && PQS.lastItems[it.key] && PQS.lastItems[it.key].why) || it.screen.why, flags = (p.flags || []).length ? ' <span class="nb-flag" title="' + esc(p.flags.join('; ')) + '">check</span>' : '';
    const lk = PQS.lastItems && PQS.lastItems[it.key] && PQS.lastItems[it.key].link ? ' · <a href="' + esc(PQS.lastItems[it.key].link) + '" target="_blank" rel="noopener noreferrer">own page</a>' : '';
    return '<tr class="nb-r nb-' + esc(st) + '"><td>' + (can ? '<input type="checkbox" data-pqk="' + esc(it.key) + '"' + (it.include ? ' checked' : '') + ' aria-label="Include">' : '') + '</td><td>' + esc(PQ_LABEL[st] || st) + (it.screen.of ? ' <small>' + esc(it.screen.of) + '</small>' : '') + '</td><td>' + esc(p.date || '') + '</td><td>' + esc(p.outlet_clean || '') + '</td><td>' + esc(p.headline || '(' + it.batch.name + ')') + flags + lk + '</td><td class="nb-note">' + esc(note || '') + '</td></tr>';
  }).join('');
  const parts = [];
  if (c.new) parts.push(fmtN(c.new) + ' new'); if (c.reprint) parts.push(fmtN(c.reprint) + ' reprint' + (c.reprint === 1 ? '' : 's')); if (c.known) parts.push(fmtN(c.known) + ' already in the tracker');
  if (c.dup_batch) parts.push(fmtN(c.dup_batch) + ' repeated in these PDFs'); if (c.needs_look) parts.push(fmtN(c.needs_look) + ' need' + (c.needs_look === 1 ? 's' : '') + ' a look'); if (c.refused) parts.push(fmtN(c.refused) + ' not ProQuest article PDFs');
  if (c.added) parts.push(fmtN(c.added) + ' added to the update');
  const sm = $('#pqSummary'); sm.hidden = !items.length; sm.textContent = items.length ? fmtN(items.length) + ' PDF' + (items.length === 1 ? '' : 's') + ': ' + parts.join(', ') + '.' : '';
  const add = $('#pqAdd'); add.textContent = pick.length ? 'Add ' + fmtN(pick.length) + (pick.length === 1 ? ' story' : ' stories') + ' to the update' : 'Add to the update';
  add.disabled = !pick.length || PQS.busy || PQS.reading || NBS.busy || trackerBusy();
  $('#pqLinksRow').hidden = !items.length;
}
async function pqAdd() {
  if (PQS.busy || NBS.busy) return;
  const chosen = PQS.items.filter(it => !PQS.added.has(it.key) && (it.screen.status === 'new' || it.screen.status === 'reprint') && it.include);
  if (!chosen.length) return;
  PQS.busy = true; pqDrawAll(); nbDrawAll(); const prog = $('#pqProg'), warn = $('#pqWarn'); prog.hidden = false; warn.hidden = true; warn.innerHTML = '';
  const say = (m, f) => { prog.textContent = m; };
  try {
    const pending = [...NBS.pdfs.values(), ...PQS.pdfs.values()].reduce((a, x) => a + x.bytes.length, 0);
    if (pending > NB_PDF_CAP) throw new Error('The PDFs in this tab add up to ' + fmtN(Math.round(pending / 1048576)) + ' MB, over the ' + (NB_PDF_CAP >> 20) + ' MB one update can hold. Add some now, download the update folder, then reload this page for the rest.');
    let sample = null, mcp = null;
    try { sample = realClaude && realClaude.use ? await realClaude.use('sample') : null; } catch (e) { sample = null; }
    try { mcp = realClaude && realClaude.use ? await realClaude.use('mcp') : null; } catch (e) { mcp = null; }
    const wl = [];
    if (!sample) wl.push('Claude (sampling) is not available here: tone, topic, language and translation could not be filled in. The rows are marked and need checking.');
    const wantLinks = $('#pqLinks').checked;
    if (wantLinks && !mcp) wl.push('The TinyFish connector is not available: the publishers’ own links were not looked up.');
    const res = await window.__pq.run(chosen, { say, links: wantLinks && !!mcp, sample, mcp, mark: (c, id) => { S.noMirror.add(c + '.' + id); } });
    PQS.lastItems = Object.assign(PQS.lastItems || {}, Object.fromEntries(res.items.map(x => [x.key, x])));
    res.items.forEach(x => PQS.added.add(x.key));
    PQS.lastRun = res;
    if (res.errors && res.errors.length) res.errors.forEach(e => wl.push(e));
    const nl = res.links.found;
    prog.textContent = 'Added: ' + fmtN(res.counts.stories) + ' new ' + (res.counts.stories === 1 ? 'story' : 'stories') + ', ' + fmtN(res.counts.reprint_rows) + ' reprint row' + (res.counts.reprint_rows === 1 ? '' : 's') + ' (' + fmtN(res.counts.rows) + ' spreadsheet rows)'
      + (res.links.searched ? '; publisher’s own page found for ' + fmtN(nl) + ' of ' + fmtN(res.links.searched) : '') + (res.counts.left ? '; ' + fmtN(res.counts.left) + ' left out (listed below)' : '') + '. Download the update folder in step 3.';
    res.left.forEach(x => wl.push('Left out: ' + x.hl + ' (' + x.outlet + ', ' + x.date + '): ' + x.why));
    if (!res.saved) wl.push('The run could not be saved in this tab’s store: the rows are in the list but will not be in the update folder.');
    if (wl.length) { warn.innerHTML = wl.map(x => '<li>' + esc(x) + '</li>').join(''); warn.hidden = false; }
  } catch (e) {
    prog.textContent = 'Stopped: ' + (e && e.message ? e.message : e);
  } finally { PQS.busy = false; pqDrawAll(); nbDrawAll(); updatePackUi(); }
}
function pqWire() {
  const inp = $('#pqFile'), drop = $('#pqDrop');
  inp.addEventListener('change', () => { pqAddFiles(inp.files); inp.value = ''; });
  ['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', e => { pqAddFiles(e.dataTransfer && e.dataTransfer.files ? e.dataTransfer.files : []); });
  drop.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); inp.click(); } });
  $('#pqBody').addEventListener('change', e => { const k = e.target && e.target.getAttribute && e.target.getAttribute('data-pqk'); if (!k) return; const it = PQS.items.find(x => x.key === k); if (it) { it.include = e.target.checked; pqDrawAll(); } });
  $('#pqAdd').addEventListener('click', () => { pqAdd(); });
  ['dragover', 'drop'].forEach(ev => window.addEventListener(ev, e => { if (!e.target.closest || !e.target.closest('#pqDrop')) e.preventDefault(); }));
}
