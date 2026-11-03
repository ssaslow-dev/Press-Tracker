// PROQUESTPDF-v1 answer 2: the ProQuest -> tracker outlet-name map (data/proquest_outlets.json). Pure tests of src/pqparse.js.
//   node alias_test.mjs [WORKBOOK_OUTLETS.json]   (optional: a JSON list of the sheet's Outlet names, for the whole-sheet key check)
import fs from 'fs'; import path from 'path'; import { createRequire } from 'module'; import { fileURLToPath } from 'url'; import { spawnSync } from 'child_process';
const here = path.dirname(fileURLToPath(import.meta.url)), station = path.join(here, '..', '..'), req = createRequire(import.meta.url);
const PQ = req(path.join(station, 'src', 'pqparse.js')), T = JSON.parse(fs.readFileSync(path.join(station, 'data', 'proquest_outlets.json'), 'utf8'));
let fail = 0; const ok = (n, c, x) => { console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -> ' + x)); if (!c) fail++; };
// 1. Python (the build script) and the page compute the same keys and the same cleaned names
const names = T.seen_in_proquest_rows.map(x => x.outlet).concat(T.pairs.map(p => p.pq), Object.keys(T.aliases), Object.keys(T.feeds),
  ['The Center Square', 'Center Square California, The', 'El Mundo', 'Mundo, El', 'La Presse Canadienne', 'Presse Canadienne, La', 'Los Angeles Times', 'Las Vegas Review-Journal', "L'Express", 'La Opinión', 'Opinión, La', 'Die Welt',
   'Daily Herald, The', "Sacramento Bee Today's Edition, The", 'Arkansas Times: Blogs', 'El País English', 'CNN Wire Service', 'Politico', 'Café Coado Substack', 'The', '']);
if (process.argv[2]) names.push(...JSON.parse(fs.readFileSync(process.argv[2], 'utf8')));
const uniq = [...new Set(names.filter(x => x != null))];
const r = spawnSync('python3', ['-I', path.join(here, 'alias_keys.py')], { input: JSON.stringify(uniq), encoding: 'utf8', maxBuffer: 1 << 28 });
ok('python key script ran', r.status === 0, r.stderr);
const py = JSON.parse(r.stdout || '{}'); let bad = [];
for (const n of uniq) { const k = PQ.outletKeys(n), p = py[n]; if (!p || k.base !== p[0] || k.exact !== p[1] || k.fold !== p[2] || PQ.outletOf(n) !== p[3].replace(/\s+/g, ' ').trim().replace(/\s*;.*$/, '')) bad.push([n, k, p]); }
ok('the build script and the page make the same keys and the same cleaned name for ' + uniq.length + ' names', bad.length === 0, JSON.stringify(bad.slice(0, 3)));
ok('every stored pair key is the key the page computes for its ProQuest name', T.pairs.every(p => PQ.outletKeys(p.pq).fold === p.key));
// 2. cleaning (ProQuest title -> name)
const cl = [['The Center Square ; Washington', 'The Center Square'], ['New York Times, Late Edition (East Coast); New York, N.Y.', 'New York Times'], ['Wall Street Journal (Online); New York, N.Y.', 'Wall Street Journal'],
  ['Wall Street Journal, Eastern edition; New York, N.Y.', 'Wall Street Journal'], ['Wall Street Journal (1923 - Current file); New York, N.Y.', 'Wall Street Journal'], ['Los Angeles Times (pre-1997 Fulltext); Los Angeles, Calif.', 'Los Angeles Times'],
  ['Daily News; Los Angeles, Calif.', 'Daily News'], ['University Wire; Carlsbad', 'University Wire'], ['TCA Regional News; Chicago', 'TCA Regional News'], ['Sacramento Bee [subscription]; Sacramento, Calif.', 'Sacramento Bee'], ['Mundo, El; Madrid', 'Mundo, El']];
for (const [a, b] of cl) ok('clean “' + a + '” -> “' + b + '”', PQ.outletOf(a) === b, PQ.outletOf(a));
// 3. resolving against a tracker index (names as the sheet writes them, with counts)
const sheet = { 'Center Square California, The': 26, 'Center Square Texas, The': 2, 'New York Times, The': 9, 'The New York Times': 1, 'Wall Street Journal': 11, 'Mundo, El': 5, 'Presse Canadienne, La': 1, 'Los Angeles Times': 117, 'Daily News': 39, 'CNN': 13, 'CNN Wire Service': 6, 'Tribune, The': 11, 'University Wire': 15, 'Politico': 184, 'Targeted News Service': 161, 'Desert Sun, The': 4 };
const idx = { exact: new Map(), fold: new Map() }; { const best = (m, k, n) => { const o = m.get(k); if (!o || sheet[n] > o.c) m.set(k, { n, c: sheet[n] }); }, ex = new Map(), fo = new Map();
  for (const n of Object.keys(sheet)) { const k = PQ.outletKeys(n); best(ex, k.exact, n); best(fo, k.fold, n); } ex.forEach((v, k) => idx.exact.set(k, v.n)); fo.forEach((v, k) => idx.fold.set(k, v.n)); }
const R = (title, place) => PQ.resolveOutlet(PQ.outletOf(title), place || title.split(';').slice(1).join(' '), idx);
const cases = [
  ['The Center Square; Washington', 'Center Square California, The', 'pair'],
  ['New York Times, Late Edition (East Coast); New York, N.Y.', 'New York Times, The', 'tracker'],
  ['Wall Street Journal (Online); New York, N.Y.', 'Wall Street Journal', 'tracker'],
  ['El Mundo; Madrid, Spain', 'Mundo, El', 'tracker'],
  ['La Presse Canadienne; Montreal', 'Presse Canadienne, La', 'tracker'],
  ['Los Angeles Times (pre-1997 Fulltext); Los Angeles, Calif.', 'Los Angeles Times', 'tracker'],
  ['The Desert Sun; Palm Springs, Calif.', 'Desert Sun, The', 'tracker'],
  ['University Wire; Carlsbad', 'University Wire', 'tracker'],
  ['Targeted News Service; Washington', 'Targeted News Service', 'tracker'],
  ['CNN Wire Service; Atlanta', 'CNN Wire Service', 'tracker'],                       // the exact spelling wins over the PC's fold to CNN
  ['Daily News; Los Angeles, Calif.', 'Daily News', 'pair'],
];
for (const [t, want, how] of cases) { const x = R(t); ok('“' + t + '” is filed as “' + want + '” (' + how + ')', x.name === want && x.how === how, JSON.stringify(x)); }
{ const x = R('Daily News; New York, N.Y.'); ok('a generic name in another city (Daily News; New York) is not matched to the tracker’s Daily News: kept, flagged', x.how === 'generic' && x.name === 'Daily News', JSON.stringify(x)); }
{ const x = R('Tribune; Chicago, Ill.'); ok('a generic name with no pair (Tribune) is not matched to “Tribune, The”', x.how === 'generic', JSON.stringify(x)); }
{ const x = R('Fresno Brand New Gazette Test; Fresno, Calif.'); ok('a name nothing matches is kept as ProQuest has it, how = unknown (the row gets the Team note)', x.how === 'unknown' && x.name === 'Fresno Brand New Gazette Test', JSON.stringify(x)); }
{ const x = PQ.resolveOutlet('The Center Square', 'Texas', { exact: new Map(), fold: new Map() }); ok('the Center Square pair works with an empty tracker index (it names the sheet’s spelling itself)', x.name === 'Center Square California, The' && x.how === 'pair', JSON.stringify(x)); }
{ const x = PQ.resolveOutlet('Center Square Texas, The', '', idx); ok('the tracker’s own “Center Square Texas, The” is never folded into California', x.name === 'Center Square Texas, The' && x.how === 'tracker', JSON.stringify(x)); }
ok('every pair’s target is an Outlet the sheet uses (rows counted at build time)', T.pairs.every(p => p.tracker_rows > 0 && p.source.length > 40));
console.log(fail ? fail + ' FAILED' : 'all passed'); process.exit(fail ? 1 : 0);
