# Journal du projet Lea Morel (persona IA)

Synthese des decisions, de l'etat et des lecons. A importer dans la base de connaissances.

## Concept
- Personnage 100 % fictif, adulte, assume comme IA : Lea Morel, 27 ans, coach pilates a Lyon.
- "Moments de vie" en video ; shorts soft sur Instagram / TikTok pour amener vers la page payante.
- Bible du personnage : `persona/bible.yaml` (identite, gestuelle, defauts, decors, arcs narratifs).

## Decisions cles
| Sujet | Decision | Raison |
|---|---|---|
| Plateforme payante | Fanvue | seule grande plateforme acceptant les createurs entierement IA ; OnlyFans et Fansly refusent |
| Divulgation | IA assumee partout | obligation Fanvue, labels Instagram/TikTok, AI Act art. 50 |
| Generation | Wan 2.2 (open weights) sous ComfyUI sur RunPod | licence commerciale, pas de filtre, cout de quelques centimes par clip |
| Coherence du visage | LoRA entraine sur Wan 2.2 (musubi-tuner) | un seul LoRA pour images et videos |
| Declinaisons du visage | Qwen-Image-Edit 2509 | conserve l'identite d'une image a l'autre |
| Orchestration | serveur Oracle (ARM, Debian 13) via Tailscale | allume en permanence, acces prive |
| Messages abonnes | outils IA integres a Fanvue | autorises ; ne jamais nier etre une IA |

## Chronologie
- 12/11 : cadrage, choix IA assumee, depot, bible, guide RunPod, interface de tri.
- 12/11 soir : cle API RunPod, volume `lea-models` (150 Go, EU-RO-1), modeles Wan 2.2, premier test.
- 13/11 matin : reglages de qualite, casting de 48 visages, choix du n.29.
- 13/11 : image maitre (tatouages, pendentif), jeu de reference de 40 images + 14 sans maquillage.
- 13/11 : entrainement du LoRA `leamorel_t2v_low_v1` (47 images, 1 880 pas, RTX 5090).
- 13/11 : interface de tri installee sur le serveur Oracle (port 8790, Tailscale).
- 13/11 : LoRA termine ; comparaison des versions (`persona/reference/lora_v1_comparaison.jpg`).
  Identite acquise des la version 10 ; la version 40 sur-apprend (tatouage imprime sur les vetements).
  Version conseillee : 30 (`leamorel_t2v_low_v1-000030.safetensors`, dans `/workspace/lea_lora`).
- 13/11 : premiers clips video (Wan 2.2 I2V + lightx2v 4 pas, 81 images a 16 i/s) : fenetre,
  studio, cuisine. 480x832 en ~40-60 s, 720x1280 en ~190 s sur RTX 4090.
- 13/11 : controle automatique des clips (`tools/qc/qc_clip.py`) et pilote GPU (`server/pilot/`)
  valide de bout en bout : 2 images + 2 clips en 17 min pour 0,20 $.
- 13/11 : comptes : Gmail cree ; Instagram suspendu des la creation ; Fanvue en cours d'inscription.
  Textes de profil enregistres (`persona/profile_texts.md`).
- 13/11 : fiche « Creator Personality » Fanvue saisie et enregistree ; bible alignee (celibataire,
  deux tatouages presents, deux tatouages futurs, aucun piercing, surnoms, salutation, emojis, limites).
  Grain de beaute et cicatrice au genou retires : absents des images de reference.
  Verification d'identite Fanvue envoyee.
- 13/11 : LoRA d'animation (I2V low-noise, entraine sur images fixes) : echec. Entrainement interrompu
  a 83 % par un disque plein ; la version la plus avancee ne change ni les clips ni les mesures
  (ressemblance 0,55 avec et sans). Abandonne et supprime. Cout : ~2 $.
- 13/11 : pilote valide dans sa version en deux passes (2 images + 2 clips en 9 min).
- 13/11 : premiere generation lancee depuis le serveur Oracle par le proprietaire : 2 clips arrives
  dans le tri. Chaine complete validee sans l'assistant. Avatar et banniere Fanvue choisis.
- 13/11 soir : comparaison de trois methodes d'image (Wan actuel, Wan + LoRA "photo de telephone",
  Z-Image). Z-Image l'emporte nettement sur le realisme (peau, lumiere, cadrage). LoRA de Lea
  entraine sur Z-Image base (v1, 1 410 pas, ~1 h sur RTX 4090) : traits du visage acquis et peau
  realiste, mais cheveux et tatouages non appris ; ils reviennent avec une description explicite
  dans le prompt et un LoRA applique a 1,3. Pilote passe en mode Z-Image et valide (2 images +
  2 clips en 7 min). Defaut restant : les tatouages decrits par le prompt varient de dessin et de
  cote. Second entrainement lance (v2 : 2 115 pas, taux double) pour ancrer cheveux et tatouages.
- 13/11 soir : video d'introduction (3 variantes 720p, ancienne methode) ; avatar et banniere Fanvue
  en place ; recherche son et dialogue ; feuille de route ; tache de veille bihebdomadaire.

## Etat de l'infrastructure
- RunPod : volume `lea-models` (id `0h86zhlu0v`), template ComfyUI `6uf2r3i7sy`. Aucun pod permanent.
- Sur le volume : ComfyUI, Wan 2.2 (t2v/i2v), Qwen-Image-Edit, musubi-tuner, jeu d'entrainement, LoRA.
- Serveur Oracle : depot clone, pile Docker `server/`, tri sur `http://<ip-tailscale>:8790`.
- Cles : RunPod enregistree dans l'environnement cloud ; jeton de tri dans `server/.env` (hors git).

## Reglages qui marchent
- Image fixe : Wan 2.2 T2V low-noise seul + LoRA lightx2v, 8 pas, res_multistep / beta, 864x1152 : ~10 s.
- Edition : Qwen-Image-Edit 2509 + Lightning 8 pas, image maitre en reference : ~16 s.
- Sans maquillage : passe d'edition separee avec cette seule consigne.
- Video : image de depart generee avec le LoRA (720x1280), puis Wan 2.2 I2V high+low + lightx2v,
  4 pas, shift 5, sortie WEBM convertie en MP4. Le LoRA du personnage n'a aucun effet en I2V.
- LoRA : musubi-tuner, t2v-A14B low-noise, pas de temps 0-875, rang 32, lr 1e-4, fp8 scaled, 1024 px.

## Nuit du 13/11/2026 : passage a Z-Image et lot de lancement
- Z-Image adopte pour les images (bien plus photo realiste que Wan 2.2). Pilote valide dans ce mode.
- CORRECTION (meme soir, plus tard) : la conclusion ci-dessous etait fausse. Le v2 n'avait ete teste
  qu'a une force de 1,0. A 1,4, sans decrire les tatouages, il les place lui-meme correctement
  (6 scenes sur 6). C'est la description des tatouages dans le prompt qui les doublait. Le v2 a 1,4
  est en production ; le reentrainement prevu (~2 $) est annule.
- LoRA Z-Image v2 (lr 2e-4, 45 passages, 2115 pas, ~1 h 30) : aucun gain sur le v1. Comme le v1, il
  porte le visage mais ni la couleur des cheveux ni les tatouages, qui doivent rester decrits dans le
  prompt. Le v1 reste en production (force 1,3). Depense sans retour : ~1,30 $.
- Tatouages : le modele ne distingue pas la gauche et la droite du personnage. Decrits par position
  dans l'image ("on the left side of the picture"), ils sont justes environ 3 fois sur 4 ; sinon
  doubles ou du mauvais cote. Les tirages rates ont ete remplaces a la main (champ `seed` du plan).
  Un plan peut porter `tattoos: false` (tenue couvrante).
- Lot de lancement tous publics produit avec le pilote (`server/jobs/lancement_*.yaml`, `intro.yaml`) :
  20 photos (7 s chacune), 12 clips de 5 s en 480x832 (2 min 20 chacun), 3 essais de video
  d'introduction en 720x1280 (8 min 30 chacun). Au premier passage, 7 clips sur 12 etaient bons ;
  les 5 autres refaits avec des gestes plus calmes : 2 recuperes, 3 toujours rates (objet ou sac qui
  apparait, visage qui derive quand elle tourne la tete). Bilan : 9 clips utilisables sur 12, soit
  17 calculs pour 9 clips. Pod supprime a 20 h 35 UTC.
- Decors fixes : reportes (le modele d'edition d'image reintroduit le rendu lisse).
- Etude de niches : `docs/etude-niches.md`.

## Lecons
- Un volume reseau RunPod impose Secure Cloud et lie au centre de donnees.
- La disponibilite GPU varie d'heure en heure : prevoir plusieurs cartes de repli.
- Le premier calcul apres demarrage inclut ~2 min de chargement des modeles.
- Sans LoRA rapide, Wan vieillit les visages ; avec, il les rajeunit : surveiller l'age apparent.
- Les tatouages se recopient parfois au mauvais endroit (dos, vetement) : trier.
- L'entrainement exige `--fp8_scaled`, sinon manque de memoire au chargement sur 32 Go.
- Docker + Tailscale : ecouter directement sur l'adresse Tailscale (reseau host).
- Toujours prevoir un arret automatique du pod, et verifier qu'il tourne reellement.
- Z-Image : un LoRA entraine sur le modele de base s'applique au modele Turbo a une force de 1,3
  environ ; convertir le fichier pour ComfyUI (`convert_lora.py --target other`).
- En video, ne pas faire tourner le dos a la camera : au retour, le visage est reinvente.
- Un LoRA d'animation ne s'entraine pas sur des images fixes : le modele recoit l'image a reproduire
  en entree, la perte tombe a presque zero et rien d'utile n'est appris. Il faudrait de courts clips
  du personnage. En attendant, l'identite en video repose sur l'image de depart.
- Avant tout telechargement ou entrainement, calculer la place restante sur le volume : deux pannes
  le meme jour pour un disque plein.
- En plan large, le visage est petit : la mesure de ressemblance baisse et l'identite tient moins bien.
  Preferer les plans rapproches ou moyens.
- La bible doit decrire ce que montrent les images, pas l'inverse : verifier chaque signe distinctif
  sur le jeu de reference avant de l'ecrire dans un profil public.
- Un compte Instagram neuf peut etre suspendu des la creation : creer depuis le telephone,
  laisser vieillir l'adresse e-mail, ne pas enchainer les inscriptions le meme jour.
- Attacher ou nouer ses cheveux rate a chaque essai (3 sur 3) : geste retire des plans. Preferer
  boire, rire, s'etirer, pencher la tete, replacer une meche.
- Banniere de profil Fanvue : personnage sur le cote (le centre bas est recouvert par l'avatar), et
  image entouree de marges, car Fanvue n'affiche que le centre (environ 65 % x 67 %) sans dezoom possible.
- Le pilote doit tolerer les coupures reseau passageres (reprises automatiques).
- En video, partir d'une image ou le visage est de face : depuis un profil, le modele invente
  le visage quand elle se tourne et l'identite derive.
- Un disque conteneur de 60 Go (au lieu de 150) donne acces a plus de machines disponibles.
- Surveiller le remplissage du volume (150 Go) : un disque plein fait echouer copies et sauvegardes
  sans message clair. Supprimer les modeles d'entrainement apres usage (retelechargeables en 1 min).
- Sur un serveur deja utilise, verifier les noms de services existants avant d'en creer un ;
  prefixer tout ce qui releve du projet (`girls-ai-...`).

- Z-Image : entrainer plus longtemps ou plus fort ne fait pas apprendre cheveux et tatouages au
  LoRA ; c'est le jeu de reference qu'il faudrait refaire (tatouages identiques sur toutes les
  images, legendes qui ne les decrivent pas). En attendant : description dans le prompt + tri.
- En video, les gestes amples deforment le visage : main devant le visage, tete renversee, grand
  rire, cheveux au vent, salut de la main trop pres de l'objectif. Les gestes qui tiennent : boire,
  sourire, regarder ailleurs puis revenir, respirer, petit signe de tete.
- Verifier les images de depart sur une planche avant de lancer les clips : 7 s par image contre
  plus de 2 min par clip.
- Avant de conclure qu'un LoRA n'a pas appris un trait, le tester a plusieurs forces (1,0 a 1,8)
  et sans description du trait dans le prompt. Decrire un trait que le LoRA connait deja le double.
- Instagram : la verification "vraie personne" par selfie compare le selfie aux photos du profil.
  Un compte au nom et au visage d'un personnage IA ne peut pas la passer : ne pas envoyer le selfie
  du proprietaire, ne pas fabriquer un selfie du personnage.
- RTX 5090 : 1,39 $/h constate le 13/11 (PRO 4500 : 0,72 $/h ; 4090 : 0,89 $/h).
- Clip "debut/fin" (Wan 2.2, noeud WanFirstLastFrameToVideo, memes modeles I2V) : avec une image
  de depart et une image de fin imposees, un changement de pose reussit (se lever du lit), alors
  qu'avec la seule image de depart elle ne se leve jamais. L'image de fin est fabriquee par edition
  de la premiere (meme piece, meme tenue). Champ `end_edit` d'un plan. Meme duree qu'un clip normal.
- Regle pour la video : un changement d'etat (pose, tenue, lieu) se fait par une image de fin
  imposee ou a la coupe entre deux plans, jamais invente dans un plan de 5 s.
- Le francais est compris directement par Z-Image (images) et par Wan 2.2 (mouvement) : pas de
  traduction necessaire dans le formulaire. Les cheveux sortent un peu moins cuivres qu'en anglais.
- Sur certaines machines, le premier chargement de chaque modele depuis le volume prend 2 a 5 min :
  prevoir des delais d'attente longs.
- Le proxy RunPod coupe les envois de plus de 100 Mo : deposer les gros fichiers par l'API de
  fichiers de Jupyter, en morceaux (ce que fait "pilot lora add").
- Scene en sous-scenes enchainees (essai du 14/11, 2 sous-scenes) : une reussie, une avec un fondu
  fantome au milieu, parce que l'image de fin avait un cadrage plus large que l'image de depart.
  L'image de fin doit garder le meme cadrage ; consigne renforcee dans le pilote, a reverifier.
- Page Test : pod garde en veille entre deux tests (arret apres 10 min sans test). Mesure du
  14/11 : premier test 163 s, test suivant sur le meme pod 17 s.
- Essai ceinture (14/11, `server/jobs/test_ceinture.yaml`, seed constante, brassiere + short et bikini) :
  aucune trace de ceinture sur la taille nue, a 1,4 comme a 1,2 et 1,0. A 1,0, le tatouage d'epaule
  disparait (bikini) ou palit ; a 1,2, tatouages et visage tiennent. La trace n'apparait donc qu'avec
  le bas du corps nu : comparaison 1,4 / 1,2 a faire par le proprietaire sur ses plans (`char_strength`).
- Plafond GPU applique par le pilote (14/11) : registre `data/depenses.jsonl`, refus de creer un pod
  au-dela de 7,50 $ par jour, tous lanceurs confondus. Fiche `docs/agents.md` pour un agent tiers
  (OpenClaw) configure par le proprietaire.
## Couts constates
- Volume : ~0,35 $/jour. Sessions de generation : 0,20 a 0,30 $ chacune.
- Entrainement du LoRA : ~3 $ (RTX 5090 a 1,39 $/h, ~2 h 15 installation comprise).
- Session du 13/11 apres-midi (controle qualite, tests de rendu, LoRA d'animation rate, tests du pilote) : ~2,30 $.
- Session type du pilote : 2 plans en 9 a 17 min, 0,10 a 0,20 $.

- Nuit du 13/11 (plafond 10 $) : ~6 $. Pod RTX 4090 a 0,89 $/h pendant ~5 h (deux entrainements
  de LoRA Z-Image, comparaisons, lot de lancement) ~4,50 $ ; sessions de test du debut de soiree ~1,50 $.
- Cout unitaire constate sur RTX 4090 : photo ~0,002 $ ; clip 5 s en 480p ~0,035 $ ; clip 5 s en 720p ~0,13 $.
- Hrafnvik (13/11, planches des trois personnages) : ~1 $ en six courtes sessions.
- Fin de soiree du 13/11 : verification du LoRA v2 sur RTX 5090, ~0,30 $. Total de la soiree : ~7,50 $.
- Nuit du 13 au 14/11, fin : essai debut/fin, test du francais et validation dans le pilote, ~0,50 $.
  Total de la soiree : ~8 $ sur le plafond de 10 $.
- 14/11, 0 h a 0 h 40 : mise au point du studio (depot de LoRA, test d'images, scene en sous-scenes), ~0,45 $.
  Total depuis le 13/11 au soir : ~8,50 $ sur le plafond de 10 $.
- 14/11 matin : essai ceinture, RTX PRO 4500, 2,4 min, 0,03 $. Plafond courant : 7,50 $/jour.
- 14/11, essais de l'atelier : 3 images (0,02 $), un demarrage de pod avorte (0,01 $), un clip 480p
  (0,08 $), pod de veille ~10 min (0,07 $). Total ~0,18 $ ; depense du jour 0,66 $ sur 7,50 $.
- 14/11, essai des trois temps : 2 images du temps 2 sur le pod de veille (~7 min), 0,18 $ ;
  depense du jour 0,84 $ sur 7,50 $.
- 14/11, essai des raccords hors atelier (`essai_raccord`, RTX 5090, 10 min) : image, image par retouche de la
  reference, clip, clip continu qui arrive sur l'image suivante, clip : 0,23 $. Resultat : meme personne, meme
  tenue, meme cuisine sur l'image retouchee ; jointure du clip continu sans saut visible, legere derive de
  couleur (2 a 4 points sur 255).

## Comptes (13/11/2026)
- Gmail `lea.morel.ai@gmail.com` (nom affiche Lea Morel).
- Instagram : suspendu une seconde fois le 13/11 apres la verification par selfie (photo du
  proprietaire sur un profil au visage de Lea). Ne pas recreer de compte.
- TikTok : a creer depuis le telephone, un autre jour.
- Fanvue : Fully AI, NSFW ; verification d'identite envoyee, fiche Creator Personality complete,
  coordonnees bancaires renseignees ; en attente de validation du compte.

## Limites et points ouverts
- Rendu lisse regle par Z-Image ; tatouages regles par le LoRA v2 a 1,4 (a confirmer sur un lot entier) ;
  clips en 480p seulement (720p + agrandissement a mettre en place).
- Clips de 5 s sans son : montage et voix a construire.
- Le contenu explicite n'est pas produit par l'assistant : a piloter soi-meme dans ComfyUI.
- Generateur de textes de profil (`pipeline/profile_texts.py`) : produit aussi la fiche Fanvue complete
  (17 champs, FR + EN) et signale les manques de la bible. Requete verifiee avec --dry-run ; appel a
  l'API non teste (pas de cle Anthropic dans l'environnement de developpement).
- Tranche le 13/11 : la petite puce a l'oreille droite, visible sur les images de reference, est assumee
  (lobes perces). La fiche Fanvue "Mes modifications corporelles" ne la mentionne pas : a completer si souhaite.
- A faire : LoRA d'animation a valider, planification du pilote, branchement du controle qualite,
  montage et voix, contestation Instagram, compte TikTok, fin d'inscription Fanvue, publication.
- 14/11, 11 h 20 : pod de clips `girls-ai-p0002r2` reste orphelin environ 2 min (redemarrage de `triage` trois
  secondes apres un lancement du proprietaire), supprime a la main : ~0,03 $. Calcul a relancer.
- 14/11, 15 h : essai p0004 (accroche tous publics "cafe du matin", 15 s) pour verifier le montage revu : 3 images
  deux fois (point de vue mal ecrit la premiere fois : le telephone etait dessine dans le cadre) et 3 clips : 0,35 $.
  Depense du jour : 2,26 $ sur 7,50 $. Constats : continuite tenue, raccord sans coupe propre, duree visee respectee ;
  a corriger : l'accroche chevauche le texte de la scene suivante sur un raccord continu, mention IA trop pale.
