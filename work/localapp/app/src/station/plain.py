"""plain.py: the saver's and the update folder's answers, in plain words for the panel (Sammy is not a programmer).
Pure functions, no I/O."""
from __future__ import annotations

ZIP_CODES = {
    'NO_ZIP': 'That file is not there any more.',
    'BAD_ZIP': 'This is not a readable zip file.',
    'BAD_MANIFEST': "The update's contents list (manifest.json) is missing or damaged.",
    'BAD_ENTRY': 'The zip holds a file that an update may not hold. Nothing in it was read or saved.',
    'BAD_JSON': 'A file in the zip is not in the expected form.',
    'HASH_MISMATCH': 'A file in the zip does not match its checksum, so the zip was changed or damaged after it was made.',
    'UNLISTED_FILE': 'The zip holds a file that its contents list does not mention.',
    'MISSING_FILE': 'The zip is missing a file that its contents list names.',
    'TOO_BIG': 'The zip is bigger than an update may be.',
    'TOO_MANY_FILES': 'The zip holds more files than an update may have.',
    'ZIP_BOMB': 'The zip would expand to far more than it should, so it was refused.',
    'NEWER_FORMAT': 'This update was made by a newer version of the Update station than this tracker understands.',
}

CATEGORIES = {
    'needs_fetch': 'links that still need to be looked up',
    'name_collision': 'saved page names that were already taken',
    'release_candidates_missing': 'press releases whose page is missing',
    'nocopy_rows_without_copy': 'rows that have no saved copy',
    'origin_wanted': 'stories where the first publisher should be found',
    'conflicts': 'cells where the update disagrees with the workbook (the workbook keeps its value)',
    'date_review': 'dates to check',
    'av_date_review': 'audio or video dates to check',
    'reprint_untested': 'reprints that could not be compared with the original (no text to compare)',
    'reprint_check': 'possible reprints to check',
    'outlet_unresolved': 'outlets whose kind (print, online, TV...) is unknown',
    'outlet_new': 'outlets the tracker has not seen before',
    'outlet_untyped': 'outlets with no classification rule yet',
    'gabriel_unclear': 'stories where it is unclear they are about Jesse Gabriel the Assemblymember',
    'unknown_story': 'rows that name a story the tracker does not have',
    'held': 'items held back',
    'print_pages': 'print pages that need clipping by hand',
    'backfill_finds': 'older stories found late',
    'queue_conflicts': 'review-queue decisions that conflict with the update',
}

REFUSALS = {
    'LOCKED': 'Another save is running right now. Wait a few minutes and try again.',
    'SHA_MISMATCH': 'The workbook is not the one the tracker last saved: it was changed outside the tracker (for example in Excel). '
                    'If that was on purpose, use "Accept the workbook as it is now", then bring the update in again.',
    'EXCEL_OPEN': 'Excel has the workbook open. Close it, then try again.',
    'NO_LEDGER': 'The tracker has not been told which workbook to trust yet. Use "Accept the workbook as it is now" once.',
    'UNCONFIRMED_PREVIOUS': 'The last save was never confirmed. It has to be sorted out before another save.',
    'INPUT_MISSING': 'A file the save needs is missing from the tracker folder.',
    'PIPELINE_MISMATCH': 'The tracker\'s own program files do not match their checksum list, so the save was refused. The folder may be damaged.',
    'VERIFY_FAILED': 'The save program checked its own work and found a problem, so it wrote nothing.',
    'OVERWRITE': 'The update would overwrite something already in the workbook, so it was refused.',
    'ROWCOUNT': 'The row counts did not add up, so nothing was written.',
    'FOREIGN_ROW': 'The update would touch a row it does not own, so nothing was written.',
    'TOKEN_STALE': 'The preview is out of date (something changed since you looked). Bring the update in again.',
    'BACKUP_FAILED': 'The backup of the workbook could not be made, so nothing was written.',
    'COMMIT_FAILED': 'The new workbook did not check out after it was written. Do not save again; tell Claude.',
    'BAD_ARGS': 'The save program could not read its inputs.',
}


def n(k, one, many=None):
    return f'{k} {one if k == 1 else (many or one + "s")}'


def zip_refused(e) -> str:
    base = ZIP_CODES.get(e.code, 'The update was refused.')
    return f'{base} Nothing was saved or changed. ({e.msg})'[:600]


def fingerprint_line(fp) -> str:
    cur, upd = (fp or {}).get('current') or '', (fp or {}).get('update') or ''
    if (fp or {}).get('status') == 'unknown':
        return fp.get('message', 'The workbook is not where the tracker expects it.')
    return ('This update was made from a different version of the workbook than the one in the tracker now '
            f'(update: {upd[:8]}, workbook now: {cur[:8]}). The workbook has changed since the "for Update" file was made, '
            'by a later save or an edit in Excel. Stories in the update may already be in the workbook, or others may be missing. '
            'The clean fix: make a new "for Update" file and run the Update station again. You can also use this update anyway; '
            'the save still checks everything and only fills blanks.')


def make_failed(r) -> str:
    return 'The "for Update" file could not be made: ' + str(r.get('error') or 'unknown problem')[:300]


def make_done(r, name) -> str:
    mb = r['bytes'] / 1e6
    return f'Made {name} ({mb:.1f} MB, {r["stories"]:,} stories, fingerprint {r["workbook_sha256"][:8]}).'


def refusal_text(res) -> str:
    ref = res.get('refusal') or {}
    code = ref.get('code')
    base = REFUSALS.get(code)
    tech = (ref.get('line') or res.get('line') or '').replace('Not written: ', '')
    if base:
        return f'{base} Nothing was changed.' + (f' ({tech[:200]})' if tech and code in ('VERIFY_FAILED', 'INPUT_MISSING', 'OVERWRITE', 'FOREIGN_ROW', 'BAD_ARGS') else '')
    return 'Nothing was changed. ' + tech[:300]


def _examples(items, k=3):
    out = []
    for it in items[:k]:
        if isinstance(it, dict):
            bit = it.get('outlet') or it.get('headline') or it.get('link') or it.get('aid') or it.get('story') or ''
            out.append(str(bit))
        else:
            out.append(str(it))
    return [o for o in out if o]


NOQUEUE_KEYS = ('fetch_plan', 'origin_wanted', 'queue_conflicts')


def needs_person(res) -> tuple[list, int]:
    jud = res.get('judgment') or {}
    lines, total = [], 0
    for key, items in jud.items():
        if key in NOQUEUE_KEYS:      # NOQUEUE-v1: the wanted-originals list and queue conflicts are not shown as a to-do
            continue
        if key == 'fetch_plan' or not isinstance(items, list) or not items:
            continue
        total += len(items)
        label = CATEGORIES.get(key, key.replace('_', ' '))
        ex = _examples(items)
        lines.append(f'{len(items)} {label}' + (f' (for example: {", ".join(ex)})' if ex else ''))
    return lines, total


def _diff_lines(res) -> list:
    d = res.get('diff') or {}
    lines = []
    for tab, k in (d.get('rows_added') or {}).items():
        if k:
            lines.append(f'{n(k, "row")} added to the {tab} tab')
    cf = sum((d.get('cells_filled') or {}).values())
    if cf:
        lines.append(f'{n(cf, "blank cell")} filled in')
    for key, k in (d.get('cells_changed') or {}).items():
        if k:
            lines.append({'reprint_count': f'{n(k, "reprint count")} updated',
                          'rel_derived': f'{n(k, "press-release cell")} recalculated'}.get(key, f'{k} cells changed ({key})'))
    lib = res.get('library') or {}
    if lib.get('pages_added'):
        lines.append(f'{n(len(lib["pages_added"]), "saved page")} added to the library')
    if lib.get('removed_moved'):
        lines.append(f'{n(len(lib["removed_moved"]), "file")} of removed stories moved aside (not deleted)')
    q = res.get('queued') or {}
    bits = [f'{n(q[k], lab)}' for k, lab in (('runs', 'run'), ('bills', 'bill'), ('releases', 'press release'), ('edits', 'hand edit'), ('reprints', 'reprint'))
            if q.get(k)]
    if bits:
        lines.append('The update carries ' + ', '.join(bits))
    if d.get('disallowed'):
        lines.append(f'{d["disallowed"]} changes were refused by the rules and are not included')
    return lines


def names_lines(res) -> list:
    """LIBFILES-v1 / STATIONNAMES: what the save's checks of the station's file names found (renames are listed, never silent)"""
    nm = res.get('names') or {}
    if not nm.get('present') or nm.get('error'):
        return ['The station\'s file names could not be checked (' + str(nm.get('error'))[:120] + ')'] if nm.get('error') else []
    out = [x for x in (nm.get('lines') or []) if x]
    ns = nm.get('not_saved') or []
    for x in ns[:5]:
        out.append(f"Not saved to the library: {str(x.get('file') or '').rsplit('/', 1)[-1]} ({x.get('why')})")
    if len(ns) > 5:
        out.append(f'... and {len(ns) - 5} more files not saved')
    return out


def preview_result(pv, uid) -> dict:
    code = pv.get('exit_code')
    ref = pv.get('refusal')
    if ref or code in (2, 4):
        return {'ok': False, 'update_id': uid, 'refused': (ref or {}).get('code'), 'locked': (ref or {}).get('code') == 'LOCKED', 'line': refusal_text(pv)}
    if code == 3:
        return {'ok': True, 'update_id': uid, 'can_save': False, 'headline': 'Nothing new in this update', 'lines': [
            'Everything in it is already in the workbook, or it carries nothing to write.'], 'needs_person': [], 'token': None, 'stage': 'previewed'}
    if code != 0 or not pv.get('diff'):
        return {'ok': False, 'update_id': uid, 'line': 'The preview did not finish: ' + str(pv.get('line') or pv.get('stderr') or 'no answer')[:300]}
    lines = _diff_lines(pv) + names_lines(pv)
    np_, total = needs_person(pv)
    warns = list(pv.get('warnings') or [])
    ph = (pv.get('photos') or {}).get('note')
    if ph:
        warns.append(ph)
    return {'ok': True, 'update_id': uid, 'stage': 'previewed', 'can_save': True, 'token': (pv['diff'] or {}).get('token'),
            'headline': 'If you press Save: ' + str(pv.get('line') or '').rstrip('.') + '.', 'lines': lines, 'needs_person': np_, 'needs_person_total': total,
            'warnings': warns, 'fingerprint': pv.get('fingerprint')}


def save_result(res) -> dict:
    code = res.get('exit_code')
    ref = res.get('refusal')
    if not res.get('written'):
        out = {'ok': False, 'written': False, 'locked': (ref or {}).get('code') == 'LOCKED' or bool(res.get('locked')), 'headline': 'Not saved. The workbook was not changed.',
               'lines': [res.get('line') if res.get('locked') and not ref else refusal_text(res)], 'warnings': []}
        if code == 3:
            out['lines'] = ['Nothing new to write.']
        return out
    lines = _diff_lines(res) + names_lines(res)
    wb = res.get('workbook') or {}
    if wb.get('backup'):
        lines.insert(0, f'Backup of the old workbook: {wb["backup"]}')
    if wb.get('after_sha'):
        lines.append(f'New workbook fingerprint: {wb["after_sha"][:8]}')
    warns = []
    sync = res.get('sync') or {}
    if sync.get('errors'):
        warns += ['Some page files could not be updated: ' + '; '.join(sync['errors'][:3])]
    lib = res.get('library') or {}
    if lib.get('partial'):
        warns.append('Some library files did not land. See the save log in data\\state\\logs.')
    pr = res.get('page_rebuild')
    if pr and not pr.get('ok'):
        warns.append('The workbook was saved, but the tracker page could not be rebuilt (' + str(pr.get('error'))[:150] + '). Use "Rebuild the page".')
    elif res.get('site_rebuilt') or (pr and pr.get('ok')):
        lines.append('The tracker page was rebuilt with the new stories')
    if code == 6:
        warns.append('The workbook was saved, but a log or ledger line could not be written. Tell Claude.')
    np_, total = needs_person(res)
    if total:
        lines.append(f'{n(total, "item")} are listed for a person to look at (see the run notes)')
    return {'ok': True, 'written': True, 'headline': 'Saved. ' + str(res.get('line') or '').rstrip('.') + '.', 'lines': lines, 'warnings': warns,
            'needs_person': np_}
