#!/usr/bin/env python3
"""patch_manage.py - Manage panel cleanup (MANAGE-v1, agent-manage, 2026-10-27).

  python3 -I code/patch_manage.py FILE [FILE ...]      (build/js_merged.js, or an assembled index.html copy)
  python3 -I code/patch_manage.py --check FILE ...     (report only, write nothing)

Idempotent: each edit is skipped when its new text is already there; a file where an edit finds neither its old
nor its new text is left untouched and the script exits 1.

Edits:
 1. Author badge: pages published with the tracker count as author-checked. T24 read the byline of every saved copy
    once, and the sheet task (AUTO-v1) fills Author 1..N on new rows, so a blank Author on a published copy means
    "no byline found", not "not checked". Before: Manage badge 99+ ("972 items waiting", 954 of them authors).
    Pages added by hand on one computer are still offered for a byline pass.
 2. Saved copies pane: the retired folders ("Gabriel Press Archive", "Saved pages (TinyFish)") replaced by the
    Tracker library on the Mac; file matching also names the library file names (nb00034o-s00012.pdf).
 3. Definitions: sources include NewsBank; the Tone definition follows DECISIONS (a story without a saved copy is
    rated from its headline only when the headline names him), so it no longer says only saved copies are rated.
 4. Dead code: CONF_TEXT (Confirmed / Unconfirmed, the retired Confidence column) removed; nothing references it.
"""
import re, sys

EDITS = [
    ('author-checked',
     "Object.entries(j.articles || {}).forEach(([k, p]) => { const s = sidOf(k); if (!remote[s] || s === k) remote[s] = p; }); } } catch(e) {} }",
     "Object.entries(j.articles || {}).forEach(([k, p]) => { const s = sidOf(k); if (!remote[s] || s === k) remote[s] = p; }); "
     "/* MANAGE-v1: published copies had their bylines read (T24, AUTO-v1) */ Object.keys(remote).forEach(s => aChecked.add(s)); } } catch(e) {} }"),
    ('saved-folder',
     "<p>To make saved copies readable by everyone, put the files in the Gabriel Press Archive folder (or Saved pages (TinyFish), named by story code) in this project and press Refresh from files. Pages of stories found by Update database are saved there on their own.</p>",
     "<p>To add saved copies, drop the files on the drop zone above; they are matched to stories by file name. Pages of stories found by Update database are cleaned and saved to the Tracker library on the Mac (Desktop/Tracker library/&lt;year&gt;/) when the sheet task runs.</p>"),   # F7: Refresh does not pick up files put in the library by hand
    ('saved-names',
     "<i>2026-10-13 - CalMatters - One area Democrats GOP agree…html</i>) or the story code.",
     "<i>2026-10-13 - CalMatters - One area Democrats GOP agree…html</i>), the story code (<i>s00012</i>) or the library file name (<i>nb00034o-s00012.pdf</i>)."),
    ('defs-sources',
     "<p>Stories were found through web searches, outlet tag pages, the Legislative Jewish Caucus news archive and two ProQuest news database exports.",
     "<p>Stories were found through web searches, outlet tag pages, the Legislative Jewish Caucus news archive, NewsBank searches and two ProQuest news database exports."),
    ('defs-tone',
     "Claude rates tone by reading the saved copy, so only stories with a saved copy are rated (${fmt(D.filter(rated).length)} so far).",
     "Claude rates tone by reading the saved copy. A story without one is rated from its headline only when the headline names him (${fmt(D.filter(rated).length)} rated so far)."),
    ('author-ok-note',
     "'Every saved page has been checked for an author', pa ? 'Press Refresh from files to have Claude read the bylines. <button class=\"linkbtn\" data-afind>Find authors now</button>' : 'Stories without a saved copy are left blank.'",
     "'Every saved page has been checked for an author', pa ? 'Press Refresh from files to have Claude read the bylines. <button class=\"linkbtn\" data-afind>Find authors now</button>' : 'Saved pages with no byline, and stories without a saved copy, have no author.'"),
]
CONF_RE = re.compile(r"\nconst CONF_TEXT = \{'Confirmed':[^\n]*\};[^\n]*(?=\n)")


def patch(text):
    out, notes, bad = text, [], []
    for name, old, new in EDITS:
        if new in out:
            notes.append(f'{name}: already applied')
        elif out.count(old) == 1:
            out = out.replace(old, new); notes.append(f'{name}: applied')
        else:
            bad.append(f'{name}: anchor found {out.count(old)} times')
    m = CONF_RE.findall(out)
    if not m:
        notes.append('conf-text: already removed')
    elif len(m) == 1 and out.count('CONF_TEXT') == 1:
        out = CONF_RE.sub('', out); notes.append('conf-text: removed')
    else:
        bad.append(f'conf-text: {len(m)} definitions, {out.count("CONF_TEXT")} references - left')
    return out, notes, bad


def main(argv):
    check = '--check' in argv
    files = [a for a in argv if a != '--check']
    if not files:
        print(__doc__); return 2
    rc = 0
    for f in files:
        t = open(f, encoding='utf-8').read()
        out, notes, bad = patch(t)
        if bad:
            rc = 1; print(f'{f}: NOT PATCHED - ' + '; '.join(bad + notes)); continue
        if out == t:
            print(f'{f}: unchanged ({"; ".join(notes)})')
        elif check:
            print(f'{f}: would change ({"; ".join(notes)})')
        else:
            open(f, 'w', encoding='utf-8').write(out); print(f'{f}: patched ({"; ".join(notes)})')
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
