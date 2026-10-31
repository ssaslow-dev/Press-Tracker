/* ---------- Manage panes: saved copies, data checks, definitions ---------- */
function renderAbout(){
  const el = $('#mgOther'); if (!el) return;
  const nSaved = D.filter(r=>hasHtml(r.id)).length, nLocal = local.size;
  if (S.mg==='log'){ el.innerHTML = renderLog(); return; }
  if (S.mg==='defs'){
    el.innerHTML = `
      <p>${fmt(D.length)} news stories that mention Jesse Gabriel, from ${YEARS[0]} through ${dateLabel(byId.get(D.find(r=>r.date===LAST).id))}. Each story is listed once. When the same story ran in other outlets, those are counted as reprints and named on the story.</p>
      <p>Stories were found through web searches, outlet tag pages, the Legislative Jewish Caucus news archive, NewsBank searches and two ProQuest news database exports. The tracker is built from one spreadsheet, which also holds every tone rating and author. <button class="linkbtn" data-dl="sheet">Download the spreadsheet</button></p>
      <dl>
        <dt>Issue</dt><dd>Why Gabriel appears in the story.</dd>
        <dt>Bills</dt><dd>Gabriel's bills the story covers, by number. A story can cover several. Found in the headline and saved copy, and in Claude's review of new stories.</dd>
        <dt>Reach</dt><dd>The kind of outlet that ran the story. National covers networks, wires and national papers. Statewide covers outlets like the LA Times, Sacramento Bee, CalMatters and Politico California. District &amp; Valley covers the Daily News and San Fernando Valley papers.</dd>
        <dt>How Gabriel appears</dt><dd>${pl(D.filter(r=>r.role==='Named in headline').length,'story','stories')} name him in the headline and ${pl(D.filter(r=>r.role==='Op-ed by Gabriel').length,'is an op-ed','are op-eds')} he co-wrote. The rest mention him in the text.</dd>
        <dt>Tone</dt><dd>How the story portrays Gabriel, from very positive to very negative. Claude rates tone by reading the saved copy. A story without one is rated from its headline only when the headline names him (${fmt(D.filter(rated).length)} rated so far). Anyone on the team can change a rating from the story panel.</dd>
        <dt>Author</dt><dd>Who wrote the story, one name per author (${fmt(D.filter(r=>r.authors.length).length)} stories have one). Editorial boards are listed as "&lt;Outlet&gt; Editorial Board". Job titles such as Staff Writer are shown with the story, not in the author list.</dd>
        <dt>Format</dt><dd>The kind of outlet or medium, such as Newspaper, TV or Podcast. Where the spreadsheet had none it was worked out from the outlet, such as TV for a TV station.</dd>
        <dt>Reprints</dt><dd>Other outlets that ran the same story. A few are a second edition or feed of the same outlet, and are labeled that way.</dd>
      </dl>`;
    return;
  }
  if (S.mg==='quality'){
    const n = f => D.filter(FLAGS[f].f).length, outlets = rankOf('pub'), one = outlets.filter(p => D.filter(r=>r.pub===p).length===1).length;
    const row = (cls, t, d, f) => `<div class="attn-i"><i class="${cls}"></i><div><b>${t}</b><span>${d}</span></div>${f ? `<button class="btn" data-flag="${f}">Show</button>` : '<span></span>'}</div>`;
    const pt = pendingTone().length, pa = pendingAuthor().length;
    const age = logAge();  /* HOMEUPKEEP-v1: upkeep moved here from Home's Needs attention */
    el.innerHTML = `<p>Records worth checking in the source spreadsheet. <b>Show</b> lists them in Clips.</p><div class="attn">
      ${U.found.length ? `<div class="attn-i"><i class="bad"></i><div><b>${pl(U.found.length,'new story','new stories')} found by Update database that Claude couldn’t confirm</b><span>Waiting for you to check and add them.</span></div><button class="btn" data-mgopen="upd">Review</button></div>` : ''}
      ${age > 3 ? `<div class="attn-i"><i class="warn"></i><div><b>No clips logged since ${dateLabel(byId.get(D.find(r=>r.date===LAST).id))}</b><span>That is ${pl(age,'day')}. Press Update database to check for new coverage.</span></div><button class="btn" data-runfind>Update database</button></div>` : ''}
      ${row(pt?'warn':'ok', pt ? `${pl(pt,'saved page')} waiting for a tone rating` : 'Every saved page has a tone', pt ? 'Press Refresh from files to have Claude rate them. <button class="linkbtn" data-trate>Rate now</button>' : 'Pages added later are rated the next time someone presses Refresh from files.', pt?'unrated':'')}
      ${row(pa?'warn':'ok', pa ? `${pl(pa,'saved page')} with no author checked` : 'Every saved page has been checked for an author', pa ? 'Press Refresh from files to have Claude read the bylines. <button class="linkbtn" data-afind>Find authors now</button>' : 'Saved pages with no byline, and stories without a saved copy, have no author.', pa?'noauthor':'')}
      ${row('warn', `${pl(n('searchlink'),'story links','stories link')} to a search, not the article`, 'Replace the link in the spreadsheet when the article is found.', 'searchlink')}
      ${row('info', `${fmt(outlets.length)} outlet names, ${fmt(one)} used only once`, 'Spelling variants of the same outlet split its count. Merging them in the spreadsheet makes the outlet charts more accurate.', '')}
    </div><div class="tone-status result-line"></div><div class="author-status result-line"></div>`;
    return;
  }
  el.innerHTML = `
    <p>Each story can hold a saved copy of the full article page or a PDF of the print clipping, so it stays readable if the original moves or goes behind a paywall. Claude also reads the saved copy to rate tone and find the author.</p>
    <div><div style="display:flex;justify-content:space-between;font-size:var(--fs-md);margin-bottom:4px"><span>${fmt(nSaved)} of ${fmt(D.length)} stories have a saved copy</span><span class="mono">${Math.round(nSaved/D.length*100)}%</span></div><div class="meter"><span style="width:${nSaved/D.length*100}%"></span></div></div>
    <div class="dropzone" id="drop">
      <b>Add saved pages</b>
      <p>Choose the saved .html pages or .pdf clippings, or a folder of them, or drop them here. A PDF shows the pages that name Gabriel, with his mentions highlighted on the page. Files are matched to stories by their name, either the date, outlet and headline (for example <i>2026-10-13 - CalMatters - One area Democrats GOP agree…html</i>), the story code (<i>s00012</i>) or the library file name (<i>nb00034o-s00012.pdf</i>). Pages you add here show only on this computer, but their tone and author are saved for everyone.</p>
      <div style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn primary" id="pickFiles">Choose files</button><button class="btn" id="pickDir">Choose a folder</button>${nLocal?`<button class="btn" id="clearLocal">Remove ${pl(nLocal,'page')} added here</button>`:''}</div>
      <div class="result-line" id="dropMsg"></div>
      <div class="tone-status result-line"></div>
    </div>
    <p>To add saved copies, drop the files on the drop zone above; they are matched to stories by file name. Pages of stories found by Update database are cleaned and saved to the Tracker library on the Mac (Desktop/Tracker library/&lt;year&gt;/) when you ask Claude in chat to “save the last run to the sheet”.</p>
    <div><button class="btn" id="copyIds">Copy story code list</button></div>`;
  const drop = $('#drop');
  drop.ondragover = e => { e.preventDefault(); drop.classList.add('over'); };
  drop.ondragleave = () => drop.classList.remove('over');
  drop.ondrop = e => { e.preventDefault(); drop.classList.remove('over'); ingest([...e.dataTransfer.files]); };
  $('#pickFiles').onclick = () => $('#fileIn').click();
  $('#pickDir').onclick = () => $('#dirIn').click();
  const cl = $('#clearLocal'); if (cl) cl.onclick = () => { local.clear(); IDB.clear(); FT.clear(); FTO.clear(); indexSaved(); render(); toast('Removed the pages added here'); };
  $('#copyIds').onclick = () => copy(['Story code\tFile name\tDate\tOutlet\tHeadline\tLink'].concat(D.map(r=>[r.id, r.id+'.html', r.date, r.outlet, r.hl, r.plink||r.link].map(tsvCell).join('\t'))).join('\n'), 'Copied the story code list. Paste it into a spreadsheet.');
}
