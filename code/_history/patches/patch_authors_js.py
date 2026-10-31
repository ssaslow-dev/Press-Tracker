"""T30: tracker JS change for split authors. Anchor-based; every anchor must match exactly once (else exit 1).
Usage: python3 -I patch_authors_js.py IN.js OUT.js
Data contract it expects (build_data.py patch): each record has `authors` (list, from Author 1..N) and `atitle` (Author title);
`author` stays the raw "Author / byline". Records without `authors` fall back to splitAuthors(author) as before.
"""
import sys
src, dst = sys.argv[1:3]
js = open(src, encoding='utf-8').read()

R = []
# 1. one entry per person: normalized key + canonical display form
R.append(("const splitAuthors = s => String(s||'').split(/\\s*;\\s*/).map(x => x.trim()).filter(Boolean);\n",
"""const splitAuthors = s => String(s||'').split(/\\s*;\\s*/).map(x => x.trim()).filter(Boolean);
/* T30: a story lists each author separately (sheet columns Author 1..N). authorKey = build-side author_key():
   accents, case, periods, commas, extra spaces and single-letter middle initials ignored, so "Jeremy B. White" and
   "Jeremy B White" are one entry. ACANON: key -> display form used most often (ties: the longer form).
   Spelling variants that differ otherwise (Haven Daly / Haven Daley) are NOT merged here; they are in Sammy's review queue. */
const authorKey = a => { let w = String(a||'').normalize('NFKD').replace(/[\\u0300-\\u036f]/g,'').replace(/[‘’]/g,"'").toLowerCase().replace(/[.,]/g,' ').replace(/\\s+/g,' ').trim().split(' ');
  if (w.length > 2) w = [w[0], ...w.slice(1,-1).filter(x => x.length > 1), w[w.length-1]]; return w.join(' '); };
const ACANON = new Map();
function buildAuthorCanon(rows){ const c = new Map();
  rows.forEach(r => (r.authors||[]).forEach(a => { a = String(a||'').trim(); if (!a) return; const k = authorKey(a); const m = c.get(k) || c.set(k, new Map()).get(k); m.set(a, (m.get(a)||0)+1); }));
  ACANON.clear(); c.forEach((m, k) => ACANON.set(k, [...m.entries()].sort((x,y) => y[1]-x[1] || y[0].length-x[0].length)[0][0])); }
const canonAuthors = list => { const seen = new Set(), out = [];
  (list||[]).forEach(a => { a = String(a||'').trim(); if (!a) return; const k = authorKey(a); if (seen.has(k)) return; seen.add(k);
    if (!ACANON.has(k)) ACANON.set(k, a); out.push(ACANON.get(k)); }); return out; };
/* author kind from the data (build_data: akinds, parallel to authors): person | board | staff | wire | org.
   Generic staff groups ("<Outlet> Staff", News Staff, Newsroom, Staff and Wire Reports) sit in ONE folded
   "Staff bylines" group at the end of the Reporter filter; on stories they stay normal author links. */
const AKIND = new Map();
const isStaffAuthor = a => AKIND.get(authorKey(a)) === 'staff';
function staffGroup(f, stf, c, sel){
  const q = (S.fq[f.key]||'').toLowerCase();
  const v = stf.filter(x => !q || x.toLowerCase().includes(q)).sort((a,b) => (c.get(b)||0)-(c.get(a)||0) || a.localeCompare(b));
  if (!v.length) return '';
  const on = v.filter(x => sel.has(x)).length, open = S.openFacets.has('author-staff') || !!q;
  return `<details class="facet fgroup" data-facet="author-staff" ${open?'open':''}><summary>Staff bylines<small>${on ? on+' on' : fmt(v.length)}</small></summary><div class="body"><div class="hint">Unsigned staff and newsroom credits, such as Daily News Staff.</div>${v.map(x => opt(f, x, c)).join('')}</div></details>`;
}
try { document.head.insertAdjacentHTML('beforeend', '<style>details.fgroup{padding:0 0 0 8px;border-bottom:0;border-top:1px dashed var(--line-2)}</style>'); } catch(e){}
"""))
# 2. search also matches every Author N and the title
R.append(("r.pub, r.author, r.text_en,", "r.pub, r.author, ...(r.authors||[]), r.atitle, r.text_en,"))
# 3. authors found at runtime go through the same canonical names
R.append(("function setAuthor(r, a){ r.author = a; r.authors = splitAuthors(a); r._s = searchStr(r); }",
          "function setAuthor(r, a){ r.author = a; r.authors = canonAuthors(splitAuthors(a)); r._s = searchStr(r); }"))
R.append(("D.forEach(r => { r.author = r.author || ''; r.authors = splitAuthors(r.author); });",
          "D.forEach(r => { r.author = r.author || ''; r.atitle = r.atitle || ''; r.authors = Array.isArray(r.authors) && r.authors.length ? r.authors.map(String) : splitAuthors(r.author); });\n"
          "D.forEach(r => (r.authors||[]).forEach((a, i) => { const k = (r.akinds||[])[i]; if (k) AKIND.set(authorKey(a), k); }));\n"
          "buildAuthorCanon(D); D.forEach(r => { r.authors = canonAuthors(r.authors); });"))
R.append(("    r.authors = splitAuthors(r.author); r._s = searchStr(r); r.pick = reprintCount(r);",
          "    r.atitle = r.atitle || ''; r.authors = canonAuthors(Array.isArray(r.authors) && r.authors.length ? r.authors : splitAuthors(r.author)); r._s = searchStr(r); r.pick = reprintCount(r);"))
# 4. author link -> canonical person (so X's link shows X's solo AND co-written stories)
R.append(("S.sel.author.add(b.dataset.author); go('db'); toast(`Showing stories by ${b.dataset.author}`);",
          "const who = canonAuthors([b.dataset.author])[0] || b.dataset.author; S.sel.author.add(who); go('db'); toast(`Showing stories by ${who}`);"))
# 5. cards: each author its own link (clip still opens the story when clicked elsewhere)
R.append(("${r.author?` · by ${esc(r.authors.join(', '))}`:''}",
          "${r.authors.length?` · by ${r.authors.map(a => `<button type=\"button\" class=\"tlink\" data-author=\"${esc(a)}\" title=\"Filter to stories by ${esc(a)}\">${esc(a)}</button>`).join(', ')}`:''}"))
R.append(("  const c = e.target.closest('.clip[data-id]'); if (c){ const list",
          "  if (e.target.closest('.clip [data-author]')) return; // author link inside a card: the document handler filters\n"
          "  const c = e.target.closest('.clip[data-id]'); if (c){ const list"))
# 6. table and story detail: show when any author; detail adds the title
R.append(("${r.author?`<span class=\"by\">By ${r.authors.map(", "${r.authors.length?`<span class=\"by\">By ${r.authors.map("))
R.append(("${r.author ? `<span>By ${r.authors.map(a => `<button class=\"linkbtn\" data-author=\"${esc(a)}\" title=\"See every clip by ${esc(a)}\">${esc(a)}</button>`).join(', ')}</span>` : ''}",
          "${r.authors.length ? `<span>By ${r.authors.map(a => `<button class=\"linkbtn\" data-author=\"${esc(a)}\" title=\"See every clip by ${esc(a)}\">${esc(a)}</button>`).join(', ')}${r.atitle ? ` <span class=\"atitle\">(${esc(r.atitle)})</span>` : ''}</span>` : ''}"))
# 7. export: byline + Author 1..N + Author title
R.append(("['Author','author'],",
          "['Author / byline','author'],...Array.from({length: Math.max(1, ...D.map(r => (r.authors||[]).length))}, (_, i) => [`Author ${i+1}`, r => (r.authors||[])[i] || '']),['Author title','atitle'],"))
R.append(("copy(['Date\\tOutlet\\tAuthor\\tHeadline", "copy(['Date\\tOutlet\\tAuthors\\tHeadline"))
R.append(("rows.map(r=>[r.date,r.outlet,r.author,r.hl,", "rows.map(r=>[r.date,r.outlet,(r.authors||[]).join('; ') || r.author,r.hl,"))
# 7b. Reporter filter: staff groups folded into one "Staff bylines" group at the end
R.append(("let vals = valuesOf(f.key).slice(), extra = '', more = '';",
          "let vals = valuesOf(f.key).slice(), extra = '', more = '', stf = [];\n    if (f.key === 'author'){ stf = vals.filter(isStaffAuthor); vals = vals.filter(v => !isStaffAuthor(v)); }"))
R.append(("all = valuesOf(f.key).length, noun", "all = valuesOf(f.key).filter(v => f.key !== 'author' || !isStaffAuthor(v)).length, noun"))
R.append(("vals = [...sel].filter(v => !shown.includes(v)).concat(shown);",
          "vals = [...sel].filter(v => !shown.includes(v) && !(f.key === 'author' && isStaffAuthor(v))).concat(shown);"))
R.append(("${vals.map(v=>opt(f,v,c)).join('')}${more}</div></details>`;",
          "${vals.map(v=>opt(f,v,c)).join('')}${more}${f.key === 'author' ? staffGroup(f, stf, c, sel) : ''}</div></details>`;"))
# 8. wording
R.append(("hint:'Who wrote the story. Found in saved copies, so most stories have none yet.'}",
          "hint:'Who wrote the story. Co-authors are listed one by one, and a co-written story counts for each of them.'}"))
R.append(("<dt>Author</dt><dd>Who wrote the story. Claude reads the byline of the saved copy, so only stories with a saved copy have one (${fmt(D.filter(r=>r.author).length)} so far).</dd>",
          "<dt>Author</dt><dd>Who wrote the story, one name per author (${fmt(D.filter(r=>r.authors.length).length)} stories have one). Editorial boards are listed as \"&lt;Outlet&gt; Editorial Board\". Job titles such as Staff Writer are shown with the story, not in the author list.</dd>"))

bad = []
for old, new in R:
    n = js.count(old)
    if n != 1: bad.append((n, old[:90])); continue
    js = js.replace(old, new)
if bad:
    for n, o in bad: print(f'anchor found {n}x: {o!r}')
    sys.exit(1)
open(dst, 'w', encoding='utf-8').write(js)
print(f'ok: {len(R)} replacements -> {dst}')
