# Son et dialogue - etat des lieux (recherche du 13/11/2026)

Sources : comparatifs publies en octobre-novembre 2026 (tests a l'aveugle Everypixel, Clipia,
articles de synthese). Aucun de ces outils n'a ete teste dans ce projet. Les regles de contenu
(adulte) de chaque service n'ont pas ete verifiees : a lire avant tout usage.

## Les trois paliers
1. Ambiance et musique : ajout au montage (`tools/montage/montage.py --audio`). Rien a inventer.
2. Voix off : creer une voix stable pour Lea (synthese vocale), la poser sur les clips, sous-titrer.
   Sert aussi aux messages vocaux pour les abonnes.
3. Lea parle face camera : deux voies, ci-dessous.

## Palier 3, voie ouverte (sur notre volume, sans filtre)
| Outil | Ce qu'il fait | Points notables |
|---|---|---|
| InfiniteTalk (MeiGen-AI) | une image + une piste audio -> video parlee de longueur libre | bati sur Wan 2.1 I2V 14B + encodeur audio wav2vec2 ; workflow natif ComfyUI, modeles repackages par Comfy-Org ; 480p ou 720p ; arrive en tete de la synchronisation des levres dans un test a l'aveugle d'octobre 2026 (58 % contre 56 % pour MiniMax H3 Turbo) |
| Wan 2.2 S2V | audio -> video | deja disponible dans le depot de modeles que nous utilisons |
| LatentSync 1.6 | re-synchronise les levres d'une video existante sur un nouvel audio | licence Apache 2.0 |
| LTX-2 / LTX-2.5 | genere image et son ensemble | licence communautaire (gratuite sous un seuil de revenus) |
| StableAvatar | avatar long a partir d'une image et d'un audio | moins repandu |

A retenir : InfiniteTalk repose sur la meme famille de modeles que notre chaine et tourne dans
ComfyUI. C'est le premier candidat a tester. Licence a verifier.

## Palier 3, voie fermee (tous publics uniquement, a priori)
| Service | Force | Prix releve |
|---|---|---|
| HeyGen (Avatar IV / V) | presentateur photo-realiste, jusqu'a 30 min d'un seul tenant, 175+ langues | 29 $/mois, environ 30 min de video realiste |
| Hedra (Character-3) | personnages expressifs a partir d'une image ; avatars en direct | des 15-20 $/mois ; API 2,5 cents/s en 540p |
| Kling (Avatar, Lip Sync, audio natif) | mouvements naturels de la tete et du corps, bon rapport qualite/prix | abonnement des ~7-9 $/mois |
| MiniMax H3 Turbo | meilleur pour l'expression et le mouvement dans le test a l'aveugle (75 %) | via API |
| Veo 3.1 | dialogue natif, mais clips de 8 s et visage qui peut changer d'un clip a l'autre | ~0,40 $/s |
| Sync.so, VEED | re-synchronisation de levres sur une video existante | 0,05 a 0,13 $/s |

## Points de vigilance
- Francais : un test d'avril 2026 a montre HeyGen reecrivant silencieusement des scripts en francais,
  allemand et espagnol (environ 78 % de mots conserves). Toujours reecouter.
- Une voix "trop rapide et trop lisse" est le premier indice que les spectateurs reperent : ralentir.
- Temps reel : Hedra propose des avatars en direct ; qualite inferieure aux videos calculees.
  Les appels en direct restent dans les limites de Lea pour l'instant.
- Certains services utilisent les visages et voix televerses pour entrainer leurs modeles : lire
  la politique de donnees.

## Proposition
1. Lancement : ambiance + sous-titres.
2. Creer la voix de Lea, passer a la voix off.
3. Tester InfiniteTalk sur le volume avec une phrase courte en francais (voie ouverte).
4. Pour une video d'introduction parlee, comparer avec un service ferme sur un essai gratuit.
