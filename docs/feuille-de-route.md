# Feuille de route et regles de travail (13/11/2026)

## Regles de travail convenues
- Rentabilite d'abord : chaque depense GPU est annoncee, plafonnee et consignee. Pas de pod sans
  arret automatique. Plafond de la nuit du 13/11 : 10 $.
- Partage des roles : l'assistant construit et pilote toute la chaine (infrastructure, LoRA, images
  et videos tous publics ou suggestives, tri, montage, publication, automatisation, documentation).
  Le contenu explicite (prompts, generation, choix des LoRA adultes) est produit par le proprietaire,
  avec les outils que l'assistant met a sa disposition.
- Serveur Oracle : tout ce qui est cree porte un nom explicite avec `girls-ai` ; verifier qu'un nom
  est libre avant de creer un service ; ne jamais toucher aux services existants (hermes, openclaw,
  base de connaissances). Depot clone sous l'utilisateur `debian`.
- Aucun secret dans le depot ni dans la conversation : cles saisies par formulaire securise ou
  directement dans `server/.env`.
- Tout ce qui est decide est consigne : bible (personnage), journal (faits, lecons, couts), ce
  fichier (direction). Ces documents alimentent la base de connaissances (dossier `girls-ai`).
- Reutilisable pour d'autres personnages : rien de propre a Lea dans le code ; un personnage = une
  bible, un casting, un jeu de reference, un LoRA, un fichier `production.yaml`.
- Validation humaine avant toute publication ; le tri reste entre les mains du proprietaire.

## Direction technique
| Brique | Aujourd'hui | Cible |
|---|---|---|
| Images | Wan 2.2 + LoRA (rendu trop lisse) | Z-Image + LoRA (photo realiste) ; second candidat : Realism by Stable Yogi (MOSS) |
| Video | Wan 2.2 I2V, 5 s, 480p/720p, mode "mouvement naturel" | 720p + agrandissement + interpolation par IA ; test de LTX-2.5 |
| Duree | un plan de 5 s | plans continus de 10-20 s par enchainement ; montages de 30-60 s |
| Decors | inventes a chaque image | decors fixes de Lea (cuisine, studio, chambre, salle de bain) |
| Son | aucun | palier 1 ambiance ; palier 2 voix off + sous-titres ; palier 3 Lea parle (InfiniteTalk a tester) |
| Identite en video | portee par l'image de depart | eventuellement un LoRA d'animation entraine sur de courts clips |
| Controle | tri humain + controle automatique a la main | controle automatique branche sur le pilote (pre-tri) |
| Lancement d'une generation | fichier de plans ecrit a la main | formulaire dans l'interface de tri |

## Structure d'un contenu : trois temps
Une idee de moment de vie produit trois niveaux, qui correspondent au modele economique :
1. Accroche, tous publics : short pour Instagram / TikTok.
2. Montee, suggestive : pour les abonnes.
3. Final prive : champ libre rempli par le proprietaire ; contenu payant a l'unite.
Le formulaire pre-remplit les temps 1 et 2 a partir de la bible ; le pilote genere l'ensemble dans
le meme decor et la meme tenue ; le lot arrive au tri classe par destination.

## Ordre des travaux
1. Qualite d'image : LoRA Z-Image (en cours), puis jeu de reference realiste si necessaire.
2. Pilote adapte a Z-Image ; decors fixes.
3. Premier lot de lancement (clips et photos tous publics) ; nouvelle video d'introduction.
4. Enchainement de clips (videos longues) ; formulaire de generation.
5. Pilote ouvert aux LoRA choisis par le proprietaire, avec la procedure pour les deposer sur le volume.
6. Son : voix de Lea, voix off, puis essai d'InfiniteTalk.
7. Comptes et lancement : validation Fanvue, prix, messages automatiques, premieres publications ;
   contestation Instagram ; TikTok.
8. Planification hebdomadaire automatique ; suivi des couts et des revenus.

## Veille
Tache planifiee "Veille girls-ai" creee le 13/11/2026 : chaque lundi et jeudi a 9 h 46 (heure de
Paris), une session recherche les nouveautes (modeles ouverts d'image et de video, voix et dialogue,
regles Fanvue / Instagram / TikTok, tarifs RunPod) et ajoute une entree datee en tete de
`docs/veille.md`. Elle ne lance aucun pod et ne modifie rien d'autre. Premier passage : lundi 16/11.
Limites connues : la tache n'a pas de connecteur de recherche attache ni de depot pre-attache ; elle
doit ajouter le depot elle-meme et utiliser la recherche web integree. A verifier apres le premier passage.
