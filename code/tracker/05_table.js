/* ---------- table ---------- */
function sortRows(rows){
  const {key, dir} = S.sort;
  /* REVIEW4-PAGE-v1 E13: a headline sorts by its first letter or digit (leading quote marks ignored), and non-Latin headlines come after the Latin ones in either direction */
  const lead = r => String(r[key]).toLowerCase().replace(/^[^\p{L}\p{N}]+/u, ''), nl = r => key === 'hl' && /^[^\u0000-\u024f]/.test(lead(r)) ? 1 : 0;
  const val = r => key==='rep' ? r.pick : key==='reach' ? REACH_ORDER.indexOf(primaryReach(r)) : key==='tone' ? TONE_ORDER.indexOf(r.tone) : key==='hl' ? lead(r) : String(r[key]).toLowerCase();
  return rows.slice().sort((a,b) => { const na = nl(a), nb = nl(b); if (na !== nb) return na - nb; const x = val(a), y = val(b); if (x<y) return -dir; if (x>y) return dir; return b.date.localeCompare(a.date); });
}
function renderTable(rows){
  const sorted = sortRows(rows);
  const pages = Math.max(1, Math.ceil(sorted.length / S.per));
  if (S.page >= pages) S.page = pages-1;
  const slice = sorted.slice(S.page*S.per, S.page*S.per+S.per);
  document.querySelectorAll('th button[data-sort]').forEach(b => { if (b.dataset.sort===S.sort.key) b.dataset.dir = S.sort.dir<0?'↓':'↑'; else delete b.dataset.dir; });
  $('#tbody').innerHTML = slice.length ? slice.map(r => `
    <tr data-id="${r.id}" class="${r.id===S.openId?'on':''}" tabindex="0">
      <td class="x"><input type="checkbox" data-pick="${r.id}" ${S.pick.has(r.id)?'checked':''} aria-label="Tick this story"></td>
      <td class="d">${dateLabel(r)}</td>
      <td class="h"><div class="hl">${esc(r.hl)}</div>${r.hl_en ? `<div class="hl-en">${esc(r.hl_en)}</div>` : ''}${S.q && !qHitMeta(r) ? ftSnippet(r) : ''}<div class="ol"><span class="mdate">${dateLabel(r)}</span><span>${r.pub ? `<button type="button" class="tlink" data-pub="${esc(r.pub)}" title="Filter to ${esc(r.pub)}">${esc(r.outlet)}</button>` : esc(r.outlet)}</span>${r.authors.length?`<span class="by">By ${r.authors.map(a => `<button type="button" class="tlink" data-author="${esc(a)}" title="Filter to stories by ${esc(a)}">${esc(a)}</button>`).join(', ')}</span>`:''}${badges(r, true)}${r.bills.length ? `<span class="bchips ol-bills">${r.bills.map(b => `<button type="button" class="bchip" data-bill="${esc(b)}" title="Filter to ${esc(b)}">${esc(b)}</button>`).join('')}</span>` : ''}</div></td>
      <td class="t"><button type="button" class="tag tlink" data-fk="topic" data-fv="${esc(r.topic)}" title="Filter to ${esc(r.topic)}"><span class="sw" style="background:${colorFor('topic',r.topic)}"></span>${esc(r.topic)}</button>${r.bills.length ? `<span class="bchips">${r.bills.map(b => `<button type="button" class="bchip" data-bill="${esc(b)}" title="Filter to ${esc(b)}${billName(b) ? ': ' + esc(billName(b)) : ''}">${esc(b)}</button>`).join('')}</span>` : ''}</td>
      <td class="rc">${reachTags(r).map(v => `<button type="button" class="tag tlink" data-fk="reach" data-fv="${esc(v)}" title="Filter to ${esc(v)}"><span class="sw" style="background:${colorFor('reach',v)}"></span>${esc(v)}</button>`).join(' · ')}</td>
      <td class="r">${r.pick||''}</td>
    </tr>`).join('') : `<tr><td colspan="6" class="empty">No stories match these filters. <button class="linkbtn" data-clear>Clear all filters</button></td></tr>`;
  const from = sorted.length ? S.page*S.per+1 : 0, to = Math.min(sorted.length, (S.page+1)*S.per);
  $('#pager').innerHTML = `<span class="mono">${fmt(from)}–${fmt(to)} of ${fmt(sorted.length)}</span>${anyFilter() ? '' : ' <span class="note">Word-for-word press-release copies are not stories here: <button type="button" class="linkbtn" data-tb-go="releases">Press releases tab ›</button></span>'}
    <span class="ctl"><label for="per">Per page</label><select id="per">${[25,50,100,250].map(n=>`<option ${n===S.per?'selected':''}>${n}</option>`).join('')}</select>
    <button data-pg="-1" ${S.page===0?'disabled':''}>Previous</button><span class="mono">${S.page+1} / ${pages}</span><button data-pg="1" ${S.page>=pages-1?'disabled':''}>Next</button></span>`;
  S._order = sorted.map(r=>r.id); S._pageIds = slice.map(r=>r.id); drawBulk();
}

