# Brief : planches de référence des personnages de « Hrafnvik »

## Contexte

Je prépare un micro-drama vertical pour adultes, en épisodes de 45 à 60 secondes, dans un univers viking stylisé. Trois personnages récurrents portent toute la saison 1. Avant d'écrire les scripts et de produire la moindre scène, je dois savoir si leurs designs restent cohérents d'une image à l'autre. C'est l'objet de cette tâche.

La série sera diffusée sur des plateformes qui interdisent l'IA photoréaliste. Le rendu doit donc se lire comme du dessin animé au premier coup d'œil. C'est une contrainte dure : une image qui pourrait passer pour une photo est inutilisable, même si elle est belle.

## Ce que je te demande

Produire une planche de référence pour chacun des trois personnages, **habillés**, soit quatre vues par personnage :

1. Portrait de face, expression neutre.
2. Trois quarts et profil.
3. Plein pied en costume d'hiver, puis en tenue d'intérieur.
4. Le même personnage dans deux lieux : la grande salle à la lueur du feu (palette chaude), et la palissade face au fjord gelé (palette froide).

Commence par Sigrun seule. Montre-moi ses quatre vues avant de passer aux deux autres : si le style ne tient pas sur elle, il est inutile de continuer.

## Style visuel

Animation 3D « toon » dans l'esprit de la bande dessinée européenne réaliste.

- Contours encrés épais et visibles, d'épaisseur constante. C'est l'élément le plus important : il garantit que l'image se lit comme un dessin.
- Aplats de couleur, ombres en deux ou trois tons francs.
- Aucune hachure. Ces images serviront de base à de la vidéo, et les hachures y scintillent.
- Visages aux traits marqués, anatomie réaliste, pas de proportions cartoon ni manga.
- Ton « poisseux » : suie, boue, sueur, fumée grasse, bois humide. La crasse va sur le décor, les vêtements et les mains. Les visages restent propres, lisibles et attirants.
- Direction « viking punk » assumée : cheveux de couleur vive, tatouages, bijoux de bronze empilés. L'anachronisme est voulu.
- Motif du clan : le filet de pêche tressé, présent dans chaque costume.

### Palette

- Intérieurs : ocres, bruns, verts sourds, lumière de foyer.
- Extérieurs : gris-bleu froid désaturé.
- Seules couleurs saturées autorisées : le violet des cheveux de Sigrun, le turquoise de ceux d'Ylva, le bronze des bijoux.

## Personnages

Tous trois sont des adultes d'une trentaine d'années et cela doit se voir : visages marqués, corps adultes, posture d'autorité.

### Sigrun, 34 ans, cheffe du clan
Guerrière, sûre d'elle, regard dur. Longs cheveux violets. Tatouages sombres sur les deux bras et le sternum. Collier de bronze à médaillon. Fourrure de loup gris sur les épaules.

### Ylva, 33 ans, voyante
Plus joueuse, regard malicieux. Longs cheveux bleu turquoise. Traits de peinture rituelle sous les yeux. Pendentif à pierre turquoise. Cape de plumes de corbeau.

### Eirik, 36 ans, exilé de retour
Fatigué, méfiant. Cheveux blond cendré, côtés rasés, barbe courte. Tatouage de serpent de l'épaule au cou. Torques de bronze aux poignets. Manteau d'ours brun.

## Base de prompt

À adapter à ton outil et à compléter avec les ancrages du personnage :

```
3D toon-shaded animation, realistic European comic book look, thick inked outlines,
flat colors with two-tone cel shading, no hatching, adult [woman/man] in
[her/his] mid-thirties, [ancrages du personnage], viking punk costume with braided
fishing-net details and stacked bronze jewelry, grimy sooty atmosphere,
[warm earthy ochre and brown interior, firelight | cold desaturated blue-grey
exterior, frozen fjord], non-photorealistic
```

À exclure (prompt négatif si ton outil en accepte un) :

```
photorealistic, photograph, skin pores, hatching, cross-hatching, sketch lines,
anime, chibi, soft gradient shading, youthful face, teenager
```

## Modèles suggérés

Sélection faite le 13/11/2026 à partir des fiches Civitai (description, téléchargements, licence). Aucun n'a été testé sur ce projet : ce sont des points de départ, pas des certitudes. Si tu as déjà un modèle qui donne ce rendu, dis-le-moi plutôt que de changer.

**Combinaison recommandée (famille Illustrious)**

- Checkpoint : **Arthemy Comics Illustrious v8.0** — https://civitai.com/models/1273254 — style comics occidental, licence autorisant l'usage commercial des images.
- LoRA de style : **2.5D Cel Shading Modeling Style v1.0** — https://civitai.com/models/1652997 — pousse vers le rendu 3D cel-shadé. Poids conseillé par l'auteur : 0,6 (plus 2D) à 1,0 (plus 3D). Commencer vers 0,7. Pas de mot déclencheur.

**Alternative (famille SDXL)**

- Checkpoint : **_CHEYENNE_ v2.4** — https://civitai.com/models/198051 — roman graphique et ligne claire, licence autorisant l'usage commercial des images. L'auteur demande le VAE `sdxl-vae-fp16-fix` et un clip skip de 2.

**Écartés pour leur licence** : Nova Comic XL (images non retouchées interdites d'usage commercial) et AniMics Pony XL (usage commercial sur demande).

### Adaptation du prompt pour Illustrious

Illustrious se pilote par mots-clés de type Danbooru, pas par phrases. Point de départ :

```
masterpiece, western comics (style), flat color, thick outlines, bold lineart,
cel shading, 3d, solo, mature female, 34 years old, [ancrages du personnage],
fishing net clothing, bronze jewelry, fur trim, soot, grime, sweat,
[indoors, firelight, warm brown and ochre tones | outdoors, snow, frozen fjord,
cold blue-grey tones]
```

Négatif :

```
anime, big head, chibi, hatching, linear hatching, crosshatching, sketch,
photorealistic, realistic, photo, loli, child, teenager, young,
low quality, worst quality
```

Attention : le prompt de démarrage fourni par l'auteur d'Arthemy contient `linear hatching`. Retire-le, on ne veut aucune hachure.

Cette famille de modèles tire vers l'anime et vers des visages jeunes. Les termes d'âge adulte dans le positif et le négatif ci-dessus sont indispensables, pas optionnels.

## Contraintes

- Personnages habillés sur toutes les planches. Ce sont des références de design, pas des scènes.
- Aucun nom d'artiste ou d'album dans les prompts, aucun LoRA entraîné sur des planches publiées. On s'inspire d'un genre, pas d'une œuvre.
- Aucun visage qui ressemble à une personne réelle identifiable.
- Pas de pose face caméra façon pin-up : le personnage regarde ailleurs ou fait quelque chose.

## Critère de réussite

Sur les quatre vues d'un même personnage :

- la couleur et la longueur des cheveux sont identiques ;
- les tatouages sont au même endroit et ont la même forme ;
- les bijoux sont les mêmes ;
- le contour encré est présent et d'épaisseur comparable ;
- aucune vue ne peut être prise pour une photo.

Si les tatouages ne tiennent pas d'une vue à l'autre, réduis leur nombre et simplifie leur forme plutôt que de multiplier les essais, et dis-moi ce que tu as changé.

## Ce que j'attends en retour

- Les images, rangées par personnage et par vue.
- Le prompt exact et les réglages utilisés pour chaque image retenue (modèle, seed, référence éventuelle), pour pouvoir les reproduire.
- Un avis franc sur ce qui tient et ce qui ne tient pas : quels ancrages dérivent, quelles vues ont demandé le plus d'essais, et si le contour encré résiste dans les deux palettes.
- Si une contrainte de ce brief est impossible à respecter avec ton outil, dis-le plutôt que de la contourner.
