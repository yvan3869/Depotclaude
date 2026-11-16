# Chantier « continuité » (ouvert le 16/11/2026)

Fichier de suivi : il dit ce qui a été constaté, pourquoi, quelles parades sont retenues et où en est chaque travail.
À tenir à jour à chaque étape (une session interrompue reprend ici).

## Constat du propriétaire sur p0005 (16/11/2026)

1. Le contrôle des images ne semble pas fait.
2. Aux temps 3 et 4 : le lieu, l'éclairage et les vêtements retirés au temps 2 ne sont pas tenus.
3. Au temps 4, le partenaire est tantôt vu par ses yeux (vue subjective), tantôt visible derrière elle, tantôt les deux.

## Ce que disent les chiffres (aucune image ni aucun texte des temps 2 à 4 n'a été lu)

- Le contrôle a bien tourné : 63 images notées (3 par scène, 21 scènes), 7 scènes refaites, puis relues. Il a duré
  7 minutes après la dernière image : pendant ce temps l'écran montrait des images sans note. À corriger à l'affichage.
- Le contrôleur voit les mêmes défauts que le propriétaire :

  | temps | lieu faux | tenue fausse | corps abîmé | note moyenne |
  |---|---|---|---|---|
  | 1 | 6 sur 9 | 1 sur 9 | 0 | 4,8 |
  | 2 | 12 sur 15 | 7 sur 15 | 2 | 3,9 |
  | 3 | 15 sur 18 | 17 sur 18 | 4 | 4,1 |
  | 4 | 16 sur 21 | 21 sur 21 | 10 sur 21 | 3,0 |

  Mais il ne relance une scène que si aucune de ses 3 images ne dépasse 4 : un lieu ou une tenue faux ne suffit pas.

## Les causes, dans la chaîne

- **Lieu et lumière** : p0005 a été tiré en `ref`, `ref`, `pose`, `pose`. Dans ces tirages le lieu et la lumière ne sont
  que deux bouts de phrase ajoutés à la fin de chaque description, là où le modèle d'image écoute le moins, et les LoRA
  pour adultes amènent leurs propres pièces et leur propre lumière. La photo du lieu existe pourtant dans la bibliothèque
  de Léa (image choisie pour le lieu de la fiche) : elle n'a pas servi, parce que seul le tirage `decor` (ou `auto` sur un
  plan large) l'utilise.
- **Temps 4** : dès qu'une scène a une autre personne (`autres`), la Production n'impose ni pose ni lieu : texte seul et
  LoRA. Le plan « lieu de départ » (l'image part de la photo du lieu vide) existe dans le pilote mais n'est branché que sur
  la page de comparaison, pas sur la Production.
- **Tenue** : à partir du temps 2 la tenue de la fiche n'est plus ajoutée (elle se défait) : chaque scène doit dire ce
  qu'elle porte. Rien ne porte l'état d'une scène à la suivante ni d'un temps au suivant ; une scène qui ne redit pas ce
  qui a été retiré laisse le modèle rhabiller ou déshabiller à sa guise.
- **Partenaire** : aucun champ du script de p0005 ne dit d'où l'on regarde (aucun mot de vue subjective dans les 7 scènes
  du temps 4 ; « derrière » dans une seule). La ligne `pdv` de la fiche est retirée dès qu'une scène donne son angle, donc
  toujours. Le modèle choisit seul à chaque image, et certaines LoRA sont entraînées sur des vues subjectives.

## Parades retenues, dans l'ordre

### 1. Lieu et lumière tenus par la photo du lieu, aux quatre temps
- [ ] Production : une scène avec partenaire part de la photo du lieu (`lieu_depart`, déjà dans le pilote) quand le tirage
      est `decor` ou `auto`. Force 0,8 par défaut, réglable.
- [ ] Tirage `auto` : la photo du lieu sert à tout plan qui n'est pas un gros plan (aujourd'hui : plans larges seulement),
      dès que le lieu a une image choisie. À vérifier à l'image sur p0004 avant de changer la règle (plan moyen).
- [ ] Sans image du lieu dans la bibliothèque : la Production en fabrique une (pièce vide, avec la lumière de la fiche,
      tous publics, environ 0,01 $) au premier lancement et la montre pour accord.
- [ ] Lumière : elle est dans la photo du lieu (décor gelé : fond identique au pixel). Sur un gros plan (texte seul),
      la phrase de lumière passe en tête de la description.
- [ ] Proposer `auto` comme tirage par défaut des quatre temps (choix du propriétaire).

### 2. Partenaire : une seule façon de le montrer par temps
- [ ] Script : nouveau champ `atelier.vue`, par temps : `pov` (on voit par ses yeux : ses mains, ses avant-bras, jamais
      son visage) ou `tiers` (caméra extérieure, les deux visibles). Obligatoire dès qu'une scène du temps a `autres`.
- [x] Fiche de continuité : ligne `partenaire` (qui il est, écrit une seule fois) ; `autres` ne dit plus que ce qu'il fait.
- [ ] La chaîne met en tête de chaque scène du temps la phrase fixe de la vue choisie (tous publics, écrite par moi).
- [ ] Vérificateur du script : refuse un `autres` qui contredit la vue du temps.
- [ ] Contrôleur : nouvelle case « vue » (subjective, extérieure, mélange) ; un mélange relance la scène.
- [ ] Plus tard : étiquette `pov` / `tiers` posée par le propriétaire sur ses LoRA, avertissement si elle contredit le temps.

### 3. Tenue : un état porté de scène en scène
- [ ] Script : champ `tenue` par scène à partir du temps 2 (ce qu'elle porte encore, ce qui est retiré et où c'est posé).
      Vide = identique à la scène précédente, d'un temps au suivant aussi. Obligatoire sur la première scène du temps 2.
- [ ] La chaîne l'ajoute juste après la pose (début de description) et le donne au contrôleur comme champ à part.
- [x] `docs/agents.md` et `tools/triage/verifier.py` : nouveau modèle de plan, mis à jour ensemble.
- [ ] Le texte de ces champs aux temps 2 à 4 est écrit par le scénariste du propriétaire, pas par l'assistant.

### 4. Contrôle qui agit sur ces points
- [ ] Relance aussi quand la meilleure image d'une scène a le lieu, la tenue ou la vue faux (pas seulement note ≤ 4).
- [ ] Écran : « contrôle en cours » tant que les notes ne sont pas arrivées ; sur chaque scène, le défaut restant en clair.

### 5. Plus tard
- [ ] « Pose gardée » : le squelette d'une image validée (à deux aussi) est rangé sous le nom de sa position et resservi.
- [x] Brouillon à deux personnages.

## Approche élargie : « tout passe par un brouillon contrôlé » (16/11/2026, seconde demande)

Demande du propriétaire : tout automatiser, résultat le meilleur possible dès le premier tirage, sans compter le temps.
Le personnage change souvent de position et d'expression et perd des habits au fil des scènes ; le lieu et la lumière,
eux, ne changent pas : le lieu est dans la bibliothèque du personnage, la lumière est celle des images de la scène d'avant.

Idée : aujourd'hui l'image finale est tirée « à l'aveugle » depuis un texte, puis notée. À la place, chaque scène passe
d'abord par un **brouillon** peu coûteux qui fixe tout ce qui doit tenir (pièce, lumière, vêtements restants, position,
nombre de personnes, point de vue). On contrôle le brouillon, on le refait s'il est faux, et seulement ensuite Z-Image
et ses LoRA redessinent le personnage par-dessus. Le rendu final reste Z-Image + LoRA aux temps 3 et 4.

### A. Le brouillon enchaîné (l'état se transmet par l'image, plus par le texte)

- [ ] Brouillon de chaque scène par retouche à plusieurs images (Qwen-Image-Edit, déjà dans le pilote) avec :
  image 1 = **elle, telle qu'à la scène d'avant** (le brouillon précédent ; à la première scène, l'image neutre et la
  tenue de la fiche) ; image 2 = **la photo d'origine du lieu** (toujours l'originale, jamais une image déjà fabriquée,
  pour que la pièce ne dérive pas) ; image 3 au besoin = la fiche du partenaire.
- [ ] Le texte du brouillon ne dit que ce qui change : position, cadrage, ce qui est retiré ou déplacé, expression.
  Un vêtement retiré reste donc retiré aux scènes suivantes sans que le script ait à le redire.
- [ ] Entre deux temps : le dernier brouillon du temps N sert de départ au temps N+1 (la continuité avec le temps 2
  demandée par le propriétaire).
- [ ] Chaîne cassée (brouillon refusé trois fois) : on repart de la dernière image d'état valable, la scène est signalée.

### B. Le partenaire

- [ ] Fiche du partenaire dans la bibliothèque du personnage (homme adulte fictif, image habillée, tous publics) ;
  `continuite.partenaire` le décrit en une ligne.
- [ ] Vue écrite une fois par temps (`atelier.vue` : `pov` ou `tiers`) ; à défaut, la chaîne la choisit elle-même
  (première scène du temps qui cite un partenaire) et la garde pour tout le temps.
- [ ] `tiers` : brouillon à deux (elle + partenaire + lieu). `pov` : brouillon à une personne, « vu par ses yeux »,
  au plus des mains au premier plan ; le contrôleur refuse une seconde personne entière.
- [ ] Image finale d'une scène à deux : pas de squelette (il ne sait placer qu'une personne) mais « image de départ »
  depuis le brouillon à deux, force 0,6 à 0,7. À essayer ensuite : contrôle par la profondeur du brouillon.

### C. De quoi le brouillon tient l'image finale

- [ ] Seule, plan large ou moyen : squelette + décor gelé à 0,8 (essai du 15/11 : pièce identique, 4 sur 4).
- [ ] Gros plan : départ depuis un brouillon serré, force 0,6 (à essayer ; aujourd'hui le gros plan est libre).
- [ ] À deux : voir B.
- [ ] Étalonnage automatique sur le serveur, sans GPU : les couleurs de l'image finale sont accordées à celles de la
  photo du lieu (fond, hors zone du personnage) ; sur un gros plan, à celles de la peau de l'image d'avant.
- [ ] Expression : champ `expression` par scène, redit au moment de la reprise du visage.

### D. Le contrôle

- [ ] Brouillon relu avant le rendu final : position, nombre de personnes, vue, lieu, vêtements. Trois essais.
- [ ] Image finale comparée **à des images**, pas seulement au texte : à la photo du lieu (même pièce ?) et au
  brouillon (mêmes vêtements, même position ?).
- [ ] Relance aussi quand le lieu, la tenue ou la vue sont faux, pas seulement quand la note est basse.
- [ ] Relances qui changent quelque chose : 1re = autre graine ; 2e = pose plus forte, LoRA de style plus faibles ;
  3e = force de redessin plus basse (l'image reste plus près du brouillon).
- [ ] Écran : « contrôle en cours », puis le défaut restant par scène, en clair.

### E. Bibliothèques qui grandissent toutes seules

- [ ] Lieu à plusieurs vues : à partir d'une photo, un jeu de 4 à 6 angles de la même pièce, fabriqué une fois ;
  la scène prend la vue qui convient à son cadrage.
- [ ] Poses gardées : le squelette (ou le brouillon) d'une image validée par le propriétaire est rangé par position,
  vue et cadrage, et resservi en premier la fois suivante.
- [ ] Lumière : relevé chiffré (teinte, clarté, contraste) de la dernière image validée du temps précédent, appliqué
  comme cible de l'étalonnage du temps suivant.

### F. Côté script (le scénariste), sans en dépendre

La chaîne doit tenir même avec un script comme celui de p0005. Les champs ci-dessous l'aident mais ne sont pas exigés :
`atelier.vue` par temps, `continuite.partenaire`, `tenue` par scène (héritée de la scène d'avant si absente),
`expression`. À ajouter ensemble dans `atelier.py`, `verifier.py` et `docs/agents.md`, avec un nouveau modèle de plan.

### Programme d'essais (tous publics, hors projets du propriétaire)

Une séquence de 5 scènes dans un lieu de la bibliothèque de Léa, ancienne voie contre nouvelle :
1. debout, veste et robe ; 2. assise, veste retirée et posée ; 3. allongée, chaussures retirées ;
4. plan moyen, un ami assis à côté d'elle (vue extérieure) ; 5. vue par les yeux de l'ami : elle lui tend une tasse.

- [x] Essai 1 : brouillons enchaînés seuls (5 brouillons, 2 graines) : la veste reste-t-elle retirée en 3, 4, 5 ?
  la pièce est-elle la même ? combien de personnes en 4 et en 5 ?
- [x] Essai 2 : rendu final Z-Image depuis ces brouillons (gelé pour 1 à 3, départ 0,6 et 0,7 pour 4, départ pour 5).
- [x] Essai 3 : étalonnage et comparaison image à image par le contrôleur sur ces mêmes images.
- [x] Ensuite : portage dans le pilote (`poses_imposees`), puis `atelier.py` (file vide), puis essai sur p0004.

Ordre de construction : A puis B (le plus gros gain), D en même temps (sans lui rien n'est automatique), C, puis E et F.

## Nettoyage demandé par le propriétaire (16/11/2026)

« Nettoyer tes essais et les modèles qui ne servent pas sur RunPod. » Accord donné pour ces deux choses seulement.

- [x] Volume RunPod `lea-models` : dresser la liste des fichiers de modèles avec leur taille, la comparer à ce que
  la chaîne appelle (`persona/production.yaml`, `server/pilot/workflows.py`, `controle.py`, LoRA de la bibliothèque et
  des projets). Supprimer : les sorties et images déposées par mes essais (`ga_*` dans `input/` et `output/` de ComfyUI),
  les modèles téléchargés pour un essai et que plus rien n'appelle. Ne pas toucher : les LoRA du propriétaire, les
  jeux d'entraînement, le contrôleur, tout fichier dont l'usage n'est pas sûr (le lister et demander).
- [ ] Serveur : dossiers `server/data/work/girls-ai-essai-*` des essais terminés ; planches `p0004essai_*` anciennes
  de `server/data/inbox/` (garder celles de l'essai en cours).
- [ ] Noter dans `docs/journal-projet.md` ce qui a été supprimé et la place regagnée (avant / après).
- Se fait avec un pod : donc quand la chaîne est libre, à la suite d'un essai pour ne pas payer un pod de plus.

## Règles de travail

- Essais de l'assistant : tous publics, sur p0004, file d'attente vide. Le propriétaire juge les temps 3 et 4.
- Code du pilote : fusionné seulement après essai. `tools/triage/*.py` : redémarrage, donc seulement quand rien ne tourne.
- Chaque dépense est notée dans `docs/journal-projet.md`.

## Journal du chantier

- 16/11/2026, 02 h 50 : diagnostic fait, ce fichier écrit. Rien de construit encore. Une chaîne du propriétaire tourne.
- 16/11/2026, 03 h 05 : approche élargie « brouillon contrôlé » écrite (sections A à F, programme d'essais). Aucun essai : un entraînement du propriétaire tourne.
- 16/11/2026, 03 h 10 : essai 1 et 2 écrits (lanceur `ch1.py` du dossier de travail de la session : 5 scènes sur le canapé de la bibliothèque, brouillons anciens et enchaînés, partenaire, images finales gelées ou « de départ »). En attente : la chaîne est occupée par un entraînement du propriétaire ; l'essai part seul quand elle est libre. Sorties dans `server/data/work/girls-ai-essai-chaine/`. Nettoyage demandé, consigné ci-dessus.
- Si la session s'arrête ici : reprendre par l'essai 1 (le réécrire d'après la section « Programme d'essais » si le lanceur a disparu), puis suivre l'ordre de construction A, B, D, C, E, F et le nettoyage.
- 16/11/2026, 03 h 25 : parade 1 écrite sur la branche de travail `girls-ai-wip` seulement (non déployée, non essayée) : `auto` = lieu de la bibliothèque pour tout plan non serré ; scène à partenaire en tirage `decor` = image qui part de la photo du lieu (`_lieu_depart` dans `atelier.py`). À déployer avec `dep.py` quand rien ne tourne, puis à essayer sur p0004.
- 16/11/2026, 04 h 10 : essai 1 fait (0,21 $, détail au journal). Leçons : (1) ne **pas** enchaîner les brouillons l'un sur l'autre (dérive des couleurs, vêtement qui change, pose qui colle) ; la section A est à corriger : la référence d'elle reste **fixe** (une image « tenue complète » du temps) et c'est l'**état cumulé**, écrit par la chaîne d'après les scènes d'avant, qui dit ce qui est retiré ; (2) le rendu final depuis le brouillon marche : décor gelé pour elle seule, image de départ à 0,6 pour deux personnes (0,7 défait la scène) ; (3) le texte seul réinvente pièce et robe à chaque scène. Essai 2 lancé (référence fixe, 2 graines, + liste du volume pour le nettoyage).
- 16/11/2026, 04 h 30 : essai 2 fait (environ 0,10 $, detail au journal). Lecons : (1) reference fixe + etat cumule **tient pour elle seule** (robe, veste retiree, chaussures au sol) ; a garder, avec un controle du brouillon (une chaussure remise 1 fois sur 6) ; (2) **a deux, l'etat est perdu** : avec trois images (elle, lieu, partenaire) le modele recopie la reference habillee. Parade a essayer : fabriquer d'abord le brouillon d'elle seule dans le bon etat (ca marche), puis **ajouter le partenaire dans cette image** par une seconde retouche (un seul maillon, rien d'autre ne change) ; (3) la lampe et le cadrage bougent : dire le cadrage dans le texte du brouillon, et faire relire le brouillon contre la photo du lieu par le controleur. Reste a faire, dans l'ordre : essai 3 (partenaire ajoute en second, rendu final, etalonnage ColorMatch, controle image a image) + nettoyage du volume avec le meme pod ; puis portage dans `server/pilot` et `atelier.py`.
- 16/11/2026, 05 h 00 : essai 3 fait (environ 0,11 $, detail au journal). Acquis : (1) scene a deux = brouillon d'elle seule dans le bon etat, puis partenaire **ajoute par une seconde retouche** (etat tenu 2 sur 2) ; (2) rendu final : decor gele seule, depart 0,6 a deux et en vue subjective ; (3) ColorMatch (mkl) disponible dans le graphe ; (4) nettoyage du volume fait (4,1 Go), reste a nettoyer cote serveur les dossiers d'essai. La methode est donc arretee : **reference fixe + photo du lieu + etat cumule -> brouillon (relu par le controleur : position, vetements, nombre de personnes) -> partenaire ajoute si besoin -> Z-Image + LoRA (gele ou depart 0,6) -> ColorMatch**. Reste a faire : portage dans `server/pilot` (`poses_imposees` : plans `reference`, `etat`, `partenaire_image`, `depart_brouillon`), puis `atelier.py` (file vide), `verifier.py` et `docs/agents.md`, puis essai sur p0004.
- 16/11/2026, 06 h 00 : **methode en service** (commits efc4f89 et suivant, deployes). Modele de plan `2026-11-16a` : `retire` (liste, obligatoire aux temps 2 a 4), `etat`, `atelier.partenaire` ; verificateur, `docs/agents.md`, `server/jobs/modele.yaml` et page (champs de scene et de projet) a jour. Production : `_continuite` dans `atelier.py` (tirage « decor », lieu avec image, tenue dans la fiche) ; pilote : reference fixe gardee en cache, partenaire ajoute en second, relecture du brouillon par vetement retire, depart 0,6 a deux, ColorMatch. Essais 4 a 7 au journal (0,13 + 0,08 + 0,71 + 0,73 $).
- Resultat de l'essai 7 (planche `data/inbox/p0004essai_chaine7_production.jpg`) : piece et lumiere tenues sur toutes les images ; vetements justes sur les images finales apres une relance ; partenaire present et le meme.
- Reste a faire, par ordre d'interet :
  1. Brouillon : la veste retiree reste souvent sur elle (le modele de retouche obeit mal a « ne porte plus »). Piste : une **image d'etat** par liste `retire` (la reference, vetement enleve par une retouche simple a une seule image, relue une fois par le controleur, gardee en cache), dont tous les brouillons de cet etat sont tires.
  2. Vue subjective : rendue en vue exterieure, mains du partenaire absentes ; le controle relance deux fois pour rien. A voir avec les LoRA du proprietaire aux temps 3-4 ; sinon ne pas relancer sur ce seul point.
  3. Cadrage : le champ « cadrage » est note bas en plan large (personnage petit dans une grande piece) ; resserrer le brouillon.
  4. Ecran « controle en cours » ; lieu a plusieurs vues ; poses gardees ; essai aux temps 2 a 4 par le proprietaire (c'est lui qui juge).
  5. Nettoyage cote serveur : `server/data/work/girls-ai-essai-*`, `server/data/work/p0004r*`, vieilles planches `p0004essai_*` ; scenes s5 a s8 de p0004 ; puis suppression du worktree `girls-ai-wip`.
- Pour le proprietaire : pour en profiter sur un projet, tirage « decor » (ou « auto ») au temps voulu, lieu de la bibliotheque avec image, tenue dans la fiche de continuite, et un script ecrit au modele `2026-11-16a`.
