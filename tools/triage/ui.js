// Base commune des espaces du studio : selection, echappement, appels d'API, attente, message, dialogue,
// icones et sections repliables. Conventions dans docs/ui.md. A charger apres /ui.css, avant le script de la page.
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const usd = x => x == null ? '?' : Number(x).toFixed(2).replace('.', ',') + ' $';
const aide = t => t ? `<span class="aide">${t}</span>` : '';

// --- Icones : traits fins, couleur du texte. ic('nom') dans un bouton ; bi('nom', 'Libelle') pour une icone seule.
const ICONES = {
  lancer: '<path d="M7 4v16l13-8z"/>',
  chercher: '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/>',
  pause: '<path d="M8 5v14M16 5v14"/>',
  arret: '<rect x="6" y="6" width="12" height="12" rx="1"/>',
  refaire: '<path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.5"/><path d="M21 16l-5-5-8 9"/>',
  clip: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M8 4v16M16 4v16M3 9h5M3 15h5M16 9h5M16 15h5"/>',
  montage: '<circle cx="6" cy="7" r="2.5"/><circle cx="6" cy="17" r="2.5"/><path d="M8 8.5L20 18M8 15.5L20 6"/>',
  supprimer: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6"/>',
  copier: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>',
  haut: '<path d="M12 19V5M6 11l6-6 6 6"/>',
  bas: '<path d="M12 5v14M6 13l6 6 6-6"/>',
  ajouter: '<path d="M12 5v14M5 12h14"/>',
  telecharger: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
  valider: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  ecrire: '<path d="M4 20l1-4L16.5 4.5a2.1 2.1 0 0 1 3 3L8 19l-4 1zM14.5 6.5l3 3"/>',
  retoucher: '<path d="M5 19L16 8M14 6l4 4M18 3v3M16.5 4.5h3M6 5v2M5 6h2M19 14v2M18 15h2"/>',
  relire: '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  archiver: '<rect x="3" y="4" width="18" height="5" rx="1"/><path d="M5 9v11h14V9M10 13h4"/>',
  envoyer: '<path d="M21 3L10 14M21 3l-7 18-4-7-7-4z"/>',
  planche: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  analyser: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
  idee: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>',
  retour: '<path d="M15 5l-7 7 7 7"/>',
  chaine: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  fermer: '<path d="M6 6l12 12M18 6L6 18"/>',
  personnage: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-7 8-7s8 3 8 7"/>',
  lora: '<path d="M12 3l9 5-9 5-9-5zM3 13l9 5 9-5"/>',
  plier: '<path d="M7 9l5-5 5 5M7 15l5 5 5-5"/>',
  importer: '<path d="M12 15V4M7 9l5-5 5 5M5 20h14"/>',
};
const ic = n => `<svg class="ic" viewBox="0 0 24 24" aria-hidden="true">${ICONES[n] || ''}</svg>`;
const bi = (n, lab, attrs = '', cls = 's') => `<button class="i ${cls}" title="${esc(lab)}" aria-label="${esc(lab)}" ${attrs}>${ic(n)}</button>`;

// --- Sections repliables : <details data-sec="cle"${ouv('cle', true)}> ; l'etat choisi est retenu sur l'appareil.
const ouv = (cle, defaut = true) => { let v = null; try { v = localStorage.getItem('sec:' + cle); } catch (e) {} return (v === null ? defaut : v === '1') ? ' open' : ''; };
document.addEventListener('toggle', e => {
  const k = e.target.dataset && e.target.dataset.sec;
  if (k) try { localStorage.setItem('sec:' + k, e.target.open ? '1' : '0'); } catch (err) {}
}, true);

// --- Attente, message, dialogue : poses une fois dans la page.
document.body.insertAdjacentHTML('beforeend', `<div id="busy"><div><b id="busyt"></b><span class="mut" id="busys"></span></div></div>
<div id="toast" role="status"></div>
<dialog id="dlg"><b id="dlgt"></b><div class="chips" id="dlgc" style="flex-wrap:wrap;margin-top:10px"></div>
  <textarea id="dlgi" rows="2" placeholder="Consigne libre"></textarea>
  <div class="row"><span class="sp"></span><button id="dlgn">Annuler</button><button class="p" id="dlgo">Lancer</button></div></dialog>`);

async function api(path, body) {
  const r = await fetch(path, body ? {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)} : {});
  const j = await r.json().catch(() => ({ok: false, error: 'réponse illisible (' + r.status + ')'}));
  if (!j.ok) throw new Error(j.error || 'erreur');
  return j;
}
function toast(msg, ok) {
  const t = $('#toast'); t.textContent = msg; t.className = ok ? 'ok' : ''; t.style.display = 'block';
  clearTimeout(toast.t); toast.t = setTimeout(() => t.style.display = 'none', ok ? 2500 : 7000);
}
const essai = f => async (...a) => { try { return await f(...a); } catch (e) { busy(); toast(e.message); } };
function busy(msg) {
  clearInterval(busy.t); $('#busy').className = msg ? 'on' : '';
  if (!msg) return;
  const t0 = Date.now(); $('#busyt').textContent = msg;
  const tick = () => $('#busys').textContent = Math.round((Date.now() - t0) / 1000) + ' s. Vous pouvez verrouiller le téléphone : le résultat sera là au retour.';
  tick(); busy.t = setInterval(tick, 1000);
}
function demander(titre, chips) {
  return new Promise(res => {
    const d = $('#dlg'); $('#dlgt').textContent = titre; $('#dlgi').value = '';
    $('#dlgc').innerHTML = chips.map(c => `<span class="chip">${esc(c)}</span>`).join('');
    $('#dlgc').onclick = e => { if (e.target.classList.contains('chip')) $('#dlgi').value = e.target.textContent; };
    $('#dlgo').onclick = () => { d.close(); res($('#dlgi').value.trim()); };
    $('#dlgn').onclick = () => { d.close(); res(null); };
    d.oncancel = () => res(null);
    d.showModal();
  });
}
function copier(txt) {
  const ta = document.createElement('textarea'); ta.value = txt; document.body.appendChild(ta); ta.select();
  try { document.execCommand('copy'); toast('Copié', true); } catch (e) { toast('Copie impossible'); }
  ta.remove();
}
