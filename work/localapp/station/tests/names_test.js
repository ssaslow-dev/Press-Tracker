/* STATIONNAMES: the station's file-naming rules (src/names.js), no browser needed.   node tests/names_test.js */
const N = require('../src/names.js');
let failed = 0; const check = (name, ok, extra) => { if (!ok) failed++; console.log((ok ? 'PASS ' : 'FAIL ') + name + (!ok && extra !== undefined ? '  -> ' + JSON.stringify(extra) : '')); };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);

const next = { aid: 10670, s: 4942, pr: 245 };
const row = (o) => Object.assign({ 'Original or reprint': 'Original', Date: '2026-11-01', Year: 2026 }, o);
const pages = {
  'jg-aaaaaa': { url: 'https://x/a', clean: '<html>clean A</html>', scoped: '<html>scoped A</html>' },
  'jg-bbbbbb': { url: 'https://infoweb.newsbank.com/x', clean: '<article>nb text</article>', nb: { docref: 'd', file: 'files/nb-0123456789abcdef.pdf', pdf_sha256: 'x' } },
  'jg-cccccc': { url: 'https://www.proquest.com/docview/1', clean: '<article>pq text</article>', pq: { docid: '1', file: 'files/pq-fedcba9876543210.pdf', pdf_sha256: 'y', header: {} } },
  'rp-111111111111': { url: 'https://y/r', clean: '<html>reprint</html>', scoped: '' },
};
const runs = [{
  id: 'run-1', at: '2026-11-03T10:00:00Z',
  rows: [
    row({ 'Article ID': 'NEW-1', 'Story ID': 'sNEW-1', 'Tracker story code': 'jg-aaaaaa' }),                                                  // web find
    row({ 'Article ID': 'NEW-2', 'Story ID': 'sNEW-2', 'Tracker story code': 'jg-bbbbbb', Date: '2025-03-04' }),                           // NewsBank
    row({ 'Article ID': 'NEW-3', 'Story ID': 's04930', 'Original or reprint': 'Reprint', _page: 'rp-111111111111' }),                       // reprint of an existing story
    row({ 'Article ID': 'NEW-4', 'Story ID': 'sNEW-4', 'Tracker story code': 'jg-cccccc', Date: '' , Year: ''}),                            // ProQuest, undated -> this year
    row({ 'Article ID': 'NEW-5', 'Story ID': 'sNEW-1', 'Original or reprint': 'Reprint' }),                                                 // reprint of the first find, no page
  ],
  releases_new: [{ url: 'https://gabriel.asmdc.org/b', date: '2026-10-30', title: 'B', text: 'First para.\n\nSecond.' }, { url: 'https://gabriel.asmdc.org/a', date: '2026-10-29', title: 'A', html: '<p>hello</p>' },
    { url: 'https://jewishcaucus.example/old', date: '2019-01-01', title: 'old', src: 'caucus', text: 'x' }, { url: 'https://gabriel.asmdc.org/empty', date: '2026-11-01', title: 'E' }],
}];
const pl = N.plan({ next, runs, pages, today: '2026-11-03', existingStories: new Set(['s04930']), storyOfCode: () => '' });
const it = pl.items;
check('Originals first, one Article ID per row in order (Originals 10670 10671 10672, then Reprints 10673 10674)', eq(it.map(x => x.aid), ['10670', '10671', '10672', '10673', '10674']), it.map(x => x.aid));
check('new Originals take the next Story IDs; a reprint takes its story (placeholder resolved)', eq(it.map(x => x.sid), ['s04942', 's04943', 's04944', 's04930', 's04942']), it.map(x => x.sid));
check('web find: ws<aid>o-s<sid>.html in the date year, raw page (the differing clean copy) under _original_html', it[0].copy === 'library/2026/ws10670o-s04942.html' && it[0].raw === 'library/_original_html/2026/ws10670o-s04942.html', it[0]);
check('NewsBank story: the saved copy is the story PDF nb<aid>o-s<sid>.pdf in the story date’s year folder', it[1].copy === 'library/2025/nb10671o-s04943.pdf' && it[1].pdf_for === 'files/nb-0123456789abcdef.pdf' && !it[1].raw, it[1]);
check('ProQuest story: pq HTML copy + original PDF under _original_pdf; undated takes this year', it[2].copy === 'library/2026/pq10672o-s04944.html' && it[2].pdf === 'library/_original_pdf/2026/pq10672o-s04944.pdf' && it[2].pdf_for === 'files/pq-fedcba9876543210.pdf', it[2]);
check('reprint candidate: r, the story’s Story ID, its own pages doc and its raw page', it[3].kind === 'r' && it[3].copy === 'library/2026/ws10673r-s04930.html' && it[3].raw === 'library/_original_html/2026/ws10673r-s04930.html', it[3]);
check('a row with no pages doc takes its numbers but no files', it[4].aid === '10674' && !it[4].copy && !it[4].doc, it[4]);
check('releases in (date, url) order get pr00245, pr00246; a pre-2020-11-18 caucus release is skipped without a number; a release with no text takes a number and no file',
  eq(pl.releases.map(r => [r.prid, r.url.split('/').pop(), !!r.copy]), [['pr00245', 'a', true], ['pr00246', 'b', true], ['pr00247', 'empty', false]]), pl.releases);
check('release files: copy and raw page under Press releases / _original_html/Press releases', pl.releases[0].copy === 'library/Press releases/2026/pr00245.html' && pl.releases[0].raw === 'library/_original_html/Press releases/2026/pr00245.html');
check('the first free numbers after the update', eq(pl.used, { aid: 10675, s: 4945, pr: 248 }), pl.used);
check('files list: html text carried, pdfs by reference', pl.files.filter(f => f.kind === 'pdf').length === 2 && pl.files.find(f => f.path === it[0].copy).text === '<html>scoped A</html>' && pl.files.find(f => f.path === it[0].raw).text === '<html>clean A</html>');
const mb = N.manifestBlock(pl, '2026-11-03');
check('manifest block: version, from_next, items and releases', mb.version === 1 && eq(mb.from_next, { aid: 10670, s: 4942, pr: 245 }) && mb.items.length === 5 && mb.releases.length === 3);

// two runs: sorted by `at`, the second run continues the numbers
const r2 = [{ id: 'run-b', at: '2026-11-03T12:00:00Z', rows: [row({ 'Story ID': 'sNEW-9', 'Tracker story code': 'jg-aaaaaa' })] }, { id: 'run-a', at: '2026-11-03T09:00:00Z', rows: [row({ 'Story ID': 'sNEW-8', 'Tracker story code': 'jg-bbbbbb' })] }];
const p2 = N.plan({ next, runs: r2, pages, today: '2026-11-03' });
check('runs are numbered in the order of their time stamps', p2.items[0].run === 'run-a' && p2.items[0].aid === '10670' && p2.items[1].run === 'run-b' && p2.items[1].aid === '10671', p2.items.map(x => x.run + x.aid));

// two update zips made from the same for-Update file get the same numbers: the PC moves the second on
const again = N.plan({ next, runs, pages, today: '2026-11-03', existingStories: new Set(['s04930']), storyOfCode: () => '' });
check('the same file and the same run name the same way (the PC resolves the clash at save time)', eq(again.items.map(x => x.copy), it.map(x => x.copy)));

// a real Story ID on an Original that no story has yet is kept; one already used is not
const p3 = N.plan({ next, runs: [{ id: 'r', at: '1', rows: [row({ 'Story ID': 's05000' }), row({ 'Story ID': 's04930' })] }], pages: {}, today: '2026-11-03', existingStories: new Set(['s04930']) });
check('a real, unused Story ID is kept; an existing one gets a new story', p3.items[0].sid === 's05000' && p3.items[1].sid === 's04942', p3.items.map(x => x.sid));
check('stem and parseStem', N.stem('pq', '08882', 'Reprint', 's03441') === 'pq08882r-s03441' && eq(N.parseStem('nb00002o-s00001'), { fmt: 'nb', aid: '00002', kind: 'o', sid: 's00001' }));
console.log(failed ? failed + ' FAILED' : 'all passed'); process.exit(failed ? 1 : 0);
