"""Split untoned Original rows that now have text into N tone-job batches.
Usage: python3 -I make_tone_jobs.py COVERAGE.xlsx N OUT_DIR
Text sources (first found wins): lib/work/texts/nb/<aid>.json, lib/work/texts/tracker/<sid>.html.
Each job line carries everything the one-pass reader needs (TONE_GUIDE.md): text, headline, outlet, date,
language, current Role/Topic/Bills/author/word count/translation state, so all fills come from one read."""
import sys, os, json, re, html as H
import pandas as pd
COV, N, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
L = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
C = pd.read_excel(COV, sheet_name='Coverage', dtype=str).fillna('')
O = C[C['Original or reprint'] == 'Original']
def txt(h):
    h = re.sub(r'(?is)<(script|style).*?</\1>', '', h)
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'(?s)<[^>]+>', ' ', h))).strip()
jobs = []
for _, r in O.iterrows():
    need_tone = not r['Tone']
    need_topic = not r['Topic']
    nb = os.path.join(L, 'work', 'texts', 'nb', r['Article ID'] + '.json')
    tr = os.path.join(L, 'work', 'texts', 'tracker', r['Story ID'] + '.html')
    t = None
    if os.path.exists(nb):
        j = json.load(open(nb)); t = {'source': 'newsbank', 'text': j.get('text', ''), 'author_hdr': j.get('author', ''),
                                      'words': j.get('words', ''), 'mentions_gabriel': j.get('mentions_gabriel'),
                                      'bills_hdr': j.get('bills_mentioned', []), 'language_detected': j.get('language_detected', '')}
    elif os.path.exists(tr):
        t = {'source': 'tracker', 'text': txt(open(tr).read())}
    if not t or not t['text'] or not (need_tone or need_topic): continue
    jobs.append({'sid': r['Story ID'], 'aid': r['Article ID'], 'outlet': r['Outlet'], 'date': r['Date'], 'hl': r['Headline'],
                 'lang': r['Language'], 'need_tone': need_tone, 'need_topic': need_topic, 'need_bills': not r['Bills'],
                 'need_hl_en': bool(r['Language'] and r['Language'] != 'English' and not r['Translated Headline']),
                 'need_text_en': bool(r['Language'] and r['Language'] != 'English' and not r['Story in English']),
                 'role': r['Role'], 'author': r['Author / byline'], **t})
os.makedirs(OUT, exist_ok=True)
jobs.sort(key=lambda j: j['sid'])
for i in range(N):
    with open(os.path.join(OUT, f'tone_batch_{i + 1}.jsonl'), 'w') as f:
        for j in jobs[i::N]: f.write(json.dumps(j, ensure_ascii=False) + '\n')
print(len(jobs), 'jobs in', N, 'batches')
