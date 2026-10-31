/* REVIEW4-PAGE-v1 (DECISIONS REVIEW4-v1 F1/F2): one way to show a broadcast / audio time. Dates are the Pacific date; the source's own
   time (e.g. NewsBank's ET) is kept in the details; a mention's clock time is computed (airing start + offset) and marked "about". */
const AVT_PT = { PT: 0, CT: -120, ET: -180 };   /* minutes to add to a zone's clock to get Pacific */
function avtParseAir(s){
  s = String(s || '').trim(); let m;
  if ((m = s.match(/^(\d{1,2})(?::(\d{2}))?\s*[-–]\s*(\d{1,2})(?::(\d{2}))?\s*([ap])\s*(ET|PT|CT)$/i))){
    const ap = m[5].toLowerCase(), z = m[6].toUpperCase(), e = (+m[3] % 12 + (ap === 'p' ? 12 : 0)) * 60 + (+m[4] || 0);
    let b = (+m[1] % 12 + (ap === 'p' ? 12 : 0)) * 60 + (+m[2] || 0), e2 = e; if (b >= e2) b -= 720; if (b < 0){ b += 1440; e2 += 1440; }
    return { z, b, e: e2, range: true }; }
  if ((m = s.match(/^(\d{1,2}):(\d{2})\s*(ET|PT|CT)$/i))) return { z: m[3].toUpperCase(), b: +m[1] * 60 + +m[2], e: null, range: false };
  return null;
}
function avtClock(min){ min = ((Math.round(min) % 1440) + 1440) % 1440; const h = Math.floor(min / 60), m = min % 60, ap = h < 12 ? 'am' : 'pm', h12 = h % 12 || 12; return m ? `${h12}:${String(m).padStart(2, '0')}${ap}` : `${h12}${ap}`; }
function avtSecs(t){ const p = String(t || '').trim().match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/); if (!p) return null; return p[3] != null ? (+p[1] * 3600 + +p[2] * 60 + +p[3]) : (+p[1] * 60 + +p[2]); }
function avtIn(sec){ const h = Math.floor(sec / 3600), m = Math.floor(sec % 3600 / 60); return h ? `${h}h ${m}m in` : m ? `${m}m in` : 'under 1m in'; }
/* r -> { label, date (Pacific ISO), when (display), src (the source's own date/time, '' when the same), ments: [html-safe text] } */
function avtInfo(r){
  const a = r && r.av; if (!a || a.type === 'Web story') return null;
  const label = a.type === 'Episode' ? 'Published' : a.type === 'Video clip' ? 'Posted' : 'Aired', iso = a.air || r.date || '', pa = avtParseAir(a.airtime);
  const out = { label, date: iso, when: '', src: '', ments: [] };
  let toPT = 0, shift = 0, dayIso = iso;
  if (pa && /^\d{4}-\d{2}-\d{2}$/.test(iso)){
    toPT = AVT_PT[pa.z] || 0; const bPT = pa.b + toPT;
    if (r.date === a.air) { shift = Math.floor(bPT / 1440); dayIso = addDays(iso, shift); }   /* the row still carries the source's date; a re-dated row (Pacific) is left alone */
    const bp = ((bPT % 1440) + 1440) % 1440, ep = pa.e != null ? pa.e + toPT : null;
    out.date = dayIso; out.when = pa.range ? `${avtClock(bp)}–${avtClock(ep)} PT`.replace(/(am|pm)–(\d{1,2}(?::\d{2})?)\1/, '–$2$1') : `from ${avtClock(bp)} PT`;
    if (pa.z !== 'PT'){ const sm = pa.range ? `${avtClock(pa.b)}–${avtClock(pa.e)}` : avtClock(pa.b); out.src = `${dateLabel({ date: iso, prec: 'day' })}, ${sm} ${pa.z}`.replace(/(am|pm)–(\d{1,2}(?::\d{2})?)\1/, '–$2$1'); }
  }
  const bPTd = pa ? Math.floor((pa.b + toPT) / 1440) : 0, clockBasis = /^transcript time marker/.test(a.tbasis || '');
  [a.m1, a.m2, a.m3, a.m4, a.m5].filter(Boolean).forEach(m => {
    const s = avtSecs(m); if (s == null){ out.ments.push(String(m)); return; }
    if (clockBasis && pa){   /* a wall-clock marker in the source's zone */
      let min = s / 60; if (min < pa.b - 30) min += 1440; const inSec = Math.max(0, Math.round((min - pa.b) * 60)), pt = min + toPT;
      out.ments.push(`about ${avtClock(pt)} PT${Math.floor(pt / 1440) > bPTd ? ' the next day' : ''}, ${avtIn(inSec)}${pa.z !== 'PT' ? ` (${avtClock(min)} ${pa.z} in the source)` : ''}`);
    } else if (!clockBasis && pa && !pa.range){
      const pt = pa.b + toPT + s / 60; out.ments.push(`about ${avtClock(pt)} PT, ${avtIn(s)}${pt >= 1440 ? ' (after midnight)' : ''}`);
    } else if (!clockBasis) out.ments.push(avtIn(s));
    else out.ments.push(String(m));
  });
  return out;
}
/* one line for the spreadsheet copy / CSV: Pacific date, then the airing time */
function avtLine(r){ const i = avtInfo(r); return i ? [i.date, i.when].filter(Boolean).join(' ') : ''; }

/* REVIEW4-PAGE-v1 A7: exports list the publisher's (or archive) link first; a library-login link is labelled and never the raw infoweb form */
function exportLinkSets(r){ const ls = linksOf(r); return { open: ls.filter(p => p[0] === 'pub' || p[0] === 'tv').map(p => p[1]), lib: ls.filter(p => p[0] !== 'pub' && p[0] !== 'tv').map(p => p[1]) }; }
function exportLinkBest(r){ const s = exportLinkSets(r); return s.open[0] || s.lib[0] || r.plink || r.link || ''; }
function exportLibLink(r){ const s = exportLinkSets(r); return s.open.length ? (s.lib[0] || '') : ''; }
function exportLinkText(r){ const s = exportLinkSets(r), out = []; if (s.open[0]) out.push(s.open[0]); if (s.lib[0]) out.push(s.lib[0] + ' (library login)');
  return '\n' + (out.length ? out.join('\n') : (r.plink || r.link || '')); }

/* REVIEW4-PAGE-v1 E12: saved-copy viewer touch-ups (the saved files stay as they are): no internal PDF file name, a readable save date
   instead of a bare ISO date above an old story, and a note that Internet Archive captions are raw */
function viewFix(html, r){
  if (!html) return html; let h = String(html);
  h = h.replace(/(Text of the (?:NewsBank|ProQuest) PDF) \([^()]*?\.pdf(, item \d+)?\)/i, (m, a, b) => b ? `${a} (item ${b.replace(/\D/g, '')})` : a);
  h = h.replace(/<div>Saved (\d{4})-(\d{2})-(\d{2})<\/div>/, (m, y, mo, d) => `<div>Copy saved ${MONTHS[+mo - 1]} ${+d}, ${y}</div>`);
  const a = r && r.av;
  if (a && a.type === 'Broadcast segment' && a.larchive && /<h1[ >]/i.test(h)) h = h.replace(/(<\/h1>)/i, '$1<p><i>Transcript from the Internet Archive’s automatic captions: lowercase, no punctuation, and may contain errors.</i></p>');
  return h;
}
