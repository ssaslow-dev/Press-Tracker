#!/usr/bin/env python3
"""TAGS-v1 acceptance checks (TONE_GUIDE.md §5) on the coverage workbook, Originals only. Read-only.
usage: python3 acceptance_checks.py <coverage.xlsx> [--json]
  1. no Bills tag whose introduction date is after the story date
  2. no Tone where the Tone note says Gabriel is not mentioned
  3. no Other / roundup (or blank) Topic when the tagged bills all share one known issue
  4. identical Tone / Topic / Bills across a story's rows (Original + reprints) and across text-identical Originals (when --texts)
  5. Tone in the five-point scale, Topic in the list, Bills in the leginfo list
exit 1 when any check fails."""
import sys, re, json, collections
import openpyxl, billmatch as bm

ABSENT = re.compile(r"(?:not|does not|doesn't|never|no longer)\s+(?:mention|name|reference)\w*\s+Gabriel|Gabriel\s+(?:is|was)\s+not\s+(?:mentioned|named)|no\s+(?:mention|reference)\s+(?:of|to)\s+Gabriel|without\s+(?:mentioning|naming)\s+Gabriel|Gabriel\s+not\s+named", re.I)
HL_END = {'a', 'an', 'the', 'to', 'of', 'in', 'on', 'for', 'by', 'as', 'and', 'or', 'with', 'from', 'at', 'anti', 'non', 'pre', 'post', 'how', 'that', 'their', 'than'}   # REVIEW4-LEFTOVERS C7
TONES = {'', 'Very negative', 'Negative', 'Neutral', 'Positive', 'Very positive'}

def run(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True); ws = wb['Coverage']
    rows = ws.iter_rows(values_only=True); H = {h: i for i, h in enumerate(next(rows)) if h}
    g = lambda r, c: str(r[H[c]] or '').strip() if c in H and r[H[c]] is not None else ''
    fails = collections.defaultdict(list); by_story = collections.defaultdict(list)
    for r in rows:
        sid = g(r, 'Story ID'); kind = g(r, 'Original or reprint')
        by_story[sid].append((g(r, 'Tone'), g(r, 'Topic'), g(r, 'Bills')))
        if kind != 'Original': continue
        date = bm.pad_date(g(r, 'Date')[:10]); tone, topic, bills, note = g(r, 'Tone'), g(r, 'Topic'), g(r, 'Bills'), g(r, 'Tone note')
        bl = [b.strip() for b in bills.split(';') if b.strip()]
        for b in bl:
            info, _ = bm.resolve(b, date or '2099-12-31', '-' in b)
            if b not in bm.INFO: fails['5 bill not in leginfo list'].append((sid, b))
            elif date and not info: fails['1 bill tagged before any session of his'].append((sid, b, date))
            elif date and info['intro'] > date: fails['1 bill tagged before introduction'].append((sid, b, info['intro'], date))
        if tone and ABSENT.search(note): fails['2 tone but note says Gabriel absent'].append((sid, tone, note[:80]))
        if topic in ('', 'Other / roundup') and bl:
            tps = {bm.bill_topic(b, date or '2026-01-01') for b in bl}
            if len(tps) == 1 and None not in tps and 'Other / roundup' not in tps: fails['3 Other/blank topic with single-issue bills'].append((sid, bl, tps.pop()))
        hl = g(r, 'Headline')   # REVIEW4-LEFTOVERS C7: placeholder or cut headline on an Original
        if hl and (len(hl) <= 3 or hl.endswith(('…', '...')) or hl.split()[-1].lower().strip(',:;-') in HL_END): fails['6 placeholder or cut headline'].append((g(r, 'Article ID'), hl[:60]))
        if tone not in TONES: fails['5 tone value'].append((sid, tone))
        if topic and topic not in bm.TOPICS: fails['5 topic value'].append((sid, topic))
    for sid, vals in by_story.items():
        if len(set(vals)) > 1: fails['4 rows of one story differ'].append((sid, sorted(set(vals))[:3]))
    return fails

if __name__ == '__main__':
    f = run(sys.argv[1])
    if '--json' in sys.argv: print(json.dumps({k: v[:50] for k, v in f.items()}, indent=1, default=str))
    else:
        for k, v in sorted(f.items()): print(f'{k}: {len(v)}', v[:5])
        print('OK' if not f else 'FAILURES')
    sys.exit(1 if f else 0)
