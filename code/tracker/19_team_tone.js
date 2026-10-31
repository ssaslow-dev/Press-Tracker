/* ---------- team tone: anyone can correct a rating ---------- */
async function setTeamTone(id, tone){
  if (!TONE_OK.has(tone)) return;
  const t = { tone, why: `Set by the team on ${dateLabel({date:TODAY, prec:'day'})}.`, rated: TODAY, by: 'Team' };
  applyTone(id, t); lsSave(id, t);
  let ok = false; if (tdb){ try { await tdb.collection('tones').doc(id).set(t); ok = true; } catch(e){} }
  toast(ok ? `Tone set to ${tone} for everyone` : `Tone set to ${tone} on this computer`);
  render(); if (S.openId===id) openViewer(id);
}

