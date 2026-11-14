# Base d'interface du studio (14/11/2026)

Tous les espaces du studio (`tools/triage/*.html`) partagent deux fichiers servis par `triage.py` :
`/ui.css` (jetons, composants) et `/ui.js` (utilitaires, icones, sections repliables). L'Atelier est la
page de reference. Un nouvel espace part de ce squelette :

```html
<link rel="stylesheet" href="/ui.css">
<style>/* seulement les regles propres a la page */</style>
<header><div class="l1"><a href="/">Studio</a><b>Nom</b><span class="sp"></span><small id="etat"></small></div>
  <div class="chips" id="onglets"></div></header>
<main id="vue"></main>
<script src="/ui.js"></script>
<script>/* script de la page */</script>
```

## Regles

- Aucun emoji, nulle part. Les ideogrammes sont les icones SVG de `ui.js` : `ic('nom')` dans un bouton ou un lien,
  `bi('nom', 'Libelle')` pour un bouton reduit a son icone (le libelle devient `title` et `aria-label`).
  Une icone qui manque s'ajoute dans `ICONES` (24 x 24, traits, sans remplissage), jamais dans la page.
- Couleurs et rayons : uniquement les jetons (`--bg --panel --fond --line --txt --mut --acc --ok --bad --warn`
  et leurs fonds `--acc-bg --ok-bg --bad-bg --warn-bg`). Pas de couleur en dur dans une page.
- Un seul bouton principal (`.p`) par bloc : l'action attendue. `.d` pour ce qui detruit, `.s` pour les
  actions secondaires d'une ligne. Cible tactile : 38 px (32 px en `.s`).
- Une action qui coute ou qui dure s'ecrit dans une liste `.acts` : le bouton a gauche, ce qu'il fait et
  ce qu'il coute a droite (`<div class="act"><button>..</button><span class="mut">..</span></div>`).
  Un bouton indisponible dit pourquoi dans cette note, il ne disparait pas.
- Une page longue se decoupe en sections repliables numerotees dans l'ordre du travail :
  `<details class="sec" data-sec="cle"${ouv('cle', true)}><summary><span class="n">1</span>Titre<small>resume</small></summary>`.
  `data-sec` fait retenir l'etat ouvert ou ferme sur l'appareil. `.pli` : repli leger a l'interieur d'un bloc.
  Le resume (`small`) dit l'etat quand la section est fermee.
- La navigation interne (onglets, temps, filtres) va dans l'en-tete collant, en `.chips` ; `.chip.on` = courant.
- Texte en francais, phrases courtes, pas de jargon ; une aide (`.aide`) sous un champ, pas dans une bulle.
- Telephone d'abord : largeur 390 px, pas de tableau large, rien qui depende du survol.

## Ce que fournit ui.js

`$ $$ esc usd aide`, `ic bi ICONES`, `ouv`, `api(path, body)` (leve une erreur si `ok` est faux),
`essai(f)` (affiche l'erreur), `busy(msg)` (voile d'attente), `toast(msg, ok)`, `demander(titre, propositions)`
(dialogue avec consigne libre), `copier(txt)`. Le voile, le message et le dialogue sont poses dans la page par `ui.js`.

## Reste a faire

`home.html`, `index.html` (Tri) et `test.html` ont encore leurs styles propres ; les passer sur `/ui.css`
au moment ou on les retouche.
