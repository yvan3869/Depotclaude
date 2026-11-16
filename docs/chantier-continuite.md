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
- [ ] Fiche de continuité : ligne `partenaire` (qui il est, écrit une seule fois) ; `autres` ne dit plus que ce qu'il fait.
- [ ] La chaîne met en tête de chaque scène du temps la phrase fixe de la vue choisie (tous publics, écrite par moi).
- [ ] Vérificateur du script : refuse un `autres` qui contredit la vue du temps.
- [ ] Contrôleur : nouvelle case « vue » (subjective, extérieure, mélange) ; un mélange relance la scène.
- [ ] Plus tard : étiquette `pov` / `tiers` posée par le propriétaire sur ses LoRA, avertissement si elle contredit le temps.

### 3. Tenue : un état porté de scène en scène
- [ ] Script : champ `tenue` par scène à partir du temps 2 (ce qu'elle porte encore, ce qui est retiré et où c'est posé).
      Vide = identique à la scène précédente, d'un temps au suivant aussi. Obligatoire sur la première scène du temps 2.
- [ ] La chaîne l'ajoute juste après la pose (début de description) et le donne au contrôleur comme champ à part.
- [ ] `docs/agents.md` et `tools/triage/verifier.py` : nouveau modèle de plan, mis à jour ensemble.
- [ ] Le texte de ces champs aux temps 2 à 4 est écrit par le scénariste du propriétaire, pas par l'assistant.

### 4. Contrôle qui agit sur ces points
- [ ] Relance aussi quand la meilleure image d'une scène a le lieu, la tenue ou la vue faux (pas seulement note ≤ 4).
- [ ] Écran : « contrôle en cours » tant que les notes ne sont pas arrivées ; sur chaque scène, le défaut restant en clair.

### 5. Plus tard
- [ ] « Pose gardée » : le squelette d'une image validée (à deux aussi) est rangé sous le nom de sa position et resservi.
- [ ] Brouillon à deux personnages.

## Règles de travail

- Essais de l'assistant : tous publics, sur p0004, file d'attente vide. Le propriétaire juge les temps 3 et 4.
- Code du pilote : fusionné seulement après essai. `tools/triage/*.py` : redémarrage, donc seulement quand rien ne tourne.
- Chaque dépense est notée dans `docs/journal-projet.md`.

## Journal du chantier

- 16/11/2026, 02 h 50 : diagnostic fait, ce fichier écrit. Rien de construit encore. Une chaîne du propriétaire tourne.
