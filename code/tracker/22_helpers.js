/* ---------- helpers ---------- */
const tsvCell = v => String(v ?? '').replace(/[\t\n]+/g,' ');
function copy(text, ok, btn){
  const done = () => { toast(ok); if (btn) copiedFx(btn); };
  try { navigator.clipboard.writeText(text).then(done, fallback); } catch(e){ fallback(); }
  function fallback(){ const t = document.createElement('textarea'); t.value = text; t.style.position='fixed'; t.style.opacity='0'; document.body.appendChild(t); t.select(); try { document.execCommand('copy'); done(); } catch(e){ toast('Copying is blocked here. Select the text by hand.'); } t.remove(); }
}
/* a copy button flashes "Copied!" with a check, then goes back to its label */
function copiedFx(btn){
  if (!btn.dataset.label) btn.dataset.label = btn.textContent;
  clearTimeout(btn._cfx); btn.classList.remove('copied'); void btn.offsetWidth;
  btn.classList.add('copied'); btn.textContent = '✓ Copied!';
  btn._cfx = setTimeout(() => { btn.classList.remove('copied'); btn.textContent = btn.dataset.label; }, 1800);
}
let toastT; function toast(s){ const t = $('#toast'); t.textContent = s; t.hidden = false; clearTimeout(toastT); toastT = setTimeout(()=>t.hidden=true, 2800); }

