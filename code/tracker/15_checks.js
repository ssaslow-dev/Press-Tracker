/* ---------- checks: filters that only Manage and Today set ---------- */
const FLAGS = {
  searchlink: { label:'Links to a search, not the article', f: r => r.lstat==='Search link only' },
  early: { label:'Dated before 2014', f: r => r.year > 0 && r.year < 2014 },
  unrated: { label:'Saved copy, no tone yet', f: r => hasHtml(r.id) && !rated(r) },
  noauthor: { label:'Saved copy, no author yet', f: r => hasHtml(r.id) && !r.author },
  notes: { label:'Has a team note', f: r => NOTES.has(r.id) },
  foreign: { label:'Not in English', f: r => !!r.lang },
  notr: { label:'Not in English, headline not translated', f: r => r.lang && !r.hl_en },
  picked: { chip:'Reprints', label:'Reprinted in other outlets', f: r => r.pick > 0 },
  nopick: { chip:'Reprints', label:'No reprints', f: r => !r.pick },
  relcopy: { chip:'Press release', label:'Press release copies', f: r => relsOf(r.id).some(x => x.type === 'copy') },   /* RELRULE-v1 (kept for saved views / links) */
  /* RELCLIPS-v1 (rp-clips 2026-10-28, RELPLAN): every release relation, read generically from relsOf (01_authors.js); a story's
     best relation decides, so the three values split the stories: "From" tiers (copy / nearcopy / text / quote: the story
     uses the release's words), else any other tier (bill / topic / pre / later / a new one), else none */
  relfrom: { chip:'Press release', label:'Ran release text', f: r => relKind(r) === 'from' },
  relrel: { chip:'Press release', label:'Related to a release', f: r => relKind(r) === 'rel' },
  relnone: { chip:'Press release', label:'No release', f: r => relKind(r) === '' },
};
/* RELCLIPS-v1: 'from' | 'rel' | '' for a story; REL_FILTERS = the Clips "Press release" facet's buttons ([flag key, label]) */
function relKind(r){ const a = relsOf(r.id); return !a.length ? '' : a.some(x => relIndex().from(x.type)) ? 'from' : 'rel'; }
const REL_FILTERS = [['', 'Any'], ['relfrom', 'Ran release text'], ['relrel', 'Related to a release'], ['relnone', 'No release']];
const REL_FLAG = { relcopy: 1, relfrom: 1, relrel: 1, relnone: 1 };

