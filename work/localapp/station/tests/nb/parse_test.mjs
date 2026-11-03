// Unit test of src/nbparse.js on the synthetic batch PDFs, read with the vendored pdf.js (legacy build, node).  node parse_test.mjs PDFDIR
import fs from 'fs'; import path from 'path'; import { createRequire } from 'module'; import { fileURLToPath, pathToFileURL } from 'url';
const here = path.dirname(fileURLToPath(import.meta.url)), station = path.join(here, '..', '..');
const NB = createRequire(import.meta.url)(path.join(station, 'src', 'nbparse.js'));
const pdfjs = await import(pathToFileURL(path.join(station, 'vendor', 'pdf.min.mjs')).href);
pdfjs.GlobalWorkerOptions.workerSrc = pathToFileURL(path.join(station, 'vendor', 'pdf.worker.min.mjs')).href;
const dir = process.argv[2], exp = JSON.parse(fs.readFileSync(path.join(dir, 'expected.json'), 'utf8'));
let fail = 0; const ok = (n, c, x) => { console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -> ' + x)); if (!c) fail++; };

async function readBatch(file) {
  const doc = await pdfjs.getDocument({ data: new Uint8Array(fs.readFileSync(file)), isEvalSupported: false, useSystemFonts: false, verbosity: 0 }).promise;
  const pages = [];
  for (let p = 1; p <= doc.numPages; p++) { const pg = await doc.getPage(p), tc = await pg.getTextContent(), v = pg.getViewport({ scale: 1 }); pages.push({ page: p, height: v.height, lines: NB.linesFromItems(tc.items) }); }
  return pages;
}
for (const name of ['batch_A', 'batch_B', 'batch_19', 'batch_1', 'batch_7']) {
  const pages = await readBatch(path.join(dir, name + '.pdf')), r = NB.splitBatch(pages), e = exp[name];
  ok(name + ': ' + e.n + ' stories found', r.stories.length === e.n, r.stories.length);
  ok(name + ': nothing left after the last citation', r.tail.length === 0, JSON.stringify(r.tail));
  r.stories.forEach((s, i) => {
    const x = e.items[i], p = NB.parseStory(s), st = exp.stories[x.key];
    const ctx = name + ' #' + (i + 1) + ' ' + x.key;
    ok(ctx + ': page span ' + x.start_page + '-' + x.end_page, s.firstPage === x.start_page && s.lastPage === x.end_page, s.firstPage + '-' + s.lastPage);
    ok(ctx + ': docref', p.docref_key === NB.docrefKey(x.docref), p.docref + ' vs ' + x.docref);
    const hl = (st.same_as ? exp.stories[st.same_as] : st);
    ok(ctx + ': headline', p.headline === hl.hl, JSON.stringify(p.headline));
    ok(ctx + ': date', p.date === [hl.d[0], String(hl.d[1]).padStart(2, '0'), String(hl.d[2]).padStart(2, '0')].join('-'), p.date);
    ok(ctx + ': outlet', p.outlet === hl.src, p.outlet);
    if (hl.au) ok(ctx + ': author', p.author === hl.au, p.author);
    if (!st.image && hl.n) ok(ctx + ': NewsBank word count', p.words_nb === hl.n, p.words_nb);
    ok(ctx + ': no parse flags', p.flags.length === 0, p.flags.join('; '));
    ok(ctx + ': kind', p.kind === (hl.image ? 'print_page' : 'article'), p.kind);
    if (name === 'batch_A' && (x.key === 'long2' || x.key === 'rep7' || x.key === 'print9')) ok(ctx + ': spans a shared page, bands recorded', s.bands.length === (x.end_page - x.start_page + 1) && s.bands.some(b => !b.full), JSON.stringify(s.bands));
    if (name === 'batch_B') ok(ctx + ': page-aligned flow, no shared page', !s.sharedFirst && !s.sharedLast, JSON.stringify(s.bands));
    if (x.key === 'long2') ok(ctx + ': body text is only its own', !/Valley Courier/.test(p.text) && /Jesse Gabriel/.test(p.text) && p.body_words > 300, p.body_words);
    if (x.key === 'zh3') ok(ctx + ': Chinese headline and text read', /加布里埃尔/.test(p.headline) && /杰西/.test(p.text), p.text.slice(0, 40));
  });
}
// a citation read with no header (a hand-trimmed story): details come from the citation
{
  const c = 'Tat, L. (2026, March 19). Things could heat up in LA County\'s Assembly races, with no incumbent in 5 contests.Pasadena Star- News: Web Edition Articles (CA). Available from NewsBank: Access World News – Historical and Current: https://infoweb.newsbank.com/apps/news/document- view?p=WORLDNEWS&docref=news/1A6F902115B5E450.';
  const p = NB.parseStory({ lines: [], citation: c });
  ok('citation only: date', p.date === '2026-03-19', p.date); ok('citation only: docref', p.docref === 'news/1A6F902115B5E450', p.docref);
  ok('citation only: headline and outlet split', p.headline.startsWith('Things could heat up') && /^Pasadena Star-?\s?News/.test(p.outlet), p.headline + ' | ' + p.outlet);
  ok('citation only: flagged', p.flags.length > 0 && p.how === 'citation', p.flags.join(';'));
  const q = NB.parseCitation('(2026, September 20). Monterey County Herald, The (CA) , p. 5. Available from NewsBank: Access World News – Historical and Current: https://infoweb-newsbank-com.castatelib.idm.oclc.org/apps/news/document-view?p=WORLDNEWS&docref=image/v2%3A195E16E9F3E9C3B0%40AWNB-1AABE8E425C5268C%402461304-1AABE8F021C40C9F%404-1AABE8F021C40C9F%40.');
  ok('print-page citation: no author, date, proxy host, image docref', q.author === '' && q.date === '2026-09-20' && /castatelib/.test(q.host) && /^image\/v2%3A/.test(q.docref), JSON.stringify(q));
  ok('docref hyphen restored after the julian date', NB.docrefFix('image/v2%3AAAAA%40AWNB-BBBB%402461304CCCCCCCCCCCCCCCC%404-D') .includes('%402461304-CCCCCCCCCCCCCCCC'), NB.docrefFix('image/v2%3AAAAA%40AWNB-BBBB%402461304CCCCCCCCCCCCCCCC%404-D'));
}

// ---- the REAL layout (banner, labelled header, ALL-CAPS headline, APA citation without author, openurl link wrapped at a fixed width, even inside a word) ----
{
  const er = JSON.parse(fs.readFileSync(path.join(dir, 'expected_real.json'), 'utf8'));
  for (const name of ['real_pages', 'real_mid']) {
    const pages = await readBatch(path.join(dir, name + '.pdf')), r = NB.splitBatch(pages), e = er[name];
    ok(name + ': ' + e.items.length + ' stories found', r.stories.length === e.items.length, r.stories.length);
    ok(name + ': nothing left over', r.tail.length === 0 && r.junk.length === 0, JSON.stringify([r.tail, r.junk]));
    const ids = new Set(), keys = new Set();
    r.stories.forEach((s, i) => {
      const x = e.items[i], p = NB.parseStory(s), ctx = name + ' ' + x.key;
      ok(ctx + ': page span ' + x.start_page + '-' + x.end_page, s.firstPage === x.start_page && s.lastPage === x.end_page, s.firstPage + '-' + s.lastPage);
      ok(ctx + ': headline (all lines, whole words)', p.headline === x.headline, JSON.stringify(p.headline));
      ok(ctx + ': date', p.date === x.date, p.date);
      ok(ctx + ': source', p.outlet === x.source, p.outlet);
      ok(ctx + ': section', p.section === x.section, p.section);
      if (x.author) ok(ctx + ': author', p.author === x.author, p.author);
      if (!x.printpage) ok(ctx + ': word count', p.words_nb === x.words, p.words_nb);
      if (x.printpage) ok(ctx + ': printed page 18 and print_page kind', p.page === x.page && p.kind === 'print_page', p.page + ' ' + p.kind);
      ok(ctx + ': docref from the openurl link (decoded twice)', p.docref === x.docref, p.docref + ' vs ' + x.docref);
      ok(ctx + ': canonical sheet link', NB.canonLink(p.docref) === 'https://infoweb.newsbank.com/apps/news/document-view?p=WORLDNEWS&docref=' + x.docref, NB.canonLink(p.docref));
      ok(ctx + ': no parse flags', p.flags.length === 0, p.flags.join('; '));
      ok(ctx + ': the citation has the headline in whole words and "NewsBank"', p.citation.includes(x.headline) && /Available from NewsBank: https:\/\/infoweb\.newsbank\.com\/apps\/news\/openurl\?/.test(p.citation) && !/\w \w{1,2}\.? Available|DANGERO US/.test(p.citation), p.citation.slice(0, 160));
      ok(ctx + ': the banner is not in the text', !/Access World News/.test(p.text) && !/Access World News/.test(p.headline), p.text.slice(0, 60));
      if (!x.printpage) ok(ctx + ': body starts at the body', p.text.length > 100 && !/^Date:|^Source:/.test(p.text), p.text.slice(0, 60));
      ok(ctx + ': unique key and docref', !ids.has(p.docref_key) && !keys.has(s.index), p.docref_key); ids.add(p.docref_key); keys.add(s.index);
      if (name === 'real_pages') ok(ctx + ': page-aligned: no bands', s.bands.every(b => b.full) && !s.sharedFirst && !s.sharedLast, JSON.stringify(s.bands));
    });
    if (name === 'real_mid') ok(name + ': stories that share a page get a band, others none', r.stories[0].bands.some(b => !b.full) && r.stories[3].bands.every(b => b.full), JSON.stringify(r.stories.map(s => s.bands.filter(b => !b.full).length)));
  }
  // the citation's wrap, in words: lines cut in the middle of a word join without a space; the header puts back what the join cannot know
  ok('fixLike restores a headline from a citation cut inside words', NB.fixLike('SAN DIEGO. (2026, October 6). US Fed News (USA). Available from New sBank: x', 'Available from NewsBank').includes('Available from NewsBank: x'), '');
  ok('fixLike: DANGERO US -> DANGEROUS', NB.fixLike("TRUMP'S DANGERO US REMARKS. (2026", "TRUMP'S DANGEROUS REMARKS") === "TRUMP'S DANGEROUS REMARKS. (2026", '');
  const q = NB.parseCitation('TWO NEW LAWSUITS REIGNITE THE DEBATE. (2026, October 6). CE Noticias Financieras: English. Available from NewsBank: https://infoweb.newsbank.com/apps/news/openurl?ctx_ver=z39.88-2004&rft_id=info%3Asid/infoweb.newsbank.co m&svc_dat=WORLDNEWS&rft_dat=document_id%3Anews%252F1AB14299E2B1ED70.');
  ok('citation without an author: headline first, outlet after the date', q.author === '' && q.cit_title === 'TWO NEW LAWSUITS REIGNITE THE DEBATE' && q.cit_outlet === 'CE Noticias Financieras: English' && q.date === '2026-10-06' && q.docref === 'news/1AB14299E2B1ED70', JSON.stringify(q));
  const q2 = NB.parseCitation('Doe, J. (2026, October 10). Budget chair says aid will move. Valley Courier Test (CA). Available from NewsBank: https://infoweb.newsbank.com/apps/news/openurl?x=1&rft_dat=document_id%3Anews%252F1AB14299E2B1ED70.');
  ok('citation with an author', q2.has_author && q2.author === 'Doe, J' && q2.cit_title === '', JSON.stringify(q2));
  // no readable header and no docref: the parser says so (the page then calls the story "needs a look", never new)
  const bare = NB.parseStory({ lines: [{ p: 1, y: 700, h: 10, text: 'some words with no header at all' }], citation: 'nothing useful here' });
  ok('no header and no link: flagged, no docref', bare.how === 'citation' && !bare.docref && bare.flags.length >= 2, JSON.stringify(bare.flags));
}
console.log(fail ? fail + ' FAILED' : 'all passed'); process.exit(fail ? 1 : 0);
