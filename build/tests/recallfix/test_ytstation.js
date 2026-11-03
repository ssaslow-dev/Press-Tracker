// YTSTATION-v1 unit checks: the two YouTube searches in the plan, the channel filter, the find's fields, the run row's Data Source and _av.
// node build/tests/recallfix/test_ytstation.js   (same harness as test_recallfix.js)
const fs = require('fs'), path = require('path'), vm = require('vm');
const L = path.resolve(__dirname, '..', '..', '..');
const src = ['40_update_outlets.js', '41_update_search.js'].map(f => fs.readFileSync(path.join(L, 'code/tracker', f), 'utf8')).join('\n');
const rs = JSON.parse(fs.readFileSync(path.join(L, 'code/recall_sources.json'), 'utf8')), em = JSON.parse(fs.readFileSync(path.join(L, 'code/ems_ca_outlets.json'), 'utf8'));
const block = { skip_urls: [], never_coverage: [{ host: 'youtube.com', prefix: '', why: 'x' }], recall: Object.assign({}, rs, { ethnic: Object.assign({}, rs.ethnic, { outlets: em.outlets.map(o => [o.host, o.language, o.region, o.city, o.name]) }) }) };
const hostOf = u => { try { return new URL(u).hostname.replace(/^www\./, ''); } catch(e){ return ''; } };
const STUB = new Proxy(function(){}, { get: (t, k) => k === Symbol.toPrimitive ? () => '' : STUB, set: () => true, apply: () => STUB });
const document = new Proxy({ getElementById: id => id === 'fetchrules' ? { textContent: JSON.stringify(block) } : null }, { get: (t, k) => k in t ? t[k] : STUB });
const D = [{ id: 's2', date: '2026-10-20', link: 'https://www.foxla.com/news/gas', outlet: 'FOX 11 Los Angeles', pub: 'FOX 11 Los Angeles', media: 'TV', hl: 'Gas rebate debated', pick: 0 }, { id: 's1', date: '2026-10-20', link: 'https://www.ktla.com/news/a', outlet: 'KTLA', media: 'TV', hl: 'Newsom signs bill', pick: 0 }];
const ctx = { D, TODAY: '2026-11-02', LAST: '2026-10-25', U: { since: '2026-10-26', sinceManual: '2026-10-26' }, BILL_INFO: [], LOG: { runs: [] }, hostOf,
  normU: u => String(u).replace(/#.*$/, '').replace(/\/$/, '').toLowerCase(), normH: h => String(h || '').toLowerCase().replace(/\W+/g, ' ').trim(),
  esc: s => String(s), console, URL, URLSearchParams, Map, Set, Date, JSON, Math, Object, Array, String, RegExp, Number, Promise, Intl, encodeURIComponent, Error, setTimeout,
  $: () => STUB, document, window: STUB, VS: (s, n) => String(s || '').slice(0, n), fmt: String, pl: (n, w) => n + ' ' + w, STOP_CODES: new Set() };
ctx.TONE_OK = new Set(['Positive', 'Neutral', 'Negative']);
vm.createContext(ctx);
let fails = 0, n = 0; const ok = (c, m) => { n++; console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
try { vm.runInContext(src + '\n;globalThis.__x = { tfPlan, tfDedupe, ytId, ytRead, ytJudge, ytRow, ytChannelEntry, ytOembed, ytOembedParse, ytSameSegment, YT_DATA, U, proposeRows, covRow };', ctx); }
catch(e){ console.log('FAIL load: ' + e.message); process.exit(1); }
ctx.byId = new Map([['s2', D[0]]]);
const X = ctx.__x;
// 1. plan: two searches on every run (manual Since or default), each on youtube.com with the date filter
for (const manual of [true, false]){
  X.U.sinceManual = manual ? '2026-10-26' : ''; X.U.since = '2026-10-26';
  const P = X.tfDedupe(X.tfPlan()).plan, yt = P.filter(x => x.kind === 'youtube');
  ok(yt.length === 2 && yt.every(x => x.include_domains === 'youtube.com' && x.yt && x.keepDate) && yt[0].query === '"Jesse Gabriel"' && yt[1].query === '"Assemblymember Gabriel" OR "Assemblyman Gabriel"',
    `plan (${manual ? 'manual Since' : 'default'}): two YouTube searches, include_domains youtube.com, date filter (plan size ${P.length})`);
}
// LANGCAP-v1: the four new channels resolve (by name, trimmed), the Cantonese key with a trailing space too
{ const E = (n, u) => X.ytChannelEntry(n, u);
  ok(E('Noticias Telemundo').outlet === 'Noticias Telemundo' && E('CA Today 今日加州').outlet === 'NTD Television' && E('Sky Link TV Mandarin News 天下衛視 國語新聞頻道').outlet === 'Sky Link TV' && E('KBS News').outlet === 'KBS News' && E('KBS News').medium === 'TV',
    'LANGCAP: Noticias Telemundo, CA Today, Sky Link Mandarin, KBS News map to their outlets');
  ok(E('Sky Link TV Cantonese News 天下衛視 粵語新聞頻道 ').outlet === 'Sky Link TV' && E('  KBS News  ').outlet === 'KBS News' && E('Sky Link TV Mandarin News 天下衛視 國語新聞頻道 ').outlet === 'Sky Link TV', 'LANGCAP: names match after trimming whitespace (trailing space in the oEmbed name)');
  ok(!E('VOA 한국어') && !E('邓洪说法') && !E('Telemundo eñe'), 'LANGCAP: VOA Korean and the lawyer channel are not mapped');
  ok(E('x', 'https://www.youtube.com/@catoday4157').outlet === 'NTD Television', 'LANGCAP: CA Today also resolves by @handle'); }
// 2. video ids
ok(X.ytId('https://www.youtube.com/watch?v=P6zsjIepWaQ&t=5') === 'P6zsjIepWaQ' && X.ytId('https://www.youtube.com/shorts/abcdefghijk') === 'abcdefghijk' && X.ytId('https://youtu.be/P6zsjIepWaQ') === 'P6zsjIepWaQ'
  && X.ytId('https://www.youtube.com/@foxla') === '' && X.ytId('https://www.youtube.com/playlist?list=PL1') === '', 'video ids: watch, shorts, youtu.be; channels and playlists have none');
// 3. the page: channel, date, description from the real page shape
const html = fs.readFileSync(path.join(__dirname, 'yt_page_fixture.html'), 'utf8');
const mk = (title, ch) => { const c = { yt: 'P6zsjIepWaQ', url: 'https://www.youtube.com/watch?v=P6zsjIepWaQ', title, published: '', text: '' }; X.ytRead(c, { text: ch === null ? html.replace(/<ytd-channel-name>[\s\S]*?<\/ytd-channel-name>/, '') : html.replace('FOX 11 Los Angeles</yt-formatted-string>\n</p>\n</ytd-channel-name>', ch + '</yt-formatted-string>\n</p>\n</ytd-channel-name>'), title }, ''); return c; };
const c1 = mk('Special Report: Assemblyman Jesse Gabriel', 'FOX 11 Los Angeles');
ok(c1.ytChannel === 'FOX 11 Los Angeles' && c1.published === '2022-03-17' && c1.dateSrc === 'page' && c1.ytNamed === true, 'page read: channel "FOX 11 Los Angeles", date 2022-03-17, title/description names him');
// 4. channel filter
ok(X.ytJudge(c1) === '', 'FOX 11 Los Angeles is kept');
const c2 = mk('Lawmaker calls out GOP', 'Forbes Breaking News');
ok(/not on a station's own channel \(NOBLOGS-v1\)/.test(X.ytJudge(c2)), 'Forbes Breaking News is skipped: "YouTube video not on a station\'s own channel (NOBLOGS-v1)"');
ok(['KTLA 5', 'ABC7', 'NBCLA', 'CBS Los Angeles', 'KCAL News', 'Telemundo 52', 'Univision 34 Los Angeles', 'Spectrum News', 'KCRA 3', 'ABC10', 'FOX40 News', 'KTVU FOX 2 San Francisco', 'KRON 4',
  'ABC7 News Bay Area', 'NBC Bay Area', 'CBS News Bay Area', 'CapRadio', 'KQED', 'CNN', 'Fox News', 'NBC News', 'CBS News', 'ABC News', 'NewsNation', 'PBS NewsHour', 'MSNBC'].every(x => X.ytChannelEntry(x))
  && !X.ytChannelEntry('Assemblymember Jesse Gabriel') && !X.ytChannelEntry('California Assembly Democrats') && X.ytChannelEntry('fox 11 los angeles'), 'channel map: every requested station present (case-insensitive); the office and Assembly channels are not');
ok(X.ytJudge(mk('x', null)) !== '' && /could not be read/.test(X.ytJudge(mk('x', null))), 'no channel on the page: skipped, not guessed');
// 4b. oEmbed: the channel comes from author_name / author_url (fetch_content, 10 videos a call); the @handle also matches
const oj = (name, handle) => JSON.stringify({ title: 't', author_name: name, author_url: 'https://www.youtube.com/@' + handle, type: 'video' });
ok(X.ytOembedParse('```json\n' + oj('FOX 11 Los Angeles', 'foxla') + '\n```').name === 'FOX 11 Los Angeles' && X.ytOembedParse('not json') === null, 'oEmbed JSON parsed (also inside a code fence); junk gives null');
ok(X.ytChannelEntry('FOX 11 LA (renamed)', 'https://www.youtube.com/@foxla').outlet === 'FOX 11 Los Angeles' && !X.ytChannelEntry('AssemblyAssets', 'https://www.youtube.com/@AssemblyAssets'), 'handle @foxla matches FOX 11 when the name differs; AssemblyAssets does not match');
(async () => {
  const vids = ['P6zsjIepWaQ', 'nIKyZqVQaFo', 'AAAAAAAAAAA'], calls = [];
  const names = { P6zsjIepWaQ: ['FOX 11 Los Angeles', 'foxla'], nIKyZqVQaFo: ['Forbes Breaking News', 'ForbesBreakingNews'] };
  const mcp = { callTool: async (s, tool, inp) => { calls.push(inp); return { payload: { results: inp.urls.map(u => { const id = decodeURIComponent(u).match(/v=([\w-]{11})/)[1], nm = names[id]; return nm ? { url: u, text: oj(nm[0], nm[1]) } : null; }).filter(Boolean) } }; } };
  X.U.ctl = { signal: { aborted: false } };
  const list = vids.map(v => ({ yt: v, url: 'https://www.youtube.com/watch?v=' + v, title: 't' }));
  await X.ytOembed(mcp, list);
  ok(calls.length === 1 && calls[0].urls.length === 3 && /oembed/.test(calls[0].urls[0]), 'oEmbed: one fetch_content call for the 3 candidates (batch of up to 10)');
  ok(list[0].ytChannel === 'FOX 11 Los Angeles' && X.ytJudge(list[0]) === '' && /not on a station's own channel/.test(X.ytJudge(list[1])) && list[2].ytChannel === undefined, 'oEmbed: FOX 11 kept, Forbes Breaking News skipped, an unreadable oEmbed leaves the channel to the opened page');
// 5. the find's fields
const row = { outlet: 'youtube.com', pub: 'youtube.com', media: 'Online news', fmt: 'Video clip', why: 'ok', link: c1.url, date: '2022-03-17', hl: c1.title };
X.ytRow(row, c1);
ok(row.outlet === 'FOX 11 Los Angeles' && row.media === 'TV' && row.fmt === 'Broadcast segment' && row.lstat === 'Publisher URL' && row.ds === 'Web search (TinyFish, YouTube station channel)' && !row._ycheck,
  'find: Outlet FOX 11 Los Angeles, Medium TV, Format Broadcast segment, Link status Publisher URL, Data Source "Web search (TinyFish, YouTube station channel)"');
ok(JSON.stringify(row._av) === JSON.stringify({ 'Item type': 'Broadcast segment', 'Channel': 'FOX 11 Los Angeles', 'Station': 'KTTV', 'Network': 'FOX', 'Episode/segment title': 'Special Report: Assemblyman Jesse Gabriel',
  'Air/publish date': '2022-03-17', 'YouTube link': c1.url, 'Details from': 'YouTube page' }), 'find: av values (Item type, Channel, Station, Network, title, air date, YouTube link, Details from)');
const cr = mk('Other video', 'CapRadio'); cr.ytNamed = false; cr.published = ''; cr.dateSrc = ''; const r2 = { outlet: 'x', pub: 'x', why: '' }; X.ytRow(r2, cr);
ok(r2.media === 'Radio' && r2._ycheck === true && /^CHECK:/.test(r2.why) && r2._av['Air/publish date'] === '', 'radio station: Medium Radio; not named in title/description: flagged for checking; no page date -> air date blank');
// 6. the run row
try {
  // proposeRows leans on helpers from other tracker files; stub each missing one as a pass-through (only the fields under test are checked)
  const stubs = { covCols: 0 }; let out;
  for (let i = 0; i < 40 && !out; i++){
    try { out = X.proposeRows('t1', [Object.assign({ id: 'jg-aaaaaa', rep: 0, link: c1.url, plink: c1.url, tone: '', bills: [], topic: 'Other', conf: 'Confirmed', src: 'Web, verified' }, row)], []).rows[0]; }
    catch(e){ const m = /^(\w+) is not defined/.exec(e.message); if (!m) throw e; ctx[m[1]] = (...a) => a[0] == null ? '' : a[0]; }
  }
  ok(out['Data Source'] === 'Web search (TinyFish, YouTube station channel)' && out['Medium'] === 'TV' && out['Format'] === 'Broadcast segment' && out['Link status'] === 'Publisher URL' && out['Publisher link'] === c1.url && out._av && out._av.Channel === 'FOX 11 Los Angeles',
    'run row: Data Source, Medium, Format, Link status, Publisher link and _av reach the sheet task');
} catch(e){ ok(false, 'run row: ' + e.message); }
// 7. same segment as a tracked story: the outlet has a story within 2 days of the video's date -> attach, not a new story
{ const row = { outlet: 'FOX 11 Los Angeles', pub: 'FOX 11 Los Angeles' }, mkc = (d) => ({ dateSrc: d ? 'page' : '', published: d });
  X.U.since = '2026-10-15';
  const m1 = X.ytSameSegment(row, mkc('2026-10-21')), m2 = X.ytSameSegment(row, mkc('2026-10-22')), m3 = X.ytSameSegment(row, mkc('2026-10-24')), m4 = X.ytSameSegment(row, mkc(''));
  X.U.since = '2026-10-26'; const m5 = X.ytSameSegment(row, mkc(''));
  ok(m1 && m1.id === 's2' && m2 && m2.id === 's2' && m3 === null, 'same segment: FOX 11 story 2026-10-20 matches a video dated 10-21 and 10-22 (within 2 days), not 10-24');
  ok(m4 && m4.id === 's2' && m5 === null, 'same segment: a video with no date is checked against the run window (story 10-20: inside a 10-15 window, outside a 10-26 one)');
  ok(X.ytSameSegment({ outlet: 'KQED', pub: 'KQED' }, mkc('2026-10-21')) === null, 'same segment: another outlet\'s story does not match'); }
// 8. the reprint path: a station video that is a reprint of a tracked story is a Broadcast segment, not a Video clip
try {
  let out;
  for (let i = 0; i < 40 && !out; i++){
    try { out = X.proposeRows('t2', [], [{ story: 's2', outlet: 'FOX 11 Los Angeles', link: 'https://www.youtube.com/watch?v=P6zsjIepWaQ', date: '2026-10-21', hl: 'x', _av: { 'Item type': 'Broadcast segment', Channel: 'FOX 11 Los Angeles', 'Details from': 'YouTube page' } },
      { story: 's2', outlet: 'Some Site', link: 'https://www.youtube.com/watch?v=zzzzzzzzzzz', date: '2026-10-21', hl: 'y' }]).rows; }
    catch(e){ const m = /^(\w+) is not defined/.exec(e.message); if (!m) throw e; ctx[m[1]] = (...a) => a[0] == null ? '' : a[0]; }
  }
  ok(out[0].Format === 'Broadcast segment' && out[0]._av && out[0]._av.Channel === 'FOX 11 Los Angeles' && out[0]['Data Source'] === 'Web search (TinyFish, YouTube station channel)' && out[1].Format === 'Video clip' && !out[1]._av, 'reprint path: station-channel video -> Format Broadcast segment with _av; any other YouTube reprint stays Video clip');
} catch(e){ ok(false, 'reprint path: ' + e.message); }
})().then(() => { console.log(fails ? `${fails} FAILED` : `ALL ${n} CHECKS PASSED`); process.exit(fails ? 1 : 0); });
