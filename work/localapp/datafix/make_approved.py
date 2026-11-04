"""DATAFIX-v1: turns the data-check proposals into the files the "Switch-over changes" screen loads (Sammy's approved answers, docs/DECISIONS.md DATAFIX-v1 and follow-up).
Re-runnable: it reads only the proposal files in this folder and writes
    work/localapp/app/src/station/data/approved/*.csv    cell fixes (shipped with the app; the screen loads them first), in the screen's format (Tab, Article ID, Column, Current, New value, Confidence, Overwrite, Evidence)
    work/localapp/app/src/station/data/datafix_structural.json   the fixes cells cannot express (retire Unlinked print pages rows, English-Original swaps) and the list "for you to decide"
    work/localapp/app/src/station/data/prjudge_v2.json      the 13 organisation-site posts move from org_posts_listed to unmark (Press release = No)
The screen re-checks every line on the real workbook (blank-only unless the line says Overwrite).

    python3 -I work/localapp/datafix/make_approved.py

Rules applied (numbers are Sammy's answers):
  1/2  print pages: class A, high + medium (10 + 22): the blank print-page cells are filled, Edition "Web" -> "Web + Print" on the medium rows (overwrite, only where it says Web today),
       and the Unlinked row is retired (structural step, only once the row's NewsBank print-page link is filled). A-jump notes, low and class B (none) are not applied.
  6    Language fixes 00169, 00170, 10618 -> Spanish
  8    outlet-name authors: Author 1 cleared for the 14 high-confidence cells (overwrite); the 9 blog/brand ones stay
  10/11 NewsBank header fills, high + medium (low excluded), including group bylines; Page fills normalised (NewsBank spacing and zero-padding stripped)
  12   approved_pages.csv (117 Page cells, overwrite), normalised the same way
  7    s00512 / s00985: the English row becomes the Original (structural)
  14   13 organisation posts -> Press release = No
Not applied, listed on the screen for Sammy: 01920 (split into its own story, or removed), 03486 byline (Marisa Kendall).
"""
import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATION_DATA = HERE.parent / 'app' / 'src' / 'station' / 'data'
OUT = STATION_DATA / 'approved'
FIELDS = ['Tab', 'Article ID', 'Column', 'Current', 'New value', 'Confidence', 'Overwrite', 'Evidence']
LANG_FIX = ('00169', '00170', '10618')


def read(p):
    return list(csv.DictReader(open(p, encoding='utf-8-sig')))


def write(name, rows):
    OUT.mkdir(exist_ok=True)
    with open(OUT / name, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f'{name}: {len(rows)} lines')


def norm_page(v: str) -> str:
    """NewsBank quirks no paper prints: spaces ("A 4" -> A4) and leading zeros ("A001" -> A1, "05" -> 5). Section-letter order is kept as it is."""
    v = re.sub(r'\s+', '', v or '')
    return re.sub(r'(?<!\d)0+(?=\d)', '', v)


def line(tab, aid, col, new, conf, evidence, cur='', overwrite=''):
    return {'Tab': tab, 'Article ID': aid, 'Column': col, 'Current': cur, 'New value': new, 'Confidence': conf, 'Overwrite': overwrite, 'Evidence': (evidence or '')[:300]}


def main():
    # 1/2 print pages
    pp = read(HERE / 'print_pages' / 'proposals.csv')
    fills, retire = [], []
    for x in pp:
        if x['class'] != 'A' or x['confidence'] not in ('high', 'medium'):
            continue
        if x['tab'] == 'Coverage':
            if x['column'] == 'Edition':
                fills.append(line('Coverage', x['row key'], 'Edition', x['new value'], x['confidence'], x['evidence'], cur='Web', overwrite='yes'))
            else:
                fills.append(line('Coverage', x['row key'], x['column'], norm_page(x['new value']) if x['column'] == 'Page' else x['new value'], x['confidence'], x['evidence']))
        elif x['tab'] == 'Unlinked print pages' and x['column'] == '(row)':
            m = re.search(r'fills on (\d{5})', x['new value']) or re.search(r'row (\d{5})', x['evidence'])
            retire.append({'key': x['row key'], 'aid': m.group(1) if m else '', 'confidence': x['confidence']})
    assert len(retire) == 32, len(retire)
    write('01_print_pages_A.csv', fills)
    # 6 language
    tr = [x for x in read(HERE / 'translations' / 'proposals.csv') if x['column'] == 'Language' and x['article_id'] in LANG_FIX]
    assert len(tr) == 3
    write('02_language_fixes.csv', [line('Coverage', x['article_id'], 'Language', 'Spanish', x['confidence'], x['evidence'], cur='English', overwrite='yes') for x in tr])
    # 8 outlet-name authors, high only
    oa = [x for x in read(HERE / 'outlet_authors' / 'proposals.csv') if x['confidence'] == 'high']
    assert len(oa) == 14 and all(x['column'] == 'Author 1' and x['new'] == '' for x in oa)
    write('03_outlet_name_authors.csv', [line('Coverage', x['article_id'], 'Author 1', '', 'high', x['evidence'], cur=x['current'], overwrite='yes') for x in oa])
    # 10/11 NewsBank header fills, high + medium
    nb = [x for x in read(HERE / 'nb_fills2' / 'proposals.csv') if x['confidence'] in ('high', 'medium')]
    rows = []
    for x in nb:
        new = norm_page(x['new value']) if x['column'] == 'Page' else x['new value']
        rows.append(line(x['tab'], x['Article ID'], x['column'], new, x['confidence'], x['evidence']))
    write('04_newsbank_header_fills.csv', rows)
    # 12 page conflicts
    ap = read(HERE / 'nb_fills2' / 'approved_pages.csv')
    assert len(ap) == 117
    write('05_newsbank_pages.csv', [line(x['Tab'], x['Article ID'], 'Page', norm_page(x['New value']), x['Confidence'], 'printed page from the NewsBank header (AUDIT_PAGES.md)', cur=x['Current'], overwrite='yes') for x in ap])
    # structural
    struct = {
        'about': 'DATAFIX-v1: fixes the cell CSVs cannot express. Made by work/localapp/datafix/make_approved.py.',
        'retire_unlinked': retire,
        'english_original': [{'sid': 's00512', 'new_original': '01829', 'old_original': '08145'}, {'sid': 's00985', 'new_original': '03482', 'old_original': '03492'}],
        'decide': [
            '01920 (Shuang Ma Chemical, Korean chemical-supplier page) is not a translation of its story: split it into a story of its own, or remove it if it is not coverage. Your call.',
            '03486 (East Bay Express, s00985): the byline should be Marisa Kendall. Your call.',
            'About 585 Page cells hold NewsBank scan positions, not printed page numbers (sheet-wide; not changed).',
            'Sister-paper print pages (class B, 277) stay in Unlinked print pages as a clip-and-check list (print_pages/AUDIT_B.md); low-confidence print matches (25) and the 138 jump pages are not applied.',
        ],
    }
    STATION_DATA.mkdir(parents=True, exist_ok=True)
    (STATION_DATA / 'datafix_structural.json').write_text(json.dumps(struct, indent=1, ensure_ascii=False), encoding='utf-8')
    print('datafix_structural.json written')
    # 14 organisation posts -> unmark
    p = STATION_DATA / 'prjudge_v2.json'
    d = json.loads(p.read_text(encoding='utf-8'))
    if d.get('org_posts_listed'):
        have = {u['aid'] for u in d['unmark']}
        for o in d['org_posts_listed']:
            if o['aid'] not in have:
                d['unmark'].append(o)
        d['org_posts_listed'] = []
        p.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding='utf-8')
        print('prjudge_v2.json: organisation posts moved to unmark')


if __name__ == '__main__':
    main()
