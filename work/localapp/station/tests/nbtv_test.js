/* NBTV-v1 unit test of src/nbtv.js: a NewsBank broadcast transcript gets the Update button's TV handling.   node tests/nbtv_test.js */
const T = require('../src/nbtv.js');
let fail = 0; const ok = (n, c, x) => { console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -> ' + JSON.stringify(x))); if (!c) fail++; };
const TX = '[01:00:00]\n\nELEX MICHAELSON, CNN ANCHOR: Welcome back. With me now is the author of that bill, California Assemblymember Jesse Gabriel.\n\nJESSE GABRIEL, CALIFORNIA STATE ASSEMBLYMEMBER: Yes, thank you for having me, Elex. It is great to be here.\n\nMICHAELSON: What does the bill do?\n\nGABRIEL: It sets a state definition.\n\n[01:24:00]\n\nMICHAELSON: Thank you.\n\nANCHOR TWO: Next.\n\nMICHAELSON: And more.\n\nMICHAELSON: Done.';
const p = { outlet: 'Story Is with Elex Michaelson, The [CNN] (USA)', headline: 'Apple Unveils First Foldable iPhone At Product Showcase; Trump: $5,000 To All U.S. Adults. Aired 1-2a ET', text: TX, date: '2026-09-10', page: '' };
let d = T.detect(p);
ok('CNN transcript: TV, network CNN, show un-inverted', d && d.medium === 'TV' && d.network === 'CNN' && d.show === 'The Story Is with Elex Michaelson', d);
ok('Pacific date: 1-2a ET on Sep 10 is 22:00 PT on Sep 9 (REVIEW4-v1 F1), source time kept in the note', d.date_pt === '2026-09-09' && d.av['Air/publish date'] === '2026-09-09' && d.av['Air time'] === '22:00 PT' && /source time 2026-09-10 1-2a ET.*Pacific date 2026-09-09/.test(d.note), d);
ok('his role: guest (introduced, labelled turns) -> Featured; his speech -> Quoted', d.role === 'guest' && d.depth === 'Featured' && d.quoted === true && d.av['His role'] === 'guest', d);
ok('an AV row: Broadcast segment, Channel/Network CNN, transcript full, the segment title without "Aired"', d.av['Item type'] === 'Broadcast segment' && d.av.Network === 'CNN' && d.av.Channel === 'CNN' && d.av['Transcript kind'] === 'full' && !/Aired/.test(d.av['Episode/segment title']), d.av);
ok('mention markers are kept as the saved AV row keeps them', d.marks[0] === '01:00:00' && d.av['Mention 1'] === '01:00:00', d.marks);
// evening ET stays on the same Pacific day; PT is unchanged; CT shifts two hours
ok('9-10p ET on Sep 8 is 18:00 PT, same day', (x => x && x.date === '2026-09-08' && x.clock === '18:00 PT')(T.toPacific('2026-09-08', 21 * 60, 'ET')));
ok('winter: 1a ET Jan 10 is 22:00 PT Jan 9 (standard time)', (x => x && x.date === '2026-01-09' && x.clock === '22:00 PT')(T.toPacific('2026-01-10', 60, 'ET')));
ok('PT stays', (x => x && x.date === '2026-09-08' && x.clock === '07:00 PT' && x.shifted === 0)(T.toPacific('2026-09-08', 7 * 60, 'PT')));
// a station: call letters, a newscast with markers, he is only discussed
const p2 = { outlet: 'CBS - 7 WHIO (OH)', headline: 'Evening news. Aired 6-7p ET', date: '2026-09-12', text: 'ANCHOR: Lawmakers in California passed a bill. Assemblymember Jesse Gabriel authored it.\n\n[18:12:00]\n\nREPORTER: More on that.\n\nANCHOR: Next.\n\nANCHOR: Then.\n\nANCHOR: And.\n\nANCHOR: Finally.\n\nANCHOR: Bye.\n\nANCHOR: Done.' };
d = T.detect(p2);
ok('"CBS - 7 WHIO": TV, station WHIO, network CBS; named once in passing: brief mention, not Featured, not Quoted', d && d.medium === 'TV' && d.station === 'WHIO' && d.network === 'CBS' && d.role === 'brief mention' && d.depth === '' && d.quoted === false, d);
ok('6-7p ET Sep 12 is 15:00 PT, the same day', d.date_pt === '2026-09-12' && d.av['Air time'] === '15:00 PT', d);
// NPR is radio
d = T.detect({ outlet: 'Morning Edition [NPR] (USA)', headline: 'Food policy', date: '2026-09-11', text: 'A short summary of the segment.' });
ok('"Morning Edition [NPR]": Radio, Broadcast segment, no date change without an air time, and a note says so', d && d.medium === 'Radio' && d.av['Item type'] === 'Broadcast segment' && d.date_pt === '2026-09-11' && /air time not given/.test(d.note), d);
// newspapers and wires are not broadcast
ok('a newspaper is not a transcript', T.detect({ outlet: 'Bakersfield Californian, The: Web Edition Articles (CA)', headline: 'Tributes abound', text: 'A long story. '.repeat(50), date: '2026-10-28' }) === null);
ok('KFF Health News is not a station', T.detect({ outlet: 'KFF Health News', headline: 'x', text: 'Gabriel said the bill passed.', date: '2026-10-28' }) === null);
ok('a print page is never a transcript', T.detect({ outlet: 'Story [CNN]', headline: 'x', text: '', date: '2026-10-28', page: '12' }) === null);
ok('an AP story on the wire is not broadcast', T.detect({ outlet: 'Associated Press News Service, The', headline: 'New laws', text: 'LOS ANGELES (AP) — Jewish heirs filed suits.', date: '2026-09-19' }) === null);
console.log(fail ? fail + ' FAILED' : 'all passed'); process.exit(fail ? 1 : 0);
