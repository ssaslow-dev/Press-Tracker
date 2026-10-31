"""date_rules.py - DATES-v1 sanity checks and Date-source mapping for the sheet task (code/, next to sheet_task.py).
Pure functions; sheet_task.date_check calls check_row() for every new row and the publish-time script runs it over the sheet.

Checks (design §3.5):
 1 Year = Date[:4]
 2 no Date after the run day; none within 3 days of the fetch day unless Date source is page byline / page metadata / print edition
 3 Reprint Date >= Original Date - 1; exactly -1 with a web Original -> flag the Original (UTC suspect); <= -2 -> review
 4 Original dated after >= 2 of its reprints with no page stamp of its own -> review
 5 press-release copy dated before its release -> review
 6 headline says signs/signed + bill tag -> Date >= that bill's Signed date, else review
 7 Date != the page's Updated stamp when a publish stamp exists; Date <= Updated stamp
 8 new Web row with no page date and TinyFish's date = run day -> blank + note
Each finding is {'check': n, 'action': 'fix'|'review'|'blank', 'column', 'new', 'why'}; 'fix' is safe to write, the rest go to the
report (date_review)."""
import re
import datetime as dt
try:
    from dates_lib import local_day, displayed_stamp, updated_stamp, days_between, zone_for
except ImportError:   # when imported from the patches folder
    from .dates_lib import local_day, displayed_stamp, updated_stamp, days_between, zone_for

# v22: 'copied from reprint' = a no-link no-copy originator (NOCOPY-v2) dated from its reprint
SOURCES = ('print edition', 'page byline', 'page metadata', 'URL', 'NewsBank', 'ProQuest', 'air date (Pacific)', 'episode page',
           'search snippet (converted)', 'copied from Original', 'copied from reprint', 'undated', 'unknown')
PAGE_SOURCES = ('page byline', 'page metadata', 'print edition')
SIGNS = re.compile(r'\b(signs|signed|signing)\b', re.I)
UNDATED_NOTE = 'undated page; fetch-dated'


def source_from_update(date_src, edition=''):
    """the Update button's internal _date_src -> Date source vocabulary"""
    return {'page': 'page byline', 'claude': 'page byline', 'tinyfish': 'page metadata', 'snippet': 'search snippet (converted)',
            'none': 'undated', 'edited': 'copied from Original', 'url': 'URL',
            'reprint': 'copied from reprint'}.get(str(date_src or ''), 'print edition' if edition == 'Print' else 'unknown')


def with_precision(src, date):
    d = str(date or '')
    if not d:
        return 'undated'
    if len(d) == 7:
        return src + ' (month)'
    if len(d) == 4:
        return src + ' (year)'
    return src


def check_row(row, ctx):
    """row: the sheet row (dict of column -> value; Date, Year, Original or reprint, Story ID, Edition, Headline, Bills,
    Press release, Publisher link, Date source). ctx: {'run_day', 'today', 'original_date', 'original_edition',
    'reprint_dates': [...], 'release_date', 'signed': {bill: date}, 'page_text', 'page_stamp' (ISO or ''),
    'date_src' (the update button's internal value), 'has_page_date': bool}. Returns a list of findings."""
    out = []
    d = str(row.get('Date') or '')[:10]
    src = str(row.get('Date source') or source_from_update(ctx.get('date_src'), row.get('Edition')))
    kind = str(row.get('Original or reprint') or '')
    run_day, today = ctx.get('run_day') or '', ctx.get('today') or ''
    # 8 (first: it can blank the date)
    if kind and row.get('Edition', 'Web') in ('Web', '') and not ctx.get('has_page_date') and ctx.get('date_src') == 'tinyfish' and d and d in (run_day, today):
        out.append({'check': 8, 'action': 'blank', 'column': 'Date', 'new': '', 'why': "page gives no date and TinyFish's published_date is the fetch day", 'note': UNDATED_NOTE})
        return out
    if not d:
        if src not in ('undated',):
            out.append({'check': 1, 'action': 'fix', 'column': 'Date source', 'new': 'undated', 'why': 'blank Date'})
        return out
    # 1
    y = str(row.get('Year') or '').split('.')[0]
    if y != d[:4]:
        out.append({'check': 1, 'action': 'fix', 'column': 'Year', 'new': d[:4], 'why': 'Year = Date[:4]'})
    # 2
    if run_day and d > run_day:
        out.append({'check': 2, 'action': 'review', 'column': 'Date', 'new': '', 'why': f'Date after the run day {run_day}'})
    elif run_day and len(d) == 10 and src.split(' (')[0] not in PAGE_SOURCES and abs(days_between(d, run_day) or 99) <= 3:
        out.append({'check': 2, 'action': 'review', 'column': 'Date', 'new': '', 'why': f'Date within 3 days of the fetch day with Date source "{src}"'})
    # 3
    od = str(ctx.get('original_date') or '')[:10]
    if kind.startswith('Reprint') and od and len(d) == 10 and len(od) == 10:
        diff = days_between(d, od)
        if diff == -1 and ctx.get('original_edition', 'Web') in ('Web', ''):
            out.append({'check': 3, 'action': 'review', 'column': 'Date', 'new': '', 'why': f'reprint a day before its web Original ({od}): the Original is UTC-suspect', 'target': 'Original'})
        elif diff is not None and diff <= -2:
            out.append({'check': 3, 'action': 'review', 'column': 'Date', 'new': '', 'why': f'reprint {-diff} days before its Original ({od}): origin or date'})
    # 4
    rds = [x[:10] for x in (ctx.get('reprint_dates') or []) if x]
    if kind == 'Original' and len(d) == 10 and not ctx.get('has_page_date') and sum(1 for x in rds if len(x) == 10 and x < d) >= 2:
        out.append({'check': 4, 'action': 'review', 'column': 'Date', 'new': '', 'why': f'Original dated after {sum(1 for x in rds if x < d)} of its reprints and no page stamp of its own (wire / NewsBank ingest date?)'})
    # 5
    rel = str(ctx.get('release_date') or '')[:10]
    if rel and len(d) == 10 and d < rel:
        out.append({'check': 5, 'action': 'review', 'column': 'Date', 'new': '', 'why': f'press-release copy dated before the release ({rel})'})
    # 6
    if SIGNS.search(str(row.get('Headline') or '')) and ctx.get('signed'):
        for b in [x.strip() for x in str(row.get('Bills') or '').split(';') if x.strip()]:
            sd = str(ctx['signed'].get(b) or '')[:10]
            if sd and len(d) == 10 and d < sd:
                out.append({'check': 6, 'action': 'review', 'column': 'Date', 'new': '', 'why': f'headline says signed, {b} was signed {sd} (tag or session error as likely as the date)'})
    # 7
    text = ctx.get('page_text') or ''
    if text and len(d) == 10:
        upd = updated_stamp(text)
        pub = displayed_stamp(text)[0]
        if upd and pub and d == upd and pub != upd:
            out.append({'check': 7, 'action': 'fix', 'column': 'Date', 'new': pub, 'why': f'Date = the page\'s Updated stamp {upd}; the publish line says {pub}'})
        elif upd and d > upd:
            out.append({'check': 7, 'action': 'review', 'column': 'Date', 'new': '', 'why': f'Date after the page\'s Updated stamp {upd}'})
    return out


def page_date(text, stamp='', zone='America/Los_Angeles', host=''):
    """(date, source) for a fetched web page: displayed publish line > metadata stamp (local day) > ('', 'undated')."""
    d, kind, _ = displayed_stamp(text or '')
    if d:
        return d, 'page byline'
    ld = local_day(stamp, zone, host) if stamp else ''
    if ld:
        return ld, 'page metadata'
    return '', 'undated'


def header_date(row, date_src):
    """the library copy's header date: the page's own date (byline / metadata / print edition), else 'undated'; never the
    sheet date when it came from a scrape day, a save day or a search snippet."""
    src = str(row.get('Date source') or source_from_update(date_src, row.get('Edition')))
    d = str(row.get('Date') or '')[:10]
    return d if d and src.split(' (')[0] in PAGE_SOURCES + ('NewsBank', 'ProQuest', 'air date (Pacific)', 'episode page') else 'undated'
