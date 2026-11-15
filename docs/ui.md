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
- Atelier, page d'un projet : les aides sont repliees derriere un « i » (toucher pour ouvrir, bouton de l'en-tete
  pour tout afficher, `body.aides`) ; une aide qui porte `.avt` ou contient `.err` reste visible.
- Atelier, page d'un projet : la colonne de travail suit l'ordre du geste (Preparer, Scenes, Produire, Monter) ; ce
  qui vaut pour tout le projet va dans le panneau de cote (`COTES`, `.cote`, `.cpan`), jamais dans la colonne.
  Un bouton `data-a="cote" data-c="<panneau>"` l'ouvre depuis la colonne.
- Le proprietaire lit et decide ; il ne retouche pas les prompts. Une scene est une tuile (`.grille` > `.scene`) :
  image, texte a l'ecran, verdict, note ; le texte et les reglages sont dans un pli ferme, et une remarque du
  controle des plans s'affiche dans la tuile avec le bouton qui ouvre le pli. Le panneau de cote est a gauche sur
  ecran large, en barre du bas sur telephone.
- Tout ce qui se compare se range en grille (`.grille` de `ui.css` : projets, scenes, fiches) ; un choix parmi une
  liste courte se fait par tuiles a cocher (`.tuiles` > `.lt`, `.on` choisie, `.off` indisponible, `.fo` force).
- Telephone d'abord : largeur 390 px, pas de tableau large, rien qui depende du survol.

## Ce que fournit ui.js

`$ $$ esc usd aide`, `ic bi ICONES`, `ouv`, `api(path, body)` (leve une erreur si `ok` est faux),
`essai(f)` (affiche l'erreur), `busy(msg)` (voile d'attente), `toast(msg, ok)`, `demander(titre, propositions)`
(dialogue avec consigne libre), `copier(txt)`. Le voile, le message et le dialogue sont poses dans la page par `ui.js`.

## Espaces

`/atelier` (reference), `/hub` (modeles et LoRA : `hub.html`, `hub.py`, API `/api/h/*`),
`/social` (reseaux grand public : `social.html`, `social.py`, API `/api/s/*`, images par `/sfile/<nom>`).

## Reste a faire

`home.html`, `index.html` (Tri) et `test.html` ont encore leurs styles propres ; les passer sur `/ui.css`
au moment ou on les retouche.
