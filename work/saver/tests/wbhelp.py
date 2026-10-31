"""Synthetic workbook builders shared by the saver tests."""
from pathlib import Path


def base_sheets():
    """{tab: (header, rows)}. Lists, so a test can mutate cells. Coverage columns:
    0 Article ID, 1 Original or reprint, 2 Story ID, 3 Headline, 4 Place, 5 # of reprints, 6 File name, 7 Saved Copy?
    (test_saver_diff indexes into rows by these positions; the header here is the source of truth.)"""
    cov_h = ['Article ID', 'Original or reprint', 'Story ID', 'Headline', 'Place', '# of reprints', 'File name', 'Saved Copy?']
    cov = [['10001', 'Original', 's00001', 'Headline one', 'Sacramento', None, 'a.html', 'Yes'],
           ['10002', 'Original', 's00002', 'Headline two', None, None, 'b.html', 'Yes'],
           ['10003', 'Original', 's00003', 'Headline three', 'Fresno', None, 'c.html', 'No']]
    return {
        'Coverage': [cov_h, cov],
        'Originals': [list(cov_h), [list(r) for r in cov]],
        'Bills': [['Bill', 'Title', 'Author', 'Status'], [['AB 1', 't1', 'a1', 's1'], ['AB 2', 't2', 'a2', 's2']]],
        'Press releases': [['Release ID', 'URL', 'Title', 'Date', 'Related count', 'Has copies'],
                           [['pr00001', 'http://r/1', 'Rel one', '2026-01-01', 2, 'Yes'], ['pr00002', 'http://r/2', 'Rel two', '2026-01-02', None, None]]],
        'Audio & video details': [['Article ID', 'Show'], [['10002', 'Morning Show'], ['10003', 'Evening Show']]],
        'Removed': [['Article ID', 'From tab'], []],
        'Unlinked print pages': [['Article ID', 'Outlet'], [['20001', 'Paper']]],
    }


def make_wb(path, sheets, links):
    """sheets: {name: (header, rows)}; links: {(sheet, excel row, 0-based col): url}. Header [] writes an empty first row."""
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, (header, rows) in sheets.items():
        ws = wb.create_sheet(name)
        ws.append(list(header) if header else [None])
        for r in rows:
            ws.append(list(r))
        for (sn, row, col), url in links.items():
            if sn == name:
                c = ws.cell(row=row, column=col + 1)
                c.hyperlink = url
    wb.save(str(path))
    return Path(path)
