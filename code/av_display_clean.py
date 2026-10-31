#!/usr/bin/env python3
"""av_display_clean.py - AVPREVIEW-v1 draft (agent-previewclean, 2026-10-28; Sammy comment de9c2baa).

Display-copy cleaner for AUDIO & VIDEO saved copies only (stories whose "Audio & video details" row has Item type
Episode / Broadcast segment / Video clip). It removes back-end text a reader should not see in the tracker's
saved-copy viewer: capture headers, file names, our own analyst fields, millisecond time codes, player/app UI text,
transcript-vendor boilerplate. It never touches the library files: it runs on the page text make_copies puts in
articles/<year>.json (raw library file and _original_html stay as they are).

Rules are data in av_rules.json (next to this file). Order:
  1. header   - the library's capture header <div> before the <h1> ("Outlet · date", URL, "Saved YYYY-MM-DD")
  2. pdfcap   - make_copies nb_page captions ("Text of the NewsBank/ProQuest PDF (...)", "· N words", NewsBank citation)
  3. fields   - <p><b>Label:</b> value</p> header fields of the podcast transcript pages (drop / rewrite per label)
  4. strip    - regex removals/rewrites inside text nodes (time-code ranges, shortcodes, copyright tails, jammed dates)
  5. kill     - a whole block (leaf block element or bare text node) whose text fully matches
  6. tail     - a block that starts site boilerplate; it and every later block go
  7. section  - a heading block + the following blocks matching its item pattern
  8. dedupe   - a block identical to the block before it; a block = "<h1 text> <later block>" (og title+description)
  9. note     - one reader note inserted under "Transcript excerpts" headings (replaces the dropped field lines)
Safety: a kill/section block of >= 40 words is kept (flag long_block); if more than 25% of the words would go the
page is returned unchanged (flag big_removal) unless the rule is a tail rule listed with allow_big.

API:  clean(html, lang='English') -> (html, report)   report = {removed: [[rule, text]], inserted: [...], flags: [...]}
CLI:  python3 -I av_display_clean.py IN.html OUT.html [--lang English]
"""
import json, os, re, sys
from bs4 import BeautifulSoup, NavigableString, Tag, Comment

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = json.load(open(os.path.join(HERE, 'av_rules.json'), encoding='utf-8'))
BLOCK = {'p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'figcaption', 'td', 'th', 'dt', 'dd', 'header', 'footer',
         'section', 'article', 'blockquote', 'ul', 'ol', 'figure', 'main', 'aside', 'nav', 'span', 'time', 'body'}
LEAF_EXCLUDE = {'body', 'article', 'main', 'section', 'ul', 'ol', 'figure'}
WORD = re.compile(r"[\w'’-]+", re.U)


def words(t):
    return len(WORD.findall(t or ''))


def norm(t):
    return re.sub(r'\s+', ' ', (t or '').replace('\xa0', ' ')).strip()


def C(p):
    return re.compile(p, re.I | re.S)


KILL = [(r['id'], C(r['re'])) for r in RULES['kill']]
LONG_OK = {r['id'] for r in RULES['kill'] if r.get('allow_long')}
STRIP = [(r['id'], C(r['re']), r.get('to', ''), r.get('lang'), C(r['gate']) if r.get('gate') else None) for r in RULES['strip']]
TAIL = [(r['id'], C(r['re']), r.get('allow_big', False)) for r in RULES['tail']]
SECTION = [(r['id'], C(r['head']), C(r['item'])) for r in RULES['section']]
FIELDS = RULES['fields']
NOTE = RULES['note']


def leaf_blocks(soup):
    """block elements with text and no block children (in document order)"""
    out = []
    for el in soup.find_all(True):
        if el.name not in BLOCK or el.name in LEAF_EXCLUDE:
            continue
        if any(isinstance(c, Tag) and c.name in BLOCK for c in el.descendants):
            continue
        if norm(el.get_text(' ')):
            out.append(el)
    return out


def bare_texts(soup):
    """text nodes sitting directly in a non-leaf container next to block children (e.g. body text after an <h1>)"""
    out = []
    for s in soup.find_all(string=True):
        if isinstance(s, Comment) or not norm(s):
            continue
        par = s.parent
        if par and par.name in ('script', 'style', 'title', 'head', 'html', '[document]'):
            continue
        if par and any(isinstance(c, Tag) and c.name in BLOCK for c in par.children):
            out.append(s)
    return out


def clean(html, lang='English'):
    rep = {'removed': [], 'inserted': [], 'flags': [], 'rewritten': []}
    if not html:
        return html, rep
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.body or soup
    h1 = soup.find('h1')
    h1t = norm(h1.get_text(' ')) if h1 else ''

    def drop(el, rule):
        t_ = norm(el.get_text(' ') if isinstance(el, Tag) else str(el))
        rep['removed'].append([rule, t_, words(t_)])
        el.extract() if isinstance(el, NavigableString) else el.decompose()

    # 1. capture header: the first <div> before the h1 holding "Outlet · date" / URL / "Saved …" lines
    for div in body.find_all('div', recursive=False)[:1]:
        if h1 and div.sourceline is not None and h1.sourceline is not None and (div.sourceline, div.sourcepos) > (h1.sourceline, h1.sourcepos):
            break
        parts, keep = [], []
        for node in list(div.contents):
            if isinstance(node, Tag) and node.name == 'br':
                continue
            t = norm(node.get_text(' ') if isinstance(node, Tag) else str(node))
            if not t:
                continue
            if any(re.fullmatch(p, t) for p in RULES['header']):
                parts.append(t)
            else:
                keep.append(t)
        if parts and not keep:
            rep['removed'].append(['header', ' | '.join(parts), sum(words(x) for x in parts)]); div.decompose()
        elif parts:
            for node in list(div.contents):
                t = norm(node.get_text(' ') if isinstance(node, Tag) else str(node)) if not (isinstance(node, Tag) and node.name == 'br') else ''
                if t in parts or (isinstance(node, Tag) and node.name == 'br'):
                    node.extract()
            rep['removed'].append(['header', ' | '.join(parts), sum(words(x) for x in parts)])

    # 2. make_copies nb_page captions
    for p in soup.select('p.pdf-cap'):
        t = norm(p.get_text(' '))
        if re.match(r'Text of the (NewsBank|ProQuest) PDF', t) or 'Available from NewsBank' in t or re.search(r'\bProQuest\b.*\bDocument URL\b', t):
            drop(p, 'pdfcap')
        else:
            new = re.sub(r'\s*·\s*\d[\d,]*\s+words\b', '', t)
            if new != t:
                rep['removed'].append(['pdfcap_words', re.search(r'\d[\d,]*\s+words', t).group(0), words(t) - words(new)])
                p.string = new

    # 3. podcast transcript header fields <p><b>Label:</b> value</p>
    for p in soup.find_all('p'):
        b = p.find('b')
        if not b or p.contents[0] is not b:
            continue
        lab = norm(b.get_text()).rstrip(':')
        f = FIELDS.get(lab)
        if not f:
            continue
        if f['do'] == 'drop':
            drop(p, 'field:' + lab)
        elif f['do'] == 'rewrite':
            t = norm(p.get_text(' '))
            new = re.sub(f['re'], f['to'], t)
            if new != t:
                rep['rewritten'].append(['field:' + lab, t, new])
                val = new.split(':', 1)[1].strip()
                for c in list(p.contents)[1:]:
                    c.extract()
                p.append(' ' + val)

    # 4. strip inside text nodes (a rule with a gate runs only on pages matching it)
    gate_ok = {}
    for s in list(soup.find_all(string=True)):
        if isinstance(s, Comment) or (s.parent and s.parent.name in ('script', 'style', 'title')):
            continue
        t = str(s); new = t
        for rid, rx, to, lg, gate in STRIP:
            if (lg and lg != lang) or (gate and not gate_ok.setdefault(rid, bool(gate.search(html)))):
                continue
            new2 = rx.sub(to, new)
            if new2 != new:
                rep['removed'].append(['strip:' + rid, norm(' | '.join(m.group(0) for m in rx.finditer(new))), words(new) - words(new2)])
                new = new2
        if new != t:
            s.replace_with(new)

    # 5-7. block rules
    total = words(soup.get_text(' '))
    blocks = leaf_blocks(soup) + bare_texts(soup)
    # document order
    order = {id(x): i for i, x in enumerate(soup.descendants)}
    blocks.sort(key=lambda x: order.get(id(x), 0))
    gone = set()
    tail_from = None
    for i, el in enumerate(blocks):
        t = norm(el.get_text(' ') if isinstance(el, Tag) else str(el))
        for rid, rx, big in TAIL:
            if rx.fullmatch(t) or rx.match(t):
                tail_from = (i, rid, big); break
        if tail_from:
            break
    if tail_from:
        i0, rid, big = tail_from
        cut = blocks[i0:]
        w = sum(words(norm(e.get_text(' ') if isinstance(e, Tag) else str(e))) for e in cut)
        if w > 0.25 * total and not big:
            rep['flags'].append(f'big_removal:tail:{rid}:{w}/{total}')
        else:
            for e in cut:
                gone.add(id(e)); drop(e, 'tail:' + rid)
    blocks = [b for b in blocks if id(b) not in gone]
    i = 0
    while i < len(blocks):
        el = blocks[i]
        t = norm(el.get_text(' ') if isinstance(el, Tag) else str(el))
        hit = next((rid for rid, rx in KILL if rx.fullmatch(t)), None)
        if hit:
            if words(t) >= 40 and hit not in LONG_OK:
                rep['flags'].append(f'long_block:{hit}')
            else:
                drop(el, 'kill:' + hit); blocks.pop(i); continue
        sec = next(((rid, it) for rid, hd, it in SECTION if hd.fullmatch(t)), None)
        if sec:
            j = i + 1
            while j < len(blocks):
                tj = norm(blocks[j].get_text(' ') if isinstance(blocks[j], Tag) else str(blocks[j]))
                if not sec[1].search(tj) or words(tj) >= 40:
                    break
                j += 1
            for e in blocks[i:j]:
                drop(e, 'section:' + sec[0])
            del blocks[i:j]; continue
        i += 1

    # 8. dedupe: same block twice in a row; og "title + description" block at the top
    texts = [norm(b.get_text(' ') if isinstance(b, Tag) else str(b)) for b in blocks]
    keep_b, prev = [], None
    for b, t in zip(blocks, texts):
        if prev is not None and t == prev and words(t) >= 3:
            drop(b, 'dedupe:repeat'); continue
        keep_b.append(b); prev = t
    blocks = keep_b
    texts = [norm(b.get_text(' ') if isinstance(b, Tag) else str(b)) for b in blocks]
    if h1t and blocks:
        first = texts[0]
        if first.startswith(h1t + ' ') and blocks[0] is not h1:
            rest = first[len(h1t):].strip()
            if rest and rest in texts[1:]:
                drop(blocks[0], 'dedupe:og_title_desc')

    # 9. reader note under "Transcript excerpts"
    for h in soup.find_all(['h2', 'h3']):
        if norm(h.get_text()) == 'Transcript excerpts' and rep['removed'] and any(r[0].startswith('field:') for r in rep['removed']):
            n = soup.new_tag('p'); n['class'] = 'src'; n.string = NOTE
            h.insert_after(n); rep['inserted'].append(NOTE)

    # safety: total removal
    # guard counts only line-shaped removals (kill); header, field, caption, dedupe and strip rules are exact
    risky = sum(r[2] for r in rep['removed'] if r[0].startswith('kill:'))
    if total and risky > 0.25 * total:
        rep['flags'].append(f'big_removal:{risky}/{total}')
        return html, {'removed': [], 'inserted': [], 'flags': rep['flags'], 'rewritten': []}
    out = str(soup)
    return out, rep


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('inp'); ap.add_argument('out'); ap.add_argument('--lang', default='English')
    a = ap.parse_args()
    h, r = clean(open(a.inp, encoding='utf-8').read(), a.lang)
    open(a.out, 'w', encoding='utf-8').write(h)
    print(json.dumps(r, ensure_ascii=False, indent=1))
