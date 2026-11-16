# Exploration : des vidéos faites avec l'aide d'une intelligence artificielle

Note de départ (17/11/2026) pour une conversation à part. Rien ici ne change la production.
Les conclusions de l'exploration s'écrivent dans ce seul fichier, à la suite.

## La demande

Le propriétaire veut « explorer la possibilité de créer les vidéos avec une assistance
d'intelligence artificielle », en parallèle du chantier vidéo en cours et sans le gêner.

## Ce que cela peut vouloir dire (à trancher en premier)

1. **Un réalisateur automatique.** Un assistant prend l'idée et mène toute la fabrication :
   découpage, images, clips, contrôle, reprises, montage. Le propriétaire ne fait que valider.
   Aujourd'hui ce travail est partagé entre le scénariste, la Production et lui.
2. **Un générateur qui rend la vidéo entière.** Un service extérieur reçoit une image et une
   consigne et rend le plan fini, parfois avec le son et la voix. Il remplacerait nos clips
   de 5 s assemblés un par un.
3. **Un assistant de retouche.** L'assistant regarde les clips, choisit le meilleur morceau,
   propose le montage, les accroches, le rythme.

Les trois se combinent. La voie 2 ne vaut que pour le tous publics : ces services refusent
le contenu adulte, qui reste sur Z-Image, Wan et les LoRA du propriétaire.

## Où en est la vidéo aujourd'hui

- Une image par plan (Z-Image + LoRA), puis un clip de 5 s tiré de cette image (Wan 2.2),
  puis le montage. Tout tourne sur une machine louée à l'heure.
- Déjà en place : liste de plans, cadrage et transition par plan, raccords, lieu et tenue
  tenus, contrôleur d'images, rendu « à la main » ou « posé », banc d'essai des LoRA de clip,
  montage vers une durée visée, amorce.
- Ce qui coince : chaque plan tourné une seule fois, 5 s, sans choix du meilleur morceau ;
  une seule accroche par projet ; pas de son, de voix ni de lèvres ; plans longs du temps 4
  à préparer ; le contrôle regarde les images, pas encore les clips.
- Détails : `docs/format-video.md`, `docs/chantier-continuite.md`, `docs/son-et-dialogue.md`.

## Règles de l'exploration

- Discussion d'abord. Le code éventuel va sur une branche à part, les essais dans un projet
  d'essai tous publics, sous le même plafond de dépense, chaque dépense notée au journal.
- Rien n'entre en production sans l'accord du propriétaire donné dans la conversation
  principale.
- Les règles du projet restent les mêmes : partage des rôles, conformité, secrets, services
  existants intouchés.

## Questions à ouvrir

- Quelle part du travail le propriétaire veut-il garder à la main ?
- Service extérieur payé à la vidéo, ou tout sur nos machines ?
- Licence : usage commercial permis, personnage fictif accepté ?
- Le visage de Léa tient-il d'un plan à l'autre dans un générateur extérieur ?
- Coût d'une vidéo de 10 à 20 s, comparé au nôtre.

## Conclusions

(à remplir)
