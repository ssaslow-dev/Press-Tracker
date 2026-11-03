/* NBTV-v1: a NewsBank (or ProQuest) BROADCAST TRANSCRIPT ("Story Is with Elex Michaelson, The [CNN] (USA)", "CBS - 7 WHIO", a station's call letters,
   speaker labels, "[01:00:00]" markers, "Aired 1-2a ET") gets the same handling as the Update button's TV finds and as the save program gives a TV row:
     Medium TV (Radio for NPR and AM/FM stations), Format "Broadcast segment", an Audio & video row (`_av`), the PACIFIC air date (REVIEW4-v1 F1: the source's own
     time is kept in the note), his role from the transcript (REVIEW4-v1 F3: a guest is Featured; F4: his transcribed speech is Quoted).
   Pure functions, no DOM. A port of code/avtab.py (station_network, is_transcript, transcript_details, to_pacific, role_depth, spoken_quoted); the page's own
   avtParseAir (tracker 25_avtime.js) reads the same "1-2a ET" air-time form for display, so what is written here shows the way a TV find already does.
   Used by the Update station page (inlined, as NBTV) and by the node tests. */
(function (root) {
'use strict';
const squash = s => String(s == null ? '' : s).replace(/\s+/g, ' ').trim();
const NETWORKS = ['Telemundo', 'Univision', 'Spectrum News', 'Fox News', 'CNN', 'MSNBC', 'NPR', 'PBS', 'ABC', 'CBS', 'NBC', 'FOX', 'MyNetworkTV', 'KCAL', 'CW', 'Bloomberg', 'C-SPAN', 'BBC', 'CBC', 'Al Jazeera', 'NewsNation', 'Newsmax', 'Fox Business', 'CNBC'];
const RADIO_NETS = new Set(['npr', 'bbc', 'cbc']);
const canonNet = n => { const k = squash(n).toLowerCase(); return NETWORKS.find(x => x.toLowerCase() === k) || squash(n); };
const CALL = /(?<![A-Za-z])([KW][A-Z]{2,3})(?:-(?:TV|FM|AM|DT|CD|LD))?(?![A-Za-z])/g;
const NOT_CALL = new Set(['WITH', 'WEST', 'WEEK', 'WHAT', 'WHEN', 'WIDE', 'WAR', 'WAY', 'WHO S', 'KIDS', 'KEY', 'KING', 'WALL', 'WORLD', 'WIRE', 'WEB', 'WSJ', 'KFF', 'WNBA', 'WIRED', 'KQED', 'KCRW', 'KPCC']);   /* + names that are not television call letters */
const NETRX = new RegExp('\\b(' + NETWORKS.slice().sort((a, b) => b.length - a.length).map(x => x.replace(/[.*+?^${}()|[\]\\-]/g, '\\$&')).join('|') + ')', 'i');

/* ('KTVU', 'FOX') from 'KTVU FOX 2' / 'CBS - 7 WHIO' / 'Story Is ..., The [CNN]' */
function stationNetwork(outlet) {
  const o = squash(outlet); let st = '', net = '', m;
  if ((m = /\[([^\]]+)\]\s*(?:\([^)]*\))?\s*$/.exec(o))) net = canonNet(m[1]);
  if ((m = /^([A-Za-z]+) - \d+ ([KW][A-Z]{2,3})\b/.exec(o))) { net = net || canonNet(m[1]); st = st || m[2]; }
  if (!st) { for (const c of [...o.matchAll(CALL)].map(x => x[1])) if (!NOT_CALL.has(c)) { st = c; break; } }
  if (!net) { const m2 = NETRX.exec(o.replace(/\[.*?\]/g, '')); if (m2 && (m2.index === 0 || o.slice(0, m2.index).trim().toUpperCase() === st)) net = canonNet(m2[1]); }
  return { station: st, network: net };
}
/* broadcast / podcast transcript: speaker labels or time markers (avtab.is_transcript) */
function isTranscript(text) {
  const t = String(text || '');
  const up = (t.match(/^[ \t]*[A-Z][A-Z .'\-]{2,40}(?:,\s*[A-Z0-9 .,'()&/\-]{2,80})?:\s/gm) || []).length;
  const mixed = (t.match(/^[ \t]*[A-Z][a-z]+(?: [A-Z][a-z'\-]+){1,2}:\s/gm) || []).length;
  const marks = (t.match(/\[\d{1,2}:\d{2}:\d{2}\]/g) || []).length;
  return up >= 6 || marks >= 2 || (mixed >= 10 && /transcript/i.test(t.slice(0, 3000)));
}
const AIRED = /\bAired\s+([\d:\-\u2013apmAPM ]+(?:ET|PT|CT))\b/;
/* "1-2a ET" -> { z: 'ET', start: 60 (minutes after midnight, in z), range: '1-2a ET' } (the page's avtParseAir reads the same text) */
function parseAir(s) {
  s = squash(s); let m;
  if ((m = /^(\d{1,2})(?::(\d{2}))?\s*[-\u2013]\s*(\d{1,2})(?::(\d{2}))?\s*([ap])\s*(ET|PT|CT)$/i.exec(s))) {
    const ap = m[5].toLowerCase(), e = ((+m[3]) % 12 + (ap === 'p' ? 12 : 0)) * 60 + (+m[4] || 0); let b = ((+m[1]) % 12 + (ap === 'p' ? 12 : 0)) * 60 + (+m[2] || 0);
    if (b >= e) b -= 720; if (b < 0) b += 1440;
    return { z: m[6].toUpperCase(), start: b, text: s };
  }
  if ((m = /^(\d{1,2}):(\d{2})\s*(ET|PT|CT)$/i.exec(s))) return { z: m[3].toUpperCase(), start: +m[1] * 60 + +m[2], text: s };
  return null;
}
const ZONE = { ET: 'America/New_York', CT: 'America/Chicago', MT: 'America/Denver', PT: 'America/Los_Angeles' };
/* the Pacific date and clock of a wall-clock time in another US zone (avtab.to_pacific): -> { date, clock ('22:00 PT'), shifted: days } or null */
function toPacific(date, startMin, z) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(date || '')); const zone = ZONE[z]; if (!m || !zone) return null;
  const wall = Date.UTC(+m[1], +m[2] - 1, +m[3], 0, 0) + startMin * 60000;
  const off = (ms, tz) => { const p = new Intl.DateTimeFormat('en-US', { timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }).formatToParts(new Date(ms)).reduce((a, x) => (a[x.type] = x.value, a), {});
    return Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute, +p.second) - ms; };
  let utc = wall - off(wall, zone); utc = wall - off(utc, zone);   /* twice: the offset at the instant, not at the wall time */
  const o2 = off(utc, ZONE.PT), l = new Date(utc + o2), p2 = n => String(n).padStart(2, '0');
  const d = l.getUTCFullYear() + '-' + p2(l.getUTCMonth() + 1) + '-' + p2(l.getUTCDate());
  return { date: d, clock: p2(l.getUTCHours()) + ':' + p2(l.getUTCMinutes()) + ' PT', shifted: Math.round((Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10)) - Date.UTC(+m[1], +m[2] - 1, +m[3])) / 864e5) };
}
const STAFF = /\b(anchor|host|co-host|correspondent|reporter|contributor|analyst|meteorologist|producer|commentator|moderator|announcer|chief|editor|bureau)\b/i;
/* a speaker label starts a line, or (PDF text runs paragraphs together) follows the end of a sentence */
const UPLABEL = /(?:^[ \t]*|(?<=[.?!"\u201d)]\s+))([A-Z][A-Z .'\-]{2,40})(?:,\s*([A-Z0-9 .,'()&/\-]{2,90}))?:(?=\s)/gm;
const GAB = /\bGabriel\b/i;
/* his role from a speaker-labelled transcript (avtab.transcript_details): '' | 'guest' | 'interviewed' | 'soundbite' | 'discussed' | 'brief mention', his labelled turns, the clock markers before his mentions */
function transcriptRole(text) {
  const t = String(text || ''), labels = [...t.matchAll(UPLABEL)];
  const his = labels.filter(m => /\bGABRIEL\b/i.test(m[1])), mentions = [...t.matchAll(/\bGabriel\b/gi)].map(m => m.index);
  const named = mentions.filter(p => !his.some(m => m.index <= p && p < m.index + m[0].length));
  let role = '';
  if (his.length) { const first = his[0].index, intro = t.slice(Math.max(0, first - 600), first);
    role = /(joining (me|us)|joins (me|us)|with (me|us) now|welcome|good to have you|thank(s| you) for (being|joining|coming))/i.test(intro) ? 'guest' : his.length >= 3 ? 'interviewed' : 'soundbite'; }
  else if (named.length >= 2) role = 'discussed'; else if (named.length === 1) role = 'brief mention';
  const marks = [...t.matchAll(/\[(\d{1,2}:\d{2}:\d{2})\]/g)].map(m => [m.index, m[1]]), ts = [];
  [...his.map(m => m.index), ...named].forEach(p => { const prev = marks.filter(x => x[0] <= p); if (prev.length && !ts.includes(prev[prev.length - 1][1])) ts.push(prev[prev.length - 1][1]); });
  ts.sort();
  return { role, turns: his.length, marks: ts };
}
/* REVIEW4-v1 F3 / F4 */
const roleDepth = role => role === 'guest' || role === 'moderator' ? 'Featured' : '';
function spokenQuoted(role, text) {
  if (['discussed', 'brief mention', ''].includes(role)) return false;
  return /(?:^[ \t]*|(?<=[.?!"\u201d)]\s+))(?:ASM(?:BLY)?\.?\s+|ASSEMBLY(?:MAN|MEMBER)\s+)?(?:JESSE\s+)?GABRIEL(?:,[^:\n]{0,60})?:\s/m.test(String(text || '')) || (['guest', 'interviewed', 'moderator'].includes(role) && /\bGABRIEL\b/i.test(text) && isTranscript(text));
}
/* "Story Is with Elex Michaelson, The [CNN] (USA)" -> "The Story Is with Elex Michaelson" (SHOWNET-v1: un-inverted) */
function showOf(outlet) {
  let o = squash(outlet).replace(/\s*\([^)]*\)\s*$/, '').replace(/\s*\[[^\]]*\]\s*$/, '').trim(); if (!o) return '';
  const m = /^(.*\S),\s*(The|A|An)$/i.exec(o); if (m) o = m[2] + ' ' + m[1]; return o;
}

/* is this record a broadcast transcript? p: { outlet (NewsBank's source line), headline, text, page, date }.  -> null | the handling */
function detect(p) {
  if (!p || p.page) return null;
  const src = squash(p.outlet), hl = squash(p.headline), text = String(p.text || '');
  const sn = stationNetwork(src), bracket = /\[([^\]]+)\]/.exec(src), bnet = bracket ? NETWORKS.find(x => x.toLowerCase() === squash(bracket[1]).toLowerCase()) : '';
  const stationForm = /^[A-Za-z]+ - \d+ [KW][A-Z]{2,3}\b/.test(src);
  const tr = isTranscript(text) || AIRED.test(hl) || /\((?:BEGIN|END) (?:VIDEO CLIP|VIDEOTAPE|AUDIO CLIP)\)/i.test(text);
  const strong = !!bnet || stationForm;
  if (!(strong || ((sn.station || sn.network) && tr))) return null;
  const radio = RADIO_NETS.has(String(sn.network).toLowerCase()) || /\b(AM|FM)\b|\bradio\b/i.test(src) || /\b\d{2,3}\.\d\b/.test(src);
  const medium = radio ? 'Radio' : 'TV';
  const aired = AIRED.exec(hl), air = aired ? parseAir(aired[1]) : null;
  let date = String(p.date || '').slice(0, 10), pt = null, note = '';
  if (air && /^\d{4}-\d{2}-\d{2}$/.test(date)) { pt = toPacific(date, air.start, air.z); }
  if (pt) note = 'source time ' + date + ' ' + air.text + (pt.date !== date ? '; Pacific date ' + pt.date + ' (REVIEW4-v1 F1)' : '; same day in Pacific');
  else note = (air ? 'air time not converted (no date)' : 'air time not given: the date is NewsBank’s; check the Pacific air date (REVIEW4-v1 F1)');
  const rd = tr ? transcriptRole(text) : { role: '', turns: 0, marks: [] };
  const depth = roleDepth(rd.role), quoted = tr && spokenQuoted(rd.role, text);
  const show = showOf(src), title = squash(hl.replace(/\.?\s*Aired\s+[\d:\-\u2013apmAPM ]+(?:ET|PT|CT)\.?\s*$/, ''));
  return { medium, network: sn.network, station: sn.station, show, role: rd.role, depth, quoted, transcript: tr, date_src: date, date_pt: pt ? pt.date : date, air_clock: pt ? pt.clock : '', air_text: air ? air.text : '', note, title,
    marks: rd.marks,
    av: Object.assign({ 'Item type': 'Broadcast segment', 'Episode/segment title': title.slice(0, 300), 'Air/publish date': pt ? pt.date : '', 'His role': rd.role, 'Details from': 'NewsBank transcript' },
      sn.network ? { Network: sn.network, Channel: sn.network } : {}, sn.station ? { Station: sn.station } : {}, show && show.toLowerCase() !== String(sn.network).toLowerCase() ? { 'Show/program': show } : {},
      pt ? { 'Air time': pt.clock } : {}, tr ? { 'Transcript kind': 'full' } : {}, rd.marks.length ? Object.assign({ 'Timestamp basis': 'transcript time marker before the mention' }, ...rd.marks.slice(0, 5).map((m, i) => ({ ['Mention ' + (i + 1)]: m }))) : {},
      note ? { Notes: note.slice(0, 400) } : {}) };
}
const api = { detect, stationNetwork, isTranscript, parseAir, toPacific, transcriptRole, roleDepth, spokenQuoted, showOf };
if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.NBTV = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
