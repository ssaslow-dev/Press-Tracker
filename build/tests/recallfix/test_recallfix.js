// RECALLFIX-v1 unit checks: Google News RSS parsing of fetch_content output, priority outlets, ethnic-media plan, TV caps, podcasts, release time stamp.
// node build/tests/recallfix/test_recallfix.js   (reads code/tracker/40_update_outlets.js + 41_update_search.js, code/recall_sources.json, code/ems_ca_outlets.json)
const fs = require('fs'), path = require('path'), vm = require('vm');
const L = path.resolve(__dirname, '..', '..', '..');
const src = ['40_update_outlets.js', '41_update_search.js'].map(f => fs.readFileSync(path.join(L, 'code/tracker', f), 'utf8')).join('\n');
const rs = JSON.parse(fs.readFileSync(path.join(L, 'code/recall_sources.json'), 'utf8')), em = JSON.parse(fs.readFileSync(path.join(L, 'code/ems_ca_outlets.json'), 'utf8'));
const block = { skip_urls: [], never_coverage: [{ host: 'youtube.com', prefix: '', why: 'x' }], recall: Object.assign({}, rs, { ethnic: Object.assign({}, rs.ethnic, { outlets: em.outlets.map(o => [o.host, o.language, o.region, o.city, o.name]) }) }) };
const hostOf = u => { try { return new URL(u).hostname.replace(/^www\./, ''); } catch(e){ return ''; } };
const STUB = new Proxy(function(){}, { get: (t, k) => k === Symbol.toPrimitive ? () => '' : STUB, set: () => true, apply: () => STUB });
const document = new Proxy({ getElementById: id => id === 'fetchrules' ? { textContent: JSON.stringify(block) } : null }, { get: (t, k) => k in t ? t[k] : STUB });
const D = [
  { id: 's1', date: '2026-10-20', link: 'https://www.ktla.com/news/a', outlet: 'KTLA', media: 'TV', hl: 'Newsom signs bill', pick: 0 },
  { id: 's2', date: '2023-01-01', link: 'https://www.vannuysnewspress.com/x', outlet: 'Van Nuys News Press', media: 'Newspaper', hl: 'old story long ago here', pick: 0 },
  { id: 's3', date: '2026-10-01', link: 'https://lasentinel.net/x', outlet: 'LA Sentinel', media: 'Newspaper', hl: 'Sentinel story', pick: 0 },
];
const ctx = { D, TODAY: '2026-11-02', LAST: '2026-10-25', U: { since: '2026-10-26', sinceManual: '2026-10-26' }, BILL_INFO: [], LOG: { runs: [] }, hostOf,
  normU: u => String(u).replace(/[?#].*$/, '').replace(/\/$/, '').toLowerCase(), normH: h => String(h || '').toLowerCase().replace(/\W+/g, ' ').trim(),
  esc: s => String(s), console, URL, URLSearchParams, Map, Set, Date, JSON, Math, Object, Array, String, RegExp, Number, Promise, Intl, encodeURIComponent, Error, setTimeout,
  $: () => STUB, document, window: STUB, VS: (s, n) => String(s || '').slice(0, n), fmt: String, pl: (n, w) => n + ' ' + w, STOP_CODES: new Set() };
vm.createContext(ctx);
let fails = 0, n = 0; const ok = (c, m) => { n++; console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
try { vm.runInContext(src + '\n;globalThis.__x = { tfPlan, gnewsParse, podcastParse, relStamp, tvQuery, tvCap, tvCaptions, podcastSearch, RC_DATA, searchPlan, tfDedupe, U };', ctx); }
catch(e){ console.log('FAIL load: ' + e.message); process.exit(1); }
const X = ctx.__x; X.U.since = '2026-10-26'; 

// 1. Google News RSS: the three shapes fetch_content returns
const item = (t, l, d, s, su) => `<item><title>${t}</title><link>${l}</link><guid isPermaLink="false">g</guid><pubDate>${d}</pubDate><description>x</description><source url="${su}">${s}</source></item>`;
const xml = `<rss version="2.0"><channel><title>t</title><link>https://news.google.com/</link>` + item('Assembly Budget Chair Jesse Gabriel Delivers $2.5 Million &amp; more - Van Nuys News Press', 'https://news.google.com/rss/articles/CBMi_ab-Z?oc=5', 'Thu, 29 Oct 2026 17:48:07 GMT', 'Van Nuys News Press', 'https://www.vannuysnewspress.com')
  + item('Sepulveda Basin gets $22M - Los Angeles Daily News', 'https://news.google.com/rss/articles/CBMi2?oc=5', 'Mon, 26 Oct 2026 22:36:32 GMT', 'Los Angeles Daily News', 'https://www.dailynews.com') + `</channel></rss>`;
const esc = x => x.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const htmlShape = '<body><p>This XML file does not appear to have any style information.</p>' + xml.replace(/&amp;/g, '&').replace(/></g, '>\n<').split('\n').map(l => '<p>' + esc(l).replace(/&amp;amp;/g, '&amp;amp;') + '</p>').join('') + '</body>';
const mdShape = xml.replace(/></g, '>\n\n<').replace(/_/g, '\\_');
const hp = X.gnewsParse(htmlShape);
const mp = X.gnewsParse(mdShape), raw = X.gnewsParse(xml);
ok(hp.length === 2 && hp[0].title === 'Assembly Budget Chair Jesse Gabriel Delivers $2.5 Million & more' && hp[0].site === 'Van Nuys News Press' && hp[0].published === '2026-10-29' && /^https:\/\/news\.google\.com\/rss\/articles\/CBMi_ab-Z\?oc=5$/.test(hp[0].url),
  'RSS as fetch_content format html (entity-escaped XML in <p> lines, the shape that gave 0 items): 2 items, title, source, date, link');
ok(mp.length === 2 && mp[0].url === 'https://news.google.com/rss/articles/CBMi_ab-Z?oc=5', 'RSS as markdown (raw XML, "\\_" escapes): 2 items, link un-escaped');
ok(raw.length === 2, 'raw XML still parses');
ok(X.gnewsParse('[Some headline about Gabriel - Outlet](https://news.google.com/rss/articles/CBMi3)').length === 1, 'markdown link fallback unchanged');
// 2. priority outlets: in the plan on every run, including a manual Since, even with no story in 24 months
const needed = ['ktla.com', 'abc7.com', 'nbclosangeles.com', 'cbsnews.com', 'foxla.com', 'spectrumnews1.com', 'audacy.com', 'kfiam640.iheart.com', 'laist.com', 'telemundo52.com', 'univision.com',
  'valleynewsgroup.com', 'vannuysnewspress.com', 'sanfernandosun.com', 'dailynews.com', 'ivpressonline.com'];
for (const manual of [true, false]){
  X.U.sinceManual = manual ? '2026-10-26' : ''; const P = X.tfPlan(), pr = P.filter(x => /^Priority outlets/.test(x.label));
  const hs = new Set(pr.flatMap(x => x.hosts));
  ok(needed.every(h => hs.has(h)) && pr.every(x => x.keepDate && x.kind === 'fresh' && x.hosts.length <= 4 && x.query.split(' OR ').length === x.hosts.length), `priority outlets in the plan (${manual ? 'manual Since' : 'default'}): ${pr.length} OR-grouped searches with the date filter, all ${needed.length} hosts`);
}
X.U.sinceManual = '2026-10-26';
const P = X.tfPlan(), pr = P.filter(x => /^Priority outlets/.test(x.label));
ok(pr.length === 6 && /site:cbsnews\.com\/losangeles/.test(pr.map(x => x.query).join(' ')), 'priority list = 12 LA TV/radio + 5 Valley sites + 3 podcast pages (PODSITE-v1) -> 6 searches; CBS LA keeps its path');
ok(X.tfDedupe(P).plan.filter(x => /^Priority outlets/.test(x.label)).length === 6, 'dedupe keeps the priority searches');
// 5. ethnic media
const et = P.filter(x => /^Ethnic media/.test(x.label));
ok(et.length > 0 && et.length <= 28 && et.every(x => x.keepDate && x.hosts.length <= 8 && x.kind === 'fresh'), `ethnic media: ${et.length} searches (cap 28), OR-of-8 with the date filter`);
ok(!et.some(x => x.hosts.includes('lasentinel.net')), 'ethnic media: an outlet already on record (LA Sentinel) is not searched again');
ok(et.some(x => /제시 가브리엘/.test(x.query) && x.hosts.length) && et.some(x => /加布里埃尔/.test(x.query)), 'ethnic media: Korean and Chinese groups also search his name in script');
const first = et[0].hosts; ok(em.outlets.filter(o => first.includes(o.host)).every(o => o.region === 'Southern California'), 'ethnic media: Southern California outlets come first');
// 3. TV
ok(X.tvQuery('National') === '("jesse gabriel" OR "assemblymember gabriel" OR "assemblyman gabriel" OR "budget chair gabriel") (market:"National")', 'TV caption query names him four ways');
ok(X.tvCap('KTLA') === 3 && X.tvCap('CNN') === 1, 'TV: LA stations 3 clips per day, others 1');
(async () => {
  const clips = [1, 2, 3, 4].map(i => ({ station: 'KTLA', show: 'News at 10', show_date: '2026-10-30', preview_url: 'https://archive.org/embed/KTLA_' + i, snippet: 'assemblymember gabriel on the budget ' + i }))
    .concat([1, 2].map(i => ({ station: 'CNN', show: 'Early', show_date: '2026-10-30', preview_url: 'https://archive.org/embed/CNN_' + i, snippet: 'california budget ' + i })),
      [{ station: 'CNN', show: 'Early', show_date: '2026-10-31', preview_url: 'https://archive.org/embed/CNN_9', snippet: 'unrelated sports' }]);
  const calls = []; const mcp = { callTool: async (s, tool, inp) => { calls.push(inp); return { payload: { results: [{ url: inp.urls[0], text: '```\n' + JSON.stringify({ clips: clips.slice() }) + '\n```' }] } }; } };
  X.U.ctl = { signal: { aborted: false } };
  const out = await X.tvCaptions(mcp); 
  const k = a => out.filter(c => c.site === a).length;
  ok(k('KTLA') === 3 && k('CNN') === 1 && out.length === 4, `TV: per station per day capped (KTLA 3, CNN 1, same clip from two markets once, caption filter kept): ${out.length} clips`);
  ok(calls.length === 2 && /assemblymember\+gabriel/.test(calls[0].urls[0]), 'TV: one call per market, query carries the name variants');
  // 4. podcasts
  const fx = fs.readFileSync(path.join(__dirname, 'itunes_fixture.json'), 'utf8');
  const eps = X.podcastParse(fx, '2026-10-26');
  ok(eps.length === 1 && eps[0].site === 'The Capitol Show' && eps[0].published === '2026-10-30' && eps[0].podcast && eps[0].url === 'https://podcasts.apple.com/us/podcast/x/id1?i=2', 'podcasts: the fuzzy results reduce to the one episode naming him after since (the Bridgerton and Gabrielle Lyon hits and the January episode dropped)');
  ok(X.podcastParse(fx, '2026-12-01').length === 0 && X.podcastParse('{"results":[]}', '').length === 0, 'podcasts: nothing after a later since; empty result fine');
  const mcp2 = { callTool: async (s, tool, inp) => ({ payload: { results: [{ url: inp.urls[0], text: fx }] } }) };
  X.U.since = '2026-10-26'; const got = await X.podcastSearch(mcp2);
  ok(got.length === 1 && got[0].noFetch && /itunes\.apple\.com/.test(rs.podcasts.url), 'podcastSearch: one fetch_content call, candidate not opened');
  // 6. release time stamp
  const a = X.relStamp('2026-10-24T21:30:11Z'), b = X.relStamp('2026-10-02T00:00:00Z'), c = X.relStamp('2026-09-25T20:00:00Z');
  ok(a && a.utc === '2026-10-24T21:30:00Z' && a.pt === '2:30 PM PT' && b === null && c.pt === '1:00 PM PT' && X.relStamp('') === null, 'release time stamp: UTC -> Pacific; midnight UTC (date only) ignored');
  console.log(fails ? `${fails} FAILED` : `ALL ${n} CHECKS PASSED`); process.exit(fails ? 1 : 0);
})();
