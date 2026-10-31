/* ---------- Manage: badge and panes ---------- */
const logAge = () => Math.round((new Date(TODAY) - new Date(LAST)) / 864e5);  /* HOMEUPKEEP-v1 */
function drawBadge(){
  const n = pendingTone().length + pendingAuthor().length + U.found.length + (logAge() > 3 ? 1 : 0);  /* HOMEUPKEEP-v1: + an out-of-date log */
  const b = $('#mgBadge'); b.hidden = !n; b.textContent = n > 99 ? '99+' : n;
  $('#updBtn').title = n ? `${pl(n,'item')} waiting: new finds, unrated pages or authors to check` : 'Review finds, saved copies, data checks and definitions';
}
function drawMg(){
  document.querySelectorAll('#mgTabs [data-mg]').forEach(b => b.setAttribute('aria-pressed', b.dataset.mg===S.mg));
  const u = S.mg==='upd';
  $('#updBody').hidden = !u; $('#updFoot').hidden = !u; $('#mgOther').hidden = u;
  if (u) drawUpd(); else renderAbout();
}
const nrm = s => String(s||'').toLowerCase().replace(/&amp;/g,'&').replace(/[^a-z0-9]+/g,'');
const byDate = new Map(); D.forEach(r => { (byDate.get(r.date) || byDate.set(r.date, []).get(r.date)).push(r); });
function matchFile(name, txt){
  const base = name.replace(/\.(html?|pdf)$/i,'').trim();
  const bl = base.toLowerCase(), byName = byId.has(bl) ? bl : byId.has(sidOf(bl)) ? sidOf(bl) : AID_OF.get(bl); if (byName && byId.has(byName)) return byName;
  // library names: <nb|pq|ws><Article ID><o|r>-s<Story ID> (nb00034o-s00012.pdf), or without the Story ID part
  const lib = bl.match(/^(?:nb|pq|ws)?(\d{5})[or]?(?:-(s\d{5}))?$/);
  if (lib){ if (lib[2] && byId.has(lib[2])) return lib[2]; const v = AID_OF.get(lib[1]); if (v && byId.has(v)) return v; }
  const m = base.match(/^(\d{4}-\d{2}(?:-\d{2})?)/);
  const title = nrm((txt.match(/<title[^>]*>([\s\S]*?)<\/title>/i)||[])[1]);
  const fits = (r, s) => { const h = nrm(r.hl); return s && h && (s.includes(h) || (s.length > 24 && h.startsWith(s.slice(-Math.min(s.length, h.length))))); };
  if (m){ const rest = nrm(base.slice(m[1].length)); const c = (byDate.get(m[1])||[]).filter(r => fits(r, rest) || (title && nrm(r.hl)===title)); if (c.length===1) return c[0].id; }
  if (title){ const c = D.filter(r => nrm(r.hl)===title || title.endsWith(nrm(r.hl))); if (c.length===1) return c[0].id; }
  return null;
}
async function ingest(files){
  let ok = 0, miss = 0; const added = [];
  for (const f of files){
    const isPdf = /\.pdf$/i.test(f.name);
    if (!isPdf && !/\.html?$/i.test(f.name)) continue;
    let txt = isPdf ? '' : await f.text();
    const id = matchFile(f.name, txt);
    if (!id){ miss++; continue; }
    if (isPdf){
      const m = $('#dropMsg'); if (m) m.textContent = `Reading ${f.name}…`;
      try { txt = await pdfFileToHtml(f, byId.get(id)); } catch(e){ miss++; continue; }
    }
    if (!isPdf) txt = cleanLocal(id, txt); /* CLEAN-v1 */
    local.set(id, txt); IDB.put(id, txt); indexHtml(id, txt); ok++; added.push(id);
  }
  render();
  const msg = `Added ${pl(ok,'saved page')}.` + (miss ? ` ${pl(miss,'file')} could not be matched to a story.` : '');
  toast(msg); const m = $('#dropMsg'); if (m) m.textContent = msg;
  toneStatus(); authorStatus();
  // saved pages of stories not in English are translated as soon as they are added: headline and whole story
  translateNew(added);
}

/* downloads: the source spreadsheet is published beside the page; the CSV is built from the listed clips */
const SHEET_URL = 'data/sheet.json';
async function saveFile(filename, data){
  const C = window.claude, dl = C && C.use ? await C.use('downloads').catch(()=>null) : null;
  if (dl){ try { await dl.save({filename, data}); } catch(e){ if (e && e.code==='rate_limited') toast('A download is already waiting for you to confirm.'); else if (!e || e.code!=='declined') toast('Downloads are not available in this view.'); } return; }
  const u = URL.createObjectURL(data instanceof Blob ? data : new Blob([data])); const a = document.createElement('a'); a.href = u; a.download = filename; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(u), 5000);
}
/* RELCLIPS-v1 (rp-clips 2026-10-28): CSV press-release columns for every release relation (relsOf, 01_authors.js), split as the
   story panel: "From press release" = copy / nearcopy / text / quote, "Related press release" = any other tier; several
   releases are joined with " | ", best evidence first; "... how" = the evidence phrase per release */
function relCsvCols(){
  const g = (r, from) => relsOf(r.id).filter(x => relIndex().from(x.type) === from), j = (a, f) => a.map(f).join(' | ');
  const url = x => x.rel.url || '', how = x => relIndex().ev(x.type) || x.type;
  return [['From press release', r => j(g(r, true), x => x.rel.title)], ['From press release link', r => j(g(r, true), url)], ['From press release how', r => j(g(r, true), how)],
    ['Related press release', r => j(g(r, false), x => x.rel.title)], ['Related press release link', r => j(g(r, false), url)], ['Related press release how', r => j(g(r, false), how)]];
}
async function download(kind){
  document.querySelectorAll('.dlmenu[open]').forEach(d => d.open = false);
  if (kind==='sheet'){
    let j = null; try { const r = await fetch(SHEET_URL, {cache:'no-cache'}); if (r.ok) j = await r.json(); } catch(e){}
    if (!j || !j.b64){ toast('The spreadsheet could not be loaded right now.'); return; }
    const bin = atob(j.b64), bytes = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return saveFile(j.filename || 'Jesse_Gabriel_Mentions.xlsx', new Blob([bytes], {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}));
  }
  const rows = exportRows(), q = v => { const t = String(v ?? ''); return /[",\n]/.test(t) ? '"' + t.replace(/"/g,'""') + '"' : t; };
  const cols = [['Story code','id'],['Date','date'],['Outlet','outlet'],['Publisher','pub'],['Author / byline','author'],...Array.from({length: Math.max(1, ...D.map(r => (r.authors||[]).length))}, (_, i) => [`Author ${i+1}`, r => (r.authors||[])[i] || '']),['Author title','atitle'],['Headline','hl'],['Language','lang'],['Headline in English','hl_en'],['Issue','topic'],['Bills',r=>r.bills.join('; ')],['Reach','reach'],['Format','media'],['Channel',r=>avChannel(r)],['Show',r=>avShow(r)],['How Gabriel appears','role'],['Mention depth','depth'],['Quoted','quoted'],['Reprints','pick'],['Reprinted in','also'],['Tone',r=>rated(r)?r.tone:''],['Tone note','twhy'],['Saved copy',r=>hasHtml(r.id)?'Yes':''],['Link',r=>exportLinkBest(r)],['Library link (login)',r=>exportLibLink(r)],['Aired (Pacific)',r=>avtLine(r)],['ProQuest link','pq'],...relCsvCols()];   /* RELEASES-v2 -> RELCLIPS-v1; AVSHOW-v1 Channel/Show */
  const csv = '\ufeff' + [cols.map(c=>c[0]).join(',')].concat(rows.map(r => cols.map(([,k]) => q(typeof k==='function' ? k(r) : r[k])).join(','))).join('\r\n');
  saveFile(`Gabriel clips ${TODAY}.csv`, new Blob([csv], {type:'text/csv'}));
}
document.addEventListener('click', e => { const b = e.target.closest('[data-dl]'); if (b) download(b.dataset.dl); else if (!e.target.closest('.dlmenu')) document.querySelectorAll('.dlmenu[open]').forEach(d => d.open = false); });

