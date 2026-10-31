#!/usr/bin/env python3
"""patch_reorg.py - REORG-v1 + PHONE-v1 (agent-reorg, 2026-10-27): Phase 1 of the Data / Press desk reorganization.

  python3 -I code/patch_reorg.py --js build/js_merged.js --views build/insights

Idempotent (every edit is skipped when its result is already there; blocks are refreshed only when their source file
changed). apply_all_patches.py runs it as step 4j, after 4i.
  tracker JS: anchored edits (Home 30-day line + one negative list + Tone line, no "new since" card; Data: toneMix options,
              title "Data", bills split by session, people-only reporter line, cut renders, hash #data / #press-desk),
              the REORG-v1 block (code/reorg_tracker.js) before the boot section. PHONE-v1 (code/reorg_phone.js) is retired
              (NOPHONE-v1, Sammy 2026-10-27 "Drop phone layout"): removed from the JS when present, never installed.
  views:      reporters.js := code/reorg_pitch.js (Press desk > Pitch) when it is the v16 reporter list or already Pitch;
              release_pickup.js: before/after baseline for "original coverage"; story_travel.js: "Where it ran" -> "Map of pickups".
A missing view file is reported and skipped (apply_all --check works on a copy without build/insights).
"""
import argparse, hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BOOT = '/* ---------- boot ---------- */'
BLOCKS = [('reorg_tracker.js', '/* ---------- REORG-v1 (agent-reorg', '/* ---------- /REORG-v1 ---------- */')]
# NOPHONE-v1 (Sammy 2026-10-27 "Drop phone layout"): the PHONE-v1 block (code/reorg_phone.js) is no longer installed and is
# removed from the tracker JS when present, so phones get the v16 header and top tabs back. Pitch's 25-row phone cap stays
# (it is part of Pitch, code/reorg_pitch.js).
RETIRED = [('/* ---------- PHONE-v1 (agent-reorg', '/* ---------- /PHONE-v1 ---------- */')]

JS_EDITS = [
    # toneMix: options {bars:false} (no per-tone bars) and {watch:false} (no "Latest negative coverage" list)
    ("function toneMix(el, capEl, rows, scope){",
     "function toneMix(el, capEl, rows, scope, o){ o = o || {};  /* REORG-v1: o.bars / o.watch === false drop the bars / the negative list */"),
    ("  return { rated: tr.length, pos, neg };\n}",
     "  if (o.bars === false){ const x = el.querySelector('.tm-a .hbars'); if (x) x.remove(); }\n"
     "  if (o.watch === false){ const x = el.querySelector('.watch'); if (x) x.remove(); }\n"
     "  return { rated: tr.length, pos, neg };\n}"),
    # Home: one negative list (very negative + negative), linking to Story travel; very positive stays its own line
    ("  const toned = [['Very negative','bad','very negative'],['Negative','bad','negative'],['Very positive','ok','very positive']].map(([t,c,l]) => [t, c, l, D.filter(r => r.prec==='day' && r.date > addDays(TODAY,-30) && r.tone===t).sort((a,b) => b.date.localeCompare(a.date))]);",
     "  const toned = [[['Very negative','Negative'],'bad','negative'],[['Very positive'],'ok','very positive']].map(([t,c,l]) => [t, c, l, D.filter(r => r.prec==='day' && r.date > addDays(TODAY,-30) && t.includes(r.tone)).sort((a,b) => b.date.localeCompare(a.date))]);  /* REORG-v1: one negative list on Home */"),
    ("`<div class=\"clip-list attn-list\">${rs.map(r => clipItem(r)).join(\"\")}</div>`]); });",
     "`<div class=\"clip-list attn-list\">${rs.map(r => c === 'bad' ? reorgAttnItem(r) : clipItem(r)).join(\"\")}</div>`]); });  /* REORG-v1 */"),
    # Home tone: one line plus the bar
    ("  if (r90.some(rated)) toneMix($('#toneMix'), $('#toneCap'), r90, ' in the last 90 days');\n"
     "  else toneMix($('#toneMix'), $('#toneCap'), D, ', all dates (none from the last 90 days are rated yet)');",
     "  if (r90.some(rated)) toneMix($('#toneMix'), $('#toneCap'), r90, ' in the last 90 days', { bars: false, watch: false });  /* REORG-v1 */\n"
     "  else toneMix($('#toneMix'), $('#toneCap'), D, ', all dates (none from the last 90 days are rated yet)', { bars: false, watch: false });"),
    # Data: title, tone without the list, the REORG extras
    ("  $('#rpTitle').textContent = `Report: ${per.charAt(0).toUpperCase()+per.slice(1)}`;",
     "  $('#rpTitle').textContent = `Data: ${per.charAt(0).toUpperCase()+per.slice(1)}`;  /* REORG-v1: the tab keeps the name Data */"),
    ("  toneMix($('#rpTone'), $('#rpToneCap'), rows, ' in this period');",
     "  toneMix($('#rpTone'), $('#rpToneCap'), rows, ' in this period', { watch: false }); reorgReport(rows);  /* REORG-v1 */"),
    # Data: bill numbers reused across sessions are one bill per session (AB 787 2021-22 vs 2023-24)
    ("  const bills = new Map(); rows.forEach(r => r.bills.forEach(b => (bills.get(b) || bills.set(b, []).get(b)).push(r)));\n"
     "  const bl = [...bills.entries()]",
     "  const bills = billGroups(rows);  /* REORG-v1: split by session */\n"
     "  const bl = [...bills.entries()]"),
    ("    const name = billName(b);\n",
     "    const [bn, bs] = b.split('|'), name = bs ? billSesName(bn, bs) : billName(b);  /* REORG-v1 */\n"),
    ("    return `<button class=\"billrow\" data-bill=\"${esc(b)}\"><b>${b}</b>",
     "    return `<button class=\"billrow\" data-bill=\"${esc(bn)}\"${bs ? ` data-bses=\"${esc(bs)}\"` : ''}><b>${bn}${bs ? ` <small>${rgSesShort(bs)}</small>` : ''}</b>"),
    ("  const bc = new Map(); rows.forEach(r => r.bills.forEach(b => bc.set(b, (bc.get(b)||0)+1)));\n",
     "  const bc = new Map([...billGroups(rows)].map(([k, rs]) => [k, rs.length]));  /* REORG-v1: split by session */\n"),
    ("joinL(tb.map(([b,c]) => `${b}${billName(b) ? ', '+billName(b) : ''} (${c})`))",
     "joinL(tb.map(([b,c]) => `${billLabel(b)} (${c})`))"),
    # Data: the reporter line counts people only (same rule as Press desk > Pitch)
    ("  const ar = authorRank(rows).slice(0,3)",
     "  const ar = authorRank(rows).filter(a => (AKIND.get(authorKey(a)) || 'person') === 'person').slice(0,3)  /* REORG-v1: people only */"),
    # Data: cut renders (Reporters chart -> one line; Bills over time; latest clips in other languages)
    ("  const rp = reporterBars($('#repBars'), rows, Infinity, 2);\n"
     "  $('#repCap').textContent = `Who wrote the stories, colored by the tone of each reporter's stories. ${pl(rp.stories,'story has','stories have')} a known author so far; authors are found in saved copies. Click a reporter to see their clips.`;\n",
     "  /* REORG-v1: the Reporters chart is cut (one line + Press desk > Pitch) */\n"),
    ("  renderTravel(rows); renderRel(rows); renderBills(rows); renderCalendar(rows);",
     "  renderTravel(rows); renderRel(rows); renderCalendar(rows);  /* REORG-v1: Bills over time cut */"),
    ("  $('#ethLatest').innerHTML = latest.length",
     "  if ($('#ethLatest')) $('#ethLatest').innerHTML = latest.length"),
    # hashes: #data for the Data tab (#report and #trends still open it); Tone by issue links open Data > Tone
    ("'#'+({db:'clips',an:'report'}[t])", "'#'+({db:'clips',an:'data'}[t])"),
    ("setTab(insH ? 'in' : ({clips:'db', trends:'an', report:'an'}[h] || 'ov'));",
     "setTab(insH ? 'in' : ({clips:'db', trends:'an', report:'an', data:'an'}[h] || (RG.toTone ? 'an' : 'ov')));  /* REORG-v1 */"),
]
NEW_SINCE = ("  // new since the last visit, grouped by day\n", "  $('#newList').innerHTML = out + (day ? '</div>' : '');\n",
             "  reorgHomeLine(n30, p30);  /* REORG-v1: no 'new since your last visit' / weekly items on Home; one 30-day line instead */\n")

REL_EDITS = [
    ("        x.fu.sort(function(a,b){ return a.lag - b.lag || (a.outlet < b.outlet ? -1 : 1); });",
     "        // REORG-v1 baseline: the same stories in the WINDOW days BEFORE the release\n"
     "        x.pre = 0; for (var j = 1; j <= WINDOW; j++) (byDate[ctx.addDays(x.date, -j)] || []).forEach(function(r){ if (x.basis === 'bill' ? (r.bills || []).some(function(b){ return bs[b]; }) : (r.topic === x.topic)) x.pre++; });\n"
     "        x.fu.sort(function(a,b){ return a.lag - b.lag || (a.outlet < b.outlet ? -1 : 1); });"),
    ("    var pct = checkable.length ? Math.round(100 * led / checkable.length) : null;",
     "    var pct = checkable.length ? Math.round(100 * led / checkable.length) : null;\n"
     "    var preN = checkable.filter(function(x){ return x.pre; }).length, pre = checkable.length ? Math.round(100 * preN / checkable.length) : null;   // REORG-v1"),
    ("      + tile('Led to original coverage', pct == null ? '–' : pct + '%', pct == null ? 'no bill or issue to match' : led + ' of ' + ctx.pl(checkable.length, 'release', 'releases') + ', within ' + WINDOW + ' days')",
     "      + tile('Original coverage, before vs after', pct == null ? '–' : pre + '% → ' + pct + '%', pct == null ? 'no bill or issue to match' : 'of ' + ctx.pl(checkable.length, 'release', 'releases') + ' with a bill or issue, ' + preN + ' already had stories on it in the ' + WINDOW + ' days before; ' + led + ' had some on the release day or the ' + WINDOW + ' days after')   // REORG-v1 baseline"),
    ("        + '</div><div><h3>Original reporting within ' + WINDOW + ' days</h3>'",
     "        + '</div><div><h3>Original reporting within ' + WINDOW + ' days</h3>'\n"
     "        + (x.basis ? '<div class=\"rpk-m\" style=\"margin-bottom:6px\">Baseline: ' + ctx.pl(x.pre, 'story', 'stories') + ' on the same ' + x.basis + ' in the ' + WINDOW + ' days before.</div>' : '')   // REORG-v1"),
    ("A match shows coverage followed the release, not that the release caused it.'",
     "A match shows coverage followed the release, not that the release caused it. The baseline counts the same kind of stories in the ' + WINDOW + ' days before the release: many releases come out while a bill is already in the news.'"),
]
TRAVEL_EDITS = [('<h2 class="sec">Where it ran</h2>', '<h2 class="sec">Map of pickups</h2>')]


def sha(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def edits(s, pairs, label, log):
    for old, new in pairs:
        if new in s:
            continue
        n = s.count(old)
        if n != 1:
            raise SystemExit(f'{label}: anchor found {n}x: {old[:90]!r}')
        s = s.replace(old, new)
        log.append(f'{label}: edit {old.strip()[:60]!r}')
    return s


def patch_js(path, log):
    s0 = s = open(path, encoding='utf-8').read()
    a, b, new = NEW_SINCE
    if a in s:
        i = s.index(a); j = s.index(b, i) + len(b)
        s = s[:i] + new + s[j:]; log.append('js: new-since block replaced')
    elif new not in s:
        raise SystemExit('js: new-since anchor missing')
    s = edits(s, JS_EDITS, 'js', log)
    for start, end in RETIRED:   # NOPHONE-v1
        if start in s:
            i = s.index(start); j = s.index(end, i) + len(end) + 1
            s = s[:i] + s[j:]; log.append('js: retired block removed: ' + start.strip('/* -'))
    for fn, start, end in BLOCKS:
        blk = open(os.path.join(HERE, fn), encoding='utf-8').read().rstrip('\n') + '\n'
        if start in s:
            i = s.index(start); j = s.index(end, i) + len(end) + 1
            if s[i:j] != blk:
                s = s[:i] + blk + s[j:]; log.append(f'js: {fn} block refreshed')
        else:
            if s.count(BOOT) != 1:
                raise SystemExit('js: boot anchor')
            s = s.replace(BOOT, blk + BOOT); log.append(f'js: {fn} block inserted')
    if s != s0:
        open(path, 'w', encoding='utf-8').write(s)
    return s != s0


def patch_views(vdir, log):
    rp = os.path.join(vdir, 'reporters.js')
    pitch = open(os.path.join(HERE, 'reorg_pitch.js'), encoding='utf-8').read()
    if not os.path.exists(rp):
        log.append(f'views: {rp} missing - skipped')
    else:
        cur = open(rp, encoding='utf-8').read()
        if cur == pitch:
            pass
        elif "label: 'Reporters'" in cur and 'Reporter outreach list' in cur:
            open(rp, 'w', encoding='utf-8').write(pitch); log.append('views: reporters.js := Pitch (reorg_pitch.js)')
        elif 'Press desk › Pitch' in cur:
            open(rp, 'w', encoding='utf-8').write(pitch); log.append('views: reporters.js Pitch refreshed')
        else:
            raise SystemExit('views: reporters.js is neither the v16 reporter list nor Pitch - merge by hand')
    for fn, pairs in (('release_pickup.js', REL_EDITS), ('story_travel.js', TRAVEL_EDITS)):
        p = os.path.join(vdir, fn)
        if not os.path.exists(p):
            log.append(f'views: {fn} missing - skipped'); continue
        s0 = open(p, encoding='utf-8').read(); s = edits(s0, pairs, fn, log)
        if s != s0:
            open(p, 'w', encoding='utf-8').write(s)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--js'); ap.add_argument('--views')
    a = ap.parse_args()
    log = []
    if a.js:
        patch_js(a.js, log)
    if a.views:
        patch_views(a.views, log)
    print('\n'.join(log) if log else 'REORG-v1: already applied')


if __name__ == '__main__':
    main()
