# Tracker JS changes for the new Reach values (Ethnic, International, multi-tag)

Source checked: `lib/build/js_merged.js` (line numbers as of 2026-10-27 00:58). CSS tokens live in the page `<style>` (see `lib/build/index_new.html` lines 15, 31, 43). Not edited by agent-reach-ethnic.

## 1. Reach value list (line 64)

Replace

```js
const REACH_ORDER = ['National','Statewide California','District & Valley','California regional & local','Jewish press','Spanish-language & ethnic','Trade, advocacy & blogs','Out-of-state local'];
```

with

```js
const REACH_ORDER = ['National','International','Statewide California','District & Valley','California regional & local','Jewish press','Spanish-language','Ethnic','Trade, advocacy & blogs','Out-of-state local'];
```

REACH_ORDER is used for: RANK.reach (65), table sort (636), chart series (880), heat-map rows (1039), reach bars (1055, limit 8 → change to 10), facet options (2918), Update-button picks (2031, 2559). All pick up the new list automatically except the bar limit.

## 2. Colors (line 62 and 68) — keep existing categories' colors unchanged

`colorFor` colors reach by index in RANK.reach and only has 8 slots (`i < 8`). Inserting values would shift every existing category's color, so map reach colors by name instead:

```js
const SLOTS = ['--s1','--s2','--s3','--s4','--s5','--s6','--s7','--s8','--s9','--s10'];
const REACH_SLOT = {'National':'--s1','Statewide California':'--s2','District & Valley':'--s3','California regional & local':'--s4','Jewish press':'--s5','Spanish-language':'--s6','Trade, advocacy & blogs':'--s7','Out-of-state local':'--s8','International':'--s9','Ethnic':'--s10'};
function colorFor(key, val){ if (key==='tone') return `var(${TONE_VAR[val]||'--tnr'})`; if (key==='reach') return REACH_SLOT[val] ? `var(${REACH_SLOT[val]})` : 'var(--sother)'; const i = RANK[key].indexOf(val); return i >= 0 && i < 7 ? `var(${SLOTS[i]})` : 'var(--sother)'; }
```

(Spanish-language inherits the old "Spanish-language & ethnic" slot --s6.) Add two tokens in all three palette blocks of the page CSS (light at line 15; dark at 31 and 43), next to `--s8`:

- light: `--s9:#1f7a8c; --s10:#9a6a1c;`
- dark (both blocks): `--s9:#4fb3c6; --s10:#d3a04a;`

(Proposed hues; check contrast against the existing s1–s8 with the dataviz validator before shipping.)

## 3. Other hard-coded labels

- Line 2178: `TF_REPRINT_REACH = new Set([... 'Spanish-language & ethnic'])` → replace with `'Spanish-language', 'Ethnic'` (keep the others). Decide whether `'International'` belongs (reprint-friendly wires abroad); suggested: no.
- Lines 507, 966, 1154, 1342 (`pmj` preset), 1735 ("major" = National or Statewide California): unchanged by name, but must use the tag-aware test in §4 (`hasReach(r,'National')`).
- Lines 967, 1217 (`r.reach === 'District & Valley'`): same, use `hasReach`.
- Sheet export (1589, 1747, 1894): write `reachTags(r).join('; ')` (sheet format: tags joined by "; ", primary first).

## 4. Multi-tag Reach (DECISIONS 2026-10-27: an outlet can have several Reach tags)

Data: `r.reach` becomes an array of tags, primary first (build step splits the sheet cell on "; "). Add once near line 347:

```js
const reachTags = r => Array.isArray(r.reach) ? r.reach : (r.reach ? String(r.reach).split(/;\s*/) : []);
const hasReach = (r, v) => reachTags(r).includes(v);
const primaryReach = r => reachTags(r)[0] || '';
```

- **Filters match any tag** — `vals()` (line 347): add `key === 'reach' ? reachTags(r) :` before the final `[r[key]]`. The facet test at line 438 (`vals(r,key).some(v => s.has(v))`) then matches any tag, and facet counts using `vals` count a story under each tag.
- **Charts count a story under each of its tags:**
  - `hbars` (930–931): build counts with `rows.forEach(r => (key==='reach' ? reachTags(r) : [r[key]]).forEach(v => c.set(v,(c.get(v)||0)+1)))`. Percent labels stay `v/rows.length` (shares can sum above 100%; say so in the footnote, e.g. "A story can count under more than one reach.").
  - Time chart (874): for `bk==='reach'` loop over `reachTags(r)` and add `w(r)` to each tag's series (and for `only`, test `hasReach(r, only)`). `fillOnly` (853): count each tag.
  - Heat map (1038): already uses `vals(r, rk)`, so it follows once `vals` is changed.
  - Brief / summary lines (507, 966, 1154) and home-district (967, 1217): replace `r.reach==='X'` with `hasReach(r,'X')`.
- **Table and story panel show tags joined by " · ":** line 651 renders one tag button; render one button per tag (each with its own swatch and `data-fv`), separated by " · ". Story panel factline (around 691) likewise, joined by " · ".
- **Table sort** (636): sort by `REACH_ORDER.indexOf(primaryReach(r))`.
- **Update button** (2031, 2559): `pick1(..., REACH_ORDER, ...)` returns one value; wrap as `[value]` (or allow a list from Claude's JSON and filter it through REACH_ORDER).
- **Edit form** (2918 `{k:'reach', opts:() => REACH_ORDER}`): needs a multi-select (checkbox chips) for reach; save as an array.
- **Saved filters / URL state** (340) are per value and work unchanged.
