/* PRINTREAD-v2 tile fix: the tiles sent to Claude must be cut from the page picture itself.
   Real batch (licensed, scratchpad only): AJG_REAL_NB4 = folder with multi4.pdf and for_update_0bccc1fc.json; AJG_TILE_OUT = where the tiles are dumped (optional).
   The source pictures are taken out of the PDF by a separate program (extract_pictures.py, pypdf), not by the station code.
   For every print page read: (1) the tiles placed back at their offsets reproduce the embedded JPEG (mean absolute difference < 3 over the whole picture, and every pixel covered);
   (2) no tile is near-blank where the source region has content (tile mean/stddev match the source region's); (3) East Bay Times p.18: its top-left tile has dark print (stddev > 30).
   Claude is a fake here (the reading is not under test). */
const fs = require('fs'), path = require('path'), cp = require('child_process');
const H = require('../nb/real_harness.js');
const DIR = process.env.AJG_REAL_NB4, FU = DIR && path.join(DIR, 'for_update_0bccc1fc.json');
if (!DIR || !fs.existsSync(path.join(DIR, 'multi4.pdf')) || !fs.existsSync(FU)) { console.log('SKIP tilefix/tile_test (AJG_REAL_NB4 not set or files absent)'); process.exit(0); }
const OUT = process.env.AJG_TILE_OUT || fs.mkdtempSync(path.join(require('os').tmpdir(), 'tiles-'));
const PAGE = path.join(H.ST, 'dist', 'index.html'), C = H.makeChecker(), check = C.check;
const PICS = path.join(OUT, '_source_pictures');
cp.execFileSync('python3', ['-I', path.join(__dirname, 'extract_pictures.py'), path.join(DIR, 'multi4.pdf'), PICS], { stdio: 'inherit' });
const pics = fs.readdirSync(PICS).filter(f => /\.jpg$/.test(f)).map(f => ({ f, b64: fs.readFileSync(path.join(PICS, f)).toString('base64') }));
const stub = (prompt, o) => {
  if (/^These items come from NewsBank/.test(prompt)) return [...prompt.matchAll(/=== ITEM (\d+)\n/g)].map(m => ({ n: +m[1], keep: true, why: 'x', press_release: 'no', pr_why: 'x', date: '', outlet: '', pub: '', hl: '', topic: 'Food safety', tone: 'Neutral', tone_why: 'x' }));
  if (!/^You are reading a scanned page/.test(prompt)) return [];
  const m = /Outlet: (.*?)\. Date: (\d{4}-\d{2}-\d{2})\. Page: (.*?)\.\n/.exec(prompt);
  (window.__tilesSeen = window.__tilesSeen || []).push({ label: m ? m[1] + '|' + m[2] + '|p' + m[3] : 'page', blobs: o.images.slice(), tiles: o.images.tiles, grid: o.images.grid });
  return { readable: false, articles: [] };
};
(async () => {
  const X = await H.start(PAGE, stub, { images: 8 }), page = X.page;
  await H.loadFile(page, FU); await H.dropPdf(page, path.join(DIR, 'multi4.pdf')); await page.uncheck('#nbLinks').catch(() => {});
  await page.click('#nbAdd'); await page.waitForFunction(() => window.__station.state.nb.lastRun, null, { timeout: 300000 });
  const res = await page.evaluate(async pics => {
    const px = async blobOrBytes => { const bmp = await createImageBitmap(blobOrBytes, { imageOrientation: 'none' }); const c = document.createElement('canvas'); c.width = bmp.width; c.height = bmp.height; const x = c.getContext('2d'); x.drawImage(bmp, 0, 0); return { w: bmp.width, h: bmp.height, d: x.getImageData(0, 0, bmp.width, bmp.height).data }; };
    const srcs = []; for (const p of pics) { const bin = atob(p.b64), u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); const im = await px(new Blob([u], { type: 'image/jpeg' })); srcs.push({ f: p.f, ...im }); }
    const lum = (d, i) => 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2];
    const stats = (d, W, x0, y0, w, h) => { let s = 0, s2 = 0, n = 0; for (let y = y0; y < y0 + h; y += 2) for (let x = x0; x < x0 + w; x += 2) { const v = lum(d, (y * W + x) * 4); s += v; s2 += v * v; n++; } const m = s / n; return { mean: m, sd: Math.sqrt(Math.max(0, s2 / n - m * m)) }; };
    const out = [];
    for (const r of window.__tilesSeen) {
      const g = r.grid, src = srcs.find(s => s.w === g.w && s.h === g.h && !s.used) ; // same size; best match chosen below
      const cands = srcs.filter(s => s.w === g.w && s.h === g.h);
      const tiles = []; for (let i = 0; i < r.blobs.length; i++) { const im = await px(r.blobs[i]); const b = new Uint8Array(await r.blobs[i].arrayBuffer()); let bs = ''; for (let k = 0; k < b.length; k += 8192) bs += String.fromCharCode.apply(null, b.subarray(k, k + 8192)); tiles.push({ ...im, t: r.tiles[i], b64: btoa(bs) }); }
      let best = null;
      for (const s of cands) {
        const cov = new Uint8Array(s.w * s.h); let sum = 0, n = 0, bad = 0; const tstat = [];
        tiles.forEach((t, i) => {
          const wide = t.w === t.t.w && t.h === t.t.h; let ts = 0, tn = 0;
          if (wide) for (let y = 0; y < t.h; y += 2) for (let x = 0; x < t.w; x += 2) { const si = ((t.t.y + y) * s.w + t.t.x + x) * 4, ti = (y * t.w + x) * 4; ts += (Math.abs(s.d[si] - t.d[ti]) + Math.abs(s.d[si + 1] - t.d[ti + 1]) + Math.abs(s.d[si + 2] - t.d[ti + 2])) / 3; tn++; }
          sum += ts; n += tn;
          for (let y = 0; y < t.t.h; y++) cov.fill(1, (t.t.y + y) * s.w + t.t.x, (t.t.y + y) * s.w + t.t.x + t.t.w);
          tstat.push({ wide, mad: tn ? ts / tn : 999, src: stats(s.d, s.w, t.t.x, t.t.y, t.t.w, t.t.h), tile: stats(t.d, t.w, 0, 0, t.w, t.h) });
        });
        const uncovered = cov.reduce((a, v) => a + (v ? 0 : 1), 0);
        if (!best || sum / n < best.mad) best = { f: s.f, mad: n ? sum / n : 999, uncovered, tstat };
      }
      out.push({ label: r.label, grid: g, best, tiles: tiles.map(t => ({ b64: t.b64, w: t.w, h: t.h, x: t.t.x, y: t.t.y })) });
    }
    return out;
  }, pics);
  let k = 0; const report = [];
  for (const r of res) {
    k++; const dir = path.join(OUT, String(k).padStart(2, '0') + '_' + r.label.replace(/[^\w|-]+/g, '_').replace(/\|/g, '_')); fs.mkdirSync(dir, { recursive: true });
    r.tiles.forEach((t, i) => fs.writeFileSync(path.join(dir, 't' + (i + 1) + '.jpg'), Buffer.from(t.b64, 'base64')));
    const b = r.best;
    report.push([r.label, r.grid.cols + 'x' + r.grid.rows, r.grid.w + 'x' + r.grid.h, 'tile ' + r.grid.tile_w + 'x' + r.grid.tile_h, 'from=' + r.grid.from, b ? 'src=' + b.f + ' mad=' + b.mad.toFixed(2) : 'NO SOURCE'].join('  '));
    check(r.label + ': the picture used is one of the PDF’s own (found by size), cut from the picture (not a drawing)', !!b && r.grid.from === 'picture', JSON.stringify(r.grid));
    if (!b) continue;
    check(r.label + ': (1) tiles placed at their offsets reproduce the embedded JPEG: mean abs diff ' + b.mad.toFixed(2) + ' < 3, whole picture covered', b.mad < 3 && b.uncovered === 0, 'uncovered=' + b.uncovered);
    const blank = b.tstat.map((t, i) => [i + 1, t]).filter(([, t]) => (t.src.sd > 12 && t.tile.sd < t.src.sd * 0.7) || Math.abs(t.tile.mean - t.src.mean) > 8);
    check(r.label + ': (2) every tile matches its source region (no blank tile where the picture has print)', blank.length === 0, JSON.stringify(blank.map(([i, t]) => [i, t.src, t.tile])));
    r.stats = b.tstat;
  }
  console.log(report.join('\n'));
  const ebt = res.find(r => /East Bay Times\|2026-11-01\|p18/.test(r.label));
  check('(3) East Bay Times p.18 was read', !!ebt, res.map(r => r.label).join('; '));
  if (ebt && ebt.best) { const t0 = ebt.best.tstat[0]; check('(3) East Bay Times p.18: the top-left tile holds dark print (stddev ' + t0.tile.sd.toFixed(1) + ' > 30)', t0.tile.sd > 30 && t0.src.sd > 30, JSON.stringify(t0)); }
  check('11 distinct page pictures were cut (14 pages; byte-identical pictures read once, PRINTFIX 7)', res.length === 11, String(res.length));
  console.log('tiles written to ' + OUT);
  check('no page error, no outside request', X.errors.length === 0 && X.outside.length === 0, JSON.stringify([X.errors.slice(0, 3), X.outside]));
  await X.close(); console.log(C.failed ? C.failed + ' FAILED' : 'all ' + C.n + ' passed'); process.exit(C.failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
