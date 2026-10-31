// LATEWINDOW-v1 (REQ-1): reprint headline searches keep the late-pickup window: after_date is the item's own minDate when that is
// earlier than U.since (tfPlan gives reprint items minDate = the story's date, up to RC_LATE_DAYS before since).
// Source-line test, no page needed.   Run: node build/tests/update_js/test_late_window_js.js
const fs = require('fs'), path = require('path');
const L = process.env.L_ROOT || path.resolve(__dirname, '..', '..', '..'), s41 = fs.readFileSync(path.join(L, 'code', 'tracker', '41_update_search.js'), 'utf8');
let n = 0; const ok = (c, m) => { if (!c) { console.log('FAIL ' + m); process.exit(1); } n++; console.log('PASS ' + m); };
const lines = s41.split('\n').filter(l => /^\s*const inp = Object\.assign\(/.test(l)); ok(lines.length === 1, 'exactly one `const inp = Object.assign(` line');
const src = lines[0].trim().replace(/^const inp = /, '');
const run = (U, it) => { return eval(src); };
const U = { since: '2026-10-20' };
ok(run(U, { minDate: '2026-10-01', query: '"x y z"' }).after_date === '2026-10-01', 'minDate before since -> after_date = minDate (late window open)');
ok(run(U, { query: '"x"' }).after_date === '2026-10-20', 'no minDate -> after_date = since');
ok(run(U, { minDate: '2026-10-25' }).after_date === '2026-10-20', 'minDate after since -> after_date = since');
ok(run(U, { minDate: '2026-10-01', after_date: '2026-09-01' }).after_date === '2026-09-01', 'an explicit after_date on the item (release pickups) still wins');
ok(run(U, { query: 'q' }).location === 'US' && /Jesse Gabriel/.test(run(U, { query: 'q' }).purpose), 'location and purpose unchanged');
ok(/Object\.assign\(\{ minDate: r\.date \}, RC_LONGTAIL/.test(s41) && /D\.filter\(r => r\.date >= late/.test(s41), 'the reprint plan line still carries minDate: r.date');
ok(/delete inp\.minDate/.test(s41), 'minDate is still stripped before the call (TinyFish never sees it)');
console.log('ALL ' + n + ' CHECKS PASSED');
