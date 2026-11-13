# Correction de l'image maîtresse de Sigrun

## Pourquoi cette consigne

Les quatre planches de Sigrun réussissent le plus difficile : aucune vue ne peut passer pour une photo, et les cheveux, le médaillon, la ceinture de corde et le tatouage du bras tiennent d'une vue à l'autre dans les deux palettes. La méthode (image maîtresse puis vues dérivées par édition) fonctionne et doit être conservée.

En revanche, le rendu obtenu n'est pas celui de la série. Trois écarts sont à corriger avant de produire Ylva et Eirik, sinon ils hériteront des mêmes défauts.

## Les trois écarts

1. **C'est de la 2D, pas de la 3D.** Les planches sont du dessin à plat, proche du cartoon américain. La cible est une animation 3D « toon » : des volumes modelés, une lumière qui tourne sur les formes, avec le contour encré par-dessus. L'image maîtresse a été générée sans la LoRA de cel shading, ce qui explique sans doute l'écart.
2. **Ce n'est pas poisseux.** Tout est propre et lumineux. Il manque la suie, la sueur, la boue, la fumée grasse, le bois humide.
3. **Ce n'est pas assez sensuel.** Le visage est un peu caricatural (yeux et maquillage de cartoon) et le costume est sage. C'est une série pour adultes : le personnage doit être désirable dès la planche de référence, même habillé. C'est l'écart le plus important commercialement.

Deux détails s'y ajoutent : le tatouage du sternum a disparu, et le filet de pêche n'apparaît que dans le décor alors qu'il doit faire partie du costume.

## Ce que je te demande

Refaire uniquement l'**image maîtresse** de Sigrun, en plusieurs variantes, et me les montrer côte à côte avec l'actuelle. Ne refais pas les quatre vues tant que je n'ai pas choisi une variante.

### Pistes, à toi de juger lesquelles fonctionnent

- **3D** : ajouter la LoRA « 2.5D Cel Shading Modeling Style » (Civitai 1652997). Essayer trois poids, par exemple 0,6, 0,8 et 1,0, à seed constant, pour que je voie l'effet du seul poids.
- **Poisseux** : demander explicitement la peau luisante de sueur, des traces de suie sur les bras et les mains, les vêtements tachés, l'air enfumé. Le visage reste propre et lisible.
- **Visage** : traits plus réalistes et plus adultes, moins de stylisation cartoon dans les yeux et le maquillage. Elle a 34 ans et dirige un clan : belle, dure, marquée.
- **Costume** : toujours habillée, mais plus près du corps et plus découvert. Décolleté qui laisse voir le tatouage du sternum, pièces de filet tressé portées sur la peau (manches, épaules ou taille), ventre ou hanches visibles si cela sert le design. Ton négatif actuel contient `cleavage` : retire-le. Garde `nude`.
- **Tatouages** : garder ceux des bras tels qu'ils sont, ils tiennent bien. Ajouter celui du sternum, simple, pour qu'il survive aux vues dérivées.

### Risque à surveiller

La LoRA a été entraînée sur des jeux et des visuels de style anime. Elle peut rajeunir le visage ou tirer vers le manga. Garde les termes d'âge adulte en positif et en négatif. Si, à tous les poids, le visage rajeunit ou devient anime, dis-le et propose une autre voie pour obtenir le volume 3D plutôt que de forcer celle-ci.

## Critère de réussite

Une variante est retenue si, d'un coup d'œil :

- elle se lit comme une image d'animation 3D et toujours pas comme une photo ;
- le contour encré est toujours présent ;
- la scène paraît chaude, enfumée et sale ;
- Sigrun est clairement une femme adulte, et attirante ;
- cheveux violets, médaillon, ceinture de corde et tatouages des bras sont inchangés par rapport à l'image actuelle.

## Ce que j'attends en retour

- Une planche comparative : l'image maîtresse actuelle et les variantes, avec le poids de LoRA indiqué sous chacune.
- Le prompt et les réglages exacts de chaque variante.
- Ton avis : laquelle tu retiendrais, et ce que chaque correction a coûté sur les autres critères (par exemple, si la 3D affaiblit le contour ou si la crasse salit le visage).

Le tout dans `hrafnvik/sigrun/`, sans écraser les fichiers existants : ils servent de point de comparaison.
