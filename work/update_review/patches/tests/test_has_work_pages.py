"""PAGESORPHAN-v1 (REQ-7): has_work counts only pages docs that an undone run (or an unwritten reprints doc) references.
Run: python3 -I build/tests/sheet_task/test_has_work_pages.py"""
import os, sys
L = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(L, 'code'))
import sheet_task as ST
fails = 0
def ok(c, m, i=''):
    global fails
    print(('PASS ' if c else 'FAIL ') + m + ('' if c else '  -- ' + str(i)[:300])); fails += (not c)
PG = {'og-aaaaaaaaaaaa': {'url': 'https://x.test/o', 'clean': '<p>t</p>'}, 'rp-bbbbbbbbbbbb': {'url': 'https://x.test/r'}}
applied = {'at': 'T', 'mode': 'find', 'ids': {'NEW-run-a-1': '10001'}, 'rows': [{'Article ID': 'NEW-run-a-1', 'Story ID': 'sNEW-run-a-1', '_page': 'rp-bbbbbbbbbbbb',
           '_origin': {'cands': [{'url': 'https://x.test/o', 'page': 'og-aaaaaaaaaaaa'}]}}]}
# 1 applied run + two orphan pages
w, why = ST.has_work({'runs': {'run-a': applied}, 'pages': dict(PG)})
ok(w is False and why['pages_orphan'] == 2 and why['pages'] == 0, '1: an applied run and two orphan pages docs are not work; pages_orphan = 2', (w, why))
# 1b one applied run, the page docs of a sheet-line-only run
w, why = ST.has_work({'runs': {'run-a': dict(applied, ids={}, sheet={'at': 'T'})}, 'pages': dict(PG)})
ok(w is False and why['pages_orphan'] == 2, '1b: a run with a sheet line counts as applied too', (w, why))
# 2 same pages, run not applied and referencing them (_page, _origin.cands[*].page)
undone = dict(applied); undone.pop('ids')
w, why = ST.has_work({'runs': {'run-a': undone}, 'pages': dict(PG)})
ok(w is True and why['pages'] == 2 and why['pages_orphan'] == 0 and why['runs'] == 1, '2: an undone run referencing both pages: work, pages = 2, no orphan', (w, why))
# 3 one orphan beside a referenced page: orphan counted, not work by itself
only_page = {'rows': [{'Article ID': 'NEW-run-b-1', '_page': 'rp-bbbbbbbbbbbb'}]}
w, why = ST.has_work({'runs': {'run-b': dict(only_page, ids={'NEW-run-b-1': '10002'})}, 'pages': {'og-orphan0000000': {}}})
ok(w is False and why['pages_orphan'] == 1, '3: a single orphan alone is not work', (w, why))
# 4 temp-code / placeholder keys of an undone run
w, why = ST.has_work({'runs': {'run-c': {'rows': [{'Article ID': 'NEW-run-c-1', 'Story ID': 'sNEW-run-c-1', 'Tracker story code': 'jg-abc123'}]}},
                      'pages': {'jg-abc123': {}, 'NEW-run-c-1': {}, 'stray': {}}})
ok(w is True and why['pages'] == 2 and why['pages_orphan'] == 1, '4: pages keyed by the placeholder Article ID / Tracker story code count; a stray one is an orphan', (w, why))
# 5 hand-added reprint not yet written -> its rp- page is referenced; written -> orphan
w, why = ST.has_work({'reprints': {'abc': {'story': 's00001', 'outlet': 'X'}}, 'pages': {'rp-abc': {}}})
ok(w is True and why['reprints'] == 1 and why['pages'] == 1 and why['pages_orphan'] == 0, '5: an unwritten reprints doc keeps its rp- page as work', (w, why))
w, why = ST.has_work({'reprints': {'abc': {'story': 's00001', 'aid': '10003'}}, 'pages': {'rp-abc': {}}})
ok(w is False and why['pages_orphan'] == 1, '5b: a written reprints doc leaves its rp- page an orphan', (w, why))
w, why = ST.has_work({'reprints': {'q1': {'story': 's00001', 'outlet': 'X', '_pageKey': 'jg-0a0a0a'}}, 'pages': {'jg-0a0a0a': {}}})
ok(w is True and why['pages'] == 1 and why['pages_orphan'] == 0, '5c: an unwritten reprints doc keeps the pages doc named by its _pageKey', (w, why))
# 6 other work kinds are unchanged
w, why = ST.has_work({'runs': {'r': {'bills_new': [{'bill': 'AB 1'}]}}, 'edits': {}, 'pages': {}})
ok(w is True and why['bills'] == 1 and why['pages_orphan'] == 0, '6: bills_new still counts as work', (w, why))
w, why = ST.has_work({})
ok(w is False and why == {'runs': 0, 'bills': 0, 'releases': 0, 'edits': 0, 'reprints': 0, 'pages': 0, 'pages_orphan': 0}, '6b: an empty db is no work', (w, why))
print('ALL %s' % ('CHECKS PASSED' if not fails else '%d FAILED' % fails)); sys.exit(1 if fails else 0)
