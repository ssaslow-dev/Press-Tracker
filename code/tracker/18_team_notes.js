/* ---------- team notes ---------- */
const NOTES = new Map(); let notesCol = null; const N_LS = 'jg2-notes';
function lsNotes(){ try { return JSON.parse(localStorage.getItem(N_LS)||'{}') || {}; } catch(e){ return {}; } }
function initNotes(db){
  Object.entries(lsNotes()).forEach(([k,v]) => { const s = sidOf(k); if (byId.has(s) && v && v.text && (s === k || !NOTES.has(s))) NOTES.set(s, v); });
  if (!db) return;
  notesCol = db.collection('notes');
  notesCol.onSnapshot(snap => {
    oldFirst(snap.docs).forEach(d => { const x = d.data(), id = sidOf(d.id); if (x && typeof x.text==='string'){ if (x.text.trim()) NOTES.set(id, { text: x.text.slice(0,2000), at: String(x.at||'').slice(0,10) }); else NOTES.delete(id); } });
    const t = $('#tnote'); if (t && S.openId && document.activeElement!==t) t.value = (NOTES.get(S.openId)||{}).text || '';
    rerender();
  }, () => {});
}
let noteT;
function saveNote(id, text){
  clearTimeout(noteT);
  noteT = setTimeout(async () => {
    const v = { text: text.slice(0,2000), at: TODAY }; if (text.trim()) NOTES.set(id, v); else NOTES.delete(id);
    const l = lsNotes(); if (text.trim()) l[id] = v; else delete l[id]; try { localStorage.setItem(N_LS, JSON.stringify(l)); } catch(e){}
    let ok = false; if (notesCol){ try { await notesCol.doc(id).set(v); ok = true; } catch(e){} }
    const m = $('#tnoteMeta'); if (m && S.openId===id) m.textContent = ok ? 'Saved for the team.' : 'Saved on this computer only.';
  }, 600);
}

