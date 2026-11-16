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
- 14/11, soir : corrections tirees de l'essai p0004 (texte efface avant un raccord sans coupe, mention IA lisible,
  controle du point de vue, gros plan tire a part). Cinq images d'essai de la scene 3 : 0,09 $. Deux voies ecartees :
  la retouche garde le cadrage de la reference, meme avec une consigne de zoom ou une reference recadree.
  Depense du jour : 2,48 $ sur 7,50 $. p0004 remonte (`final_v2.mp4`) : les deux defauts de texte ont disparu.
- 14/11, nuit : hub des modeles et des LoRA en service (`/hub`, commit 490832a) : catalogue Civitai et Hugging Face
  avec vignettes, categories liees aux temps, retenues, chargement sur le volume au clic, veille
  (`docs/veille-modeles.md`). Verifie en service : recherche, retenir, regler, retirer, quatre onglets a 390 px.
  Non essaye (payant) : le chargement sur le volume et une LoRA video dans un clip. Aucune depense.
- 14/11, nuit : espace reseaux en service (`/social`, commit de7446a) : semaine de selfies tous publics ecrite par le
  redacteur puis calculee sur le pod de veille, file a valider, texte (legende, mention IA, hashtags) et image prets
  a publier a la main. Automatique par personnage, desactive par defaut. Essai reel : semaine du 16/11 de Lea,
  7 textes puis 7 images en 3,8 min, environ 0,17 $ veille du pod comprise. Depense du jour : 2,80 $ sur 7,50 $.
  Les 7 publications attendent dans la file.
- 14/11, nuit : rendu au montage (atelier, etape montage, reglage « Rendu » par projet) : « net » (inchange, defaut),
  « telephone pose » (nettete accentuee, noirs releves, grain de capteur a la resolution finale, sous les textes),
  « tenu a la main » (le meme, plus une derive lente, un fremissement et une rotation de 0,2 degre, continus aux
  raccords sans coupe). Aucun recalcul GPU. Essai sur p0004 (15 s) : montage 47 s en net, 81 s tenu a la main,
  fichier 10 puis 15 Mo ; `final_v3.mp4` de p0004 est en rendu tenu a la main. Aucune depense.
- 14/11, nuit : transitions et camera au montage (modele de plan 2026-11-14i). Deux champs par scene, fabriques au
  montage sans GPU : `transition` (coupe, fondu, filage = panoramique file de 0,2 s, zoom = avancee rapide du plan
  qui sort puis fondu tres court) et `camera` (avance, recul, gauche, droite, par recadrage de 8 %, continue sur les
  raccords sans coupe). Le redacteur les ecrit, le controle des plans les verifie, les depots des agents les portent
  (`docs/agents.md`, « Continuite et raccords »). Essai sur p0004 : `final_v4.mp4` (file puis zoom, camera qui
  avance sur le premier groupe), montage 90 s. Aucune depense. Disque : 30 Go sur 197.
- 14/11, nuit : essai d'une LoRA video (Wan 2.2, « Shaky, handheld camera », fichier unique cote « high », force 1,0,
  mot declencheur ajoute par le pilote). Chargement sur le volume puis deux clips 480p du meme tirage, sans et avec :
  0,09 $ les deux clips, 7,7 min. Resultat : pas de tremblement visible ; le decor bouge autant dans les deux clips
  (ecart a la premiere image, bande haute : 27,9 dB sans, 27,1 dB avec), seul le geste du personnage change un peu.
  Conclusion : la chaine des LoRA video marche (hub, volume, pilote), mais celle-ci n'apporte rien ; le rendu « tenu
  a la main » du montage fait mieux, sans GPU. Correctif au passage : une LoRA video a fichier unique garde son cote
  (commit b6e2542). Depense du jour : 3,02 $ sur 7,50 $.
- 14/11 : le proprietaire a pu rouvrir le compte Instagram de Lea ce matin. Instagram reste une cible de l'espace
  reseaux (`/social`), publication a la main apres validation, mention IA dans chaque legende et label natif.
- 14/11, nuit : son, premiere marche. Commande `pilot son "<phrase en anglais>" --nom ... --duree 30 --variantes 3` :
  ambiance sonore par Stable Audio Open 1.0 (licence Stability AI Community, usage commercial gratuit sous 1 M$ de
  chiffre d'affaires ; noeuds d'origine de ComfyUI), rangee dans `data/audio/`, ou le montage la propose deja comme
  musique. PAS ENCORE ESSAYEE JUSQU'AU BOUT : le depot du modele (4,9 Go) sur le volume a echoue a 2 Go, volume plein
  (Errno 122). Le fichier partiel a ete supprime. Mesure du volume RunPod `lea-models` (150 Go) : environ 146 Go
  occupes, dont modeles de ComfyUI 107 Go (diffusion 76, encodeurs de texte 24, LoRA 6,5), `train_models` 23,7 Go
  (modeles d'entrainement : z_image_bf16 12,3 et umt5 11,4), `lea_lora` 7,2 Go (essais d'entrainement Wan, dont 7
  etapes intermediaires de 0,6 Go), sorties 0,9 Go. Il manque environ 2 Go pour le son ; rien n'est supprime sans
  l'accord du proprietaire. Depense : 0,09 $ (depot interrompu et deux pods de mesure). Depense du jour : 3,11 $ sur
  7,50 $. Hub : une fiche au nom adulte est ecartee des categories tous publics meme sans marque de la source.
- 14/11, nuit : son, essai reussi. Avec l'accord du proprietaire, les 7 etapes intermediaires de `lea_lora`
  (`leamorel_t2v_low_v1-0000NN`, 4,3 Go) ont ete supprimees du volume ; la version finale reste. Modeles du son
  deposes (5,7 Go, 5 min, une seule fois), puis trois ambiances de cuisine de 20 s en 6 s chacune :
  `data/audio/girls_ai_cuisine_1.m4a` a `_3.m4a`. p0004 remonte avec la premiere (`final_v5.mp4`, piste son AAC).
  Non juge a l'oreille par l'assistant : au proprietaire d'ecouter. Depense : 0,10 $. Depense du jour : 3,21 $ sur
  7,50 $. Une ambiance seule, modeles en place : un pod de 2 a 3 min, environ 0,03 a 0,05 $.
- 14/11, nuit : ambiance sonore dans l'atelier (modele de plan 2026-11-14j). Le projet porte une phrase
  `ambiance` (en anglais, fond sonore du lieu, sans musique ni voix), ecrite par le redacteur avec le scenario du
  temps 1 ou deposee par un agent (bloc `atelier`). Etape Montage, rubrique Son : « Fabriquer l'ambiance » loue un
  pod, range `data/audio/pNNNN_ambiance.m4a` (45 s) et le choisit comme bande-son. Essai sur p0004 : fichier pret,
  niveau moyen -17,8 dB, remonte en `final_v6.mp4`. Depense : 0,02 $. Depense du jour : 3,23 $ sur 7,50 $.
  Reste pour le son : voix off, musique, son cale sur les gestes.
- 14/11, nuit : bruit des gestes (modele de plan 2026-11-14k). Priorite du proprietaire pour le son : gestes,
  puis voix off (facultative), puis voix du personnage ; pas de musique. Aucun modele « qui regarde la video »
  n'est utilisable ici : MMAudio est sous licence non commerciale, HunyuanVideo-Foley exclut l'Union europeenne,
  LTX-2 ne tient pas sur le volume. Voie retenue : chaque scene porte `son` (une phrase en anglais, un seul bruit
  bref), fabrique par Stable Audio Open sur le meme pod que l'ambiance (« Fabriquer les sons », seuls les sons
  nouveaux ou changes ; `data/audio/bruits/pNNNN_sN.m4a`). Au montage, le bruit est pose la ou l'image du plan
  bouge le plus, sinon a une seconde du debut ; le champ « Instant (s) » le fixe a la main. Limite : c'est un
  calage sur le mouvement, approximatif. Essai sur p0004 : deux bruits (gorgee, tasse posee), `final_v7.mp4`, le
  premier cale sur le geste a 5,12 s, le second par defaut (image fixe). Non juge a l'oreille par l'assistant.
  Depense : 0,02 $ (pod de 1,3 min). Depense du jour : 3,24 $ sur 7,50 $.
- 14/11, nuit : licences. Decision du proprietaire : ne plus bloquer sur la licence des LoRA et des modeles. Le hub
  charge desormais une LoRA dont la licence n'admet pas l'usage commercial ; la mention reste affichee sur la
  fiche et a cote de la case de chargement. Le risque (retrait, reclamation) est celui du proprietaire pour toute
  video publiee ; les essais prives restent sans enjeu.
- 14/11, nuit : essai de MMAudio (son fabrique d'apres la video, licence non commerciale) sur trois clips de
  p0004, hors ComfyUI, dans `girls-ai-mmaudio` sur le volume (23 Go ; volume agrandi a 300 Go par le
  proprietaire). Cinq pods : trois echecs d'installation ou de depot (torchaudio absent, enregistrement par
  torchcodec incompatible avec la carte, depot refuse au demarrage du pod), puis quatre sons de 5 s obtenus
  (`data/work/mmaudio/`, copies `projets/p0004/mmaudio_*.mp4` : s2 avec et sans phrase, s1 et s4 sans phrase).
  Environ 2,5 min par clip, modele recharge a chaque fois. Non juge a l'oreille par l'assistant ; pas encore
  branche dans l'atelier. Depense : 0,51 $ en tout. Depense du jour : 3,75 $ sur 7,50 $.
- 14/11, nuit : essai de voix. Qwen3-TTS 1.7B VoiceDesign (Apache 2.0, voix creee par description, aucune
  personne reelle), en francais, dans `girls-ai-voix` sur le volume (5,6 Go, torch repris de `girls-ai-mmaudio`).
  Deux descriptions de voix, trois phrases chacune : `data/work/voix/voix_*.wav` (24 kHz, 2 a 6 s), assemblees en
  `projets/p0004/voix_a.m4a` et `voix_b.m4a`. Non juge a l'oreille par l'assistant. A verifier a l'ecoute : le
  naturel du francais, et si la voix reste la meme d'une phrase a l'autre (chaque phrase est creee a part).
  Depense : 0,13 $ (pod de 10,5 min, installation comprise). Depense du jour : 3,88 $ sur 7,50 $.
- 14/11, nuit : son d'apres l'image dans l'atelier (commit `d15655f`). Le proprietaire a juge MMAudio a
  l'ecoute (« ca colle a l'image »). `pilot sonimage` : lot de clips retenus d'un temps, script sur le pod (modele
  charge une fois), lance par un terminal de Jupyter (client websocket en bibliotheque standard), sons ranges dans
  `data/audio/image/<clip>.m4a`. Etape Montage : bouton « Son d'apres l'image », case « L'utiliser au montage » ;
  le son du clip remplace le bruit du geste, l'ambiance reste en fond. Essai sur p0004 : 3 clips, pod de 3,7 min,
  0,04 $ ; `final_v8.mp4` (s1, s2, s4 par l'image ; s3, image fixe, garde son bruit). Non juge a l'oreille par
  l'assistant. Depense du jour : 3,92 $ sur 7,50 $.
- 14/11, nuit : retours du proprietaire sur `final_v8` (sons qui continuent sur une image fixe, sons trop forts
  par rapport au reste) et sur la voix a (credible, mais on sent l'IA et le timbre change a la fin). Montage
  (commit `6753fb3`) : le bruit du geste est coupe a la fin de son plan (fondu de 0,25 s, sauf raccord sans coupe)
  et baisse de 6 dB ; chaque son d'apres l'image est mesure sur la part montee et mis a un niveau moyen de
  -30 dB, crete retenue a -8 dB ; rendu « tenu a la main » par defaut pour un nouveau projet (les projets
  existants ne changent pas). p0004 remonte : `final_v9.mp4`. Voix : essai de clonage de la voix a (Qwen3-TTS
  Base, ajoute sur le volume dans `girls-ai-voix`), quatre phrases dont une de 9 s : voix c (clonage complet) et
  voix d (timbre seul), `projets/p0004/voix_c.mp4` et `voix_d.mp4`, sur la page d'ecoute. Non juge a l'oreille
  par l'assistant. Depense : 0,09 $ (pod de 7,8 min). Depense du jour : 4,02 $ sur 7,50 $.
- 14/11, nuit : p0003 lance a la demande du proprietaire (« lance ») : chaine sur les temps 1 a 4, tout refaire,
  arret apres les images pour le choix des prises (17 images ; devis de la chaine entiere : 1,25 $).
  Images de p0003 : 0,09 $, plus le pod de veille de l'atelier jusqu'a son arret. Le proprietaire a regarde les
  images : « plein de trucs ne collent pas », pas de video. Chaine laissee en pause, rien d'autre produit.
  Constat de l'assistant sur les temps 1 et 2 seulement : gestes et accessoires non rendus (meme pose debout
  d'une image a l'autre), image de reference cheveux laches alors que la fiche dit queue-de-cheval, decor qui
  change, peau lisse ; cause probable : chaque image part de la reference, qui impose sa pose. En attente de ce
  qui gene le plus le proprietaire. Depense du jour : 4,22 $ sur 7,50 $.
- 14/11, nuit : passe d'interface, premiere partie (commit `b079f25`). Accueil, Tri, Test et Plan chargent
  `ui.css` : meme en-tete que l'atelier et le hub (lien Studio, titre), memes champs et boutons. Accueil : deux
  groupes (Produire : Atelier, Reseaux, Hub ; Outils : Test, Tri, Plan), icones ; Plan signale comme ancien
  formulaire. Test : lignes de LoRA en grille (nom, force, declencheur dessous), boutons de verdict en contour.
  Atelier : les deux boutons « Tout refaire » du son s'appellent « Refaire tous les sons » et « Refaire d'apres
  l'image ». Verifie par captures Chromium en 390 et 1100 px, sans debordement. Disque : 31 Go sur 197.
- 14/11, nuit : tirage par temps, LoRA du temps au calcul, cases de verdict (retours du proprietaire sur p0003 :
  veste qui apparait, tenue qui tourne aux sous-vetements chair, gestes non executes). Champ de projet `tirage` :
  `ref` (retouche de la reference) ou `direct` (image creee a part), regle dans la fiche de continuite ; par defaut
  `ref` aux temps 1 et 2, `direct` aux temps 3 et 4, projets existants compris. Au calcul, une scene sans LoRA prend
  celles de son temps (`lora_defauts.json`, jamais enregistre a ce jour) ; les LoRA partent aussi avec les clips :
  l'atelier ne les envoyait qu'avec les images, une LoRA video n'etait donc jamais chargee. Cases de verdict sous
  chaque image retenue (`verdicts.json`, codes sans texte). Essai sur p0004, temps 1 en `direct`, deux images :
  meme personne, meme tenue, meme cuisine, pose plus libre ; reglage remis a `ref`. 0,06 $ ; depense du jour
  4,28 $ sur 7,50 $. Corrige au passage : le script de deploiement reecrivait la chaine en pause sans sa version,
  la migration trois vers quatre temps se rejouait (temps de la chaine de p0003 retablis a 1, 2, 3, 4).
  Disque : 31 Go sur 197.
- 15/11 : LoRA au niveau du projet (demande du proprietaire : tout se regle au niveau du temps, rarement de la
  scene). Champ de projet `loras` (`"0"` tout le projet, `"1"` a `"4"` un temps), section « LoRA » en haut de chaque
  temps : puces du catalogue a toucher, force, mots declencheurs affiches (le pilote les ajoute seul). Une scene
  recoit projet + temps + les siennes ; une LoRA non admise a un temps y est ignoree. Les « LoRA par defaut »
  globales (champ texte de la Bibliotheque, jamais remplies) sont retirees de la page. Constat sur le catalogue :
  5 LoRA seulement, dont 2 de la categorie nu, sans mot declencheur note, aucune de pose ou d'acte, aucune LoRA de
  clip pour adultes : c'est la cause probable des gestes non rendus aux temps 3 et 4. Verifie sur p0004 (LoRA
  effectives par temps, capture), remis a vide. Aucune depense.
- 15/11 : hub, chargement des LoRA retenues. Le chargement du 14/11 a 23 h 12 (2 LoRA de Civitai) avait echoue :
  HTTP 400 du stockage vers lequel Civitai redirige, parce que la cle de Civitai suivait la redirection. `pilot/http.py`
  ne transmet plus l'en-tete Authorization a un autre hote ; verifie sans pod sur les 5 fiches retenues (premiers
  octets de chaque fichier). Page Hub : les LoRA en attente sont dans le lot d'office (case a decocher, retenue d'une
  visite a l'autre) au lieu de cases a recocher a chaque visite. Atelier : le panneau LoRA nomme les LoRA retenues pas
  encore chargees, avec un lien pour les charger. Le pod du chargement rate a coute environ 0,01 $.
- 15/11 : hub, supprimer une LoRA. Corbeille dans « Notre liste » et bouton « Supprimer » dans le reglage d'une
  retenue : la LoRA sort du catalogue et des retenues, son fichier est efface du volume au prochain chargement ou
  sur « Effacer maintenant ». Essai reel sur un pod avec un fichier d'essai : efface, nom inattendu refuse, pod
  supprime. Environ 0,03 $ ; depense du jour 0,51 $ sur 7,50 $.
- 15/11 : atelier, refonte de la page d'un projet (demande du proprietaire : ordre, agencement, moins de texte, plus
  d'icones). Colonne de travail dans l'ordre du geste : Preparer, Scenes, Produire, Monter. Tout ce qui vaut pour le
  projet entier passe dans un panneau de cote a place fixe (colonne de droite sur ecran large, barre d'icones en bas
  sur telephone) : Projet, Continuite, LoRA, Montage, Son, Chaine, Publier. Une scene montre trois champs (image,
  mouvement, texte) ; le reste est sous « Plus ». Les aides sont repliees derriere un « i » (toucher pour lire ;
  bouton de l'en-tete pour toutes les afficher). Rien n'est supprime. Verifie par captures en 390 et 1280 px sur
  p0004, sans erreur. Aucune depense. Disque : 31 Go sur 197.
- 15/11 : essai, partir de l'image precedente (question du proprietaire). 13 images tous publics sur p0004, meme
  tirage, cible : autre pose (coudes sur le plan de travail) puis autre tenue. Creee a partir de la precedente
  (Z-Image, debruitage 0,6 et 0,75) : la pose de depart reste, le geste demande n'est pas fait ; a 0,9 le geste est
  fait mais il ne reste rien de l'image de depart (resultat egal a une image creee a part). En chaine sur trois
  images : aucun des gestes demandes n'est fait. Depuis la fin d'un clip : le flou de l'image vidéo est pris pour un
  autre objet. Creee a part avec le meme tirage : pose et tenue justes, cuisine presque identique d'une image a
  l'autre. Retouche de la reference (Qwen) : pose et tenue justes, vraie piece gardee, visage un peu moins fidele,
  pas de LoRA. Conclusion : ne pas partir de l'image precedente ; garder « creee a part » aux temps 3 et 4, avec un
  tirage commun aux scenes d'un temps. Images dans data/work/girls-ai-essai-i2i. Pod de 5 minutes, environ 0,06 $.
  Mis en place le jour meme : `graines` au projet (un tirage par temps), repris par la premiere image creee a part
  de chaque scene ; « Autre image » garde un tirage propre a la scene. Format des plans inchange. Pas encore
  verifie sur une production reelle (aucune depense).
- 15/11 : essai « replacer dans la vraie piece » (p0004, tous publics). Seconde passe Qwen-Image-Edit a deux images :
  image 1 = image creee a part (pose, tenue), image 2 = reference du projet (ou la piece videe de son personnage).
  Trois poses. Pose, tenue et visage gardes presque a l'identique ; la piece ne se rapproche vraiment de la
  reference que sur une image sur trois (poignees, meubles), les deux autres sortent quasi inchangees. Defauts
  ajoutes : tatouages inventes sur l'avant-bras (surtout avec la piece vide), peau plus rouge et plus lisse.
  Limite de l'essai : les images creees a part avaient deja une cuisine tres proche de la reference (meme tirage,
  meme description du lieu). Conclusion : pas branche dans l'atelier ; le tirage commun et un « lieu » precis
  suffisent pour l'instant. Images dans data/work/girls-ai-essai-decor, planches p0004essai_decor_a/b/c dans le Tri.
  Pod de 5 minutes, environ 0,06 $.
- 15/11 : scenariste et casting confies a l'agent du proprietaire (OpenClaw). Mis en place, sans depense GPU :
  `tools/triage/verifier.py` (l'agent verifie lui-meme ses depots : refus, modele perime, remarques du controle des
  plans, code de sortie) ; modele de plan `2026-11-15a` (`atelier.projet_de` : les quatre temps d'une video se deposent
  ensemble, les temps 2 a 4 suivent le projet ouvert par le fichier du temps 1) ; depot de fiches de personnage
  (`server/jobs/personnage.modele.yaml`, `server/jobs/atelier/personnages/`, section "Fiches deposees par votre agent"
  de la page Personnages, enregistrement par le proprietaire seulement) ; deux skills dans `agents/`
  (`girls-ai-scenariste`, `girls-ai-casting`), courts, qui renvoient aux regles du depot pour suivre les changements
  de format. Rien n'est ecrit dans la configuration d'OpenClaw : le proprietaire demande l'installation a son agent.
- 15/11 : essai d'un controleur d'images (`pilot controle --nom pNNNN,pNNNN`, `server/pilot/controle.py`), demande
  par le proprietaire sur tous les temps. Sur le pod, hors ComfyUI, dans `/workspace/girls-ai-controle` (16 Go de
  poids ajoutes au volume) : Qwen2.5-VL 7B compare chaque image a sa description et repond par des cases fermees
  (decor, tenue, pose, objet, cadrage, anatomie, note sur 10) ; aucun texte libre ne revient du pod. 53 images de
  p0002, p0003 et p0004 notees en 1 min 40 ; aucun refus du modele, a aucun temps. Resultat : la note globale separe
  bien les images (2 = ratee, 7-8 = fidele) ; les cases de detail basculent toutes en « faux » quand la note est
  basse, donc elles ne disent pas quoi corriger ; un objet en trop n'est pas vu (la question ne le demandait pas).
  Sur les 9 images jugees par le proprietaire : 5 ratees sur 7 nettement signalees, 1 signalee par la case tenue,
  1 manquee ; 1 bonne sur 2 rejetee a tort (temps 4, ou 14 images sur 18 recoivent 2 : a verifier a l'oeil).
  Le mesureur de visage (facenet-pytorch) n'a rien rendu : a reprendre. Notes dans `data/work/controle/`.
  Deux pods : 16 minutes (installation ratee, module PIL absent, 0,19 $) puis 7 minutes (0,08 $).
- 15/11, suite du controleur. Essai 3 (une question par point, reponse en un mot) : regression, tout recoit 6 a 8,
  y compris les images ratees ; abandonne (8 min, 0,10 $). Essai 4, formule retenue : la question d'ensemble de
  l'essai 2 (note sur 10 et cases) plus huit questions fermees oui/non dont on lit la probabilite du « oui » au
  premier mot (`p` : fidele, decor, tenue, geste, objet, cadrage, en_trop, anatomie), et le mesureur de visage
  repare (`requests` manquait) : `visages`, `taille_visage`, `ressemblance` (mediane avec les autres images du meme
  personnage ; sous 0,6 = visage different). 53 images en 9,5 min, 0,11 $. Sur les 9 images jugees : 6 ratees sur 7
  signalees (dont l'objet en trop, par `en_trop`), 1 manquee (tenue, temps 3) ; 1 bonne sur 2 rejetee a tort
  (temps 4, deux visages). `en_trop` a aussi sonne sur une image jugee bonne. La question sur l'anatomie ne sonne
  jamais : a ne pas compter. Les notes vont dans `data/projets/<pid>/notes_images.json` et s'affichent dans
  l'Atelier sous les cases de verdict de chaque image (« Controle automatique (essai) ») ; rien n'est refait d'apres
  elles. Reste a decider : la relance automatique (3 images par scene), quand les notes seront jugees fiables.
- 15/11 : relance automatique branchee, apres accord du proprietaire. Un lancement d'images depuis l'Atelier calcule
  trois images par scene (`pilot serie` : trois fichiers de plans, tirage decale), le controleur les note pendant
  que le pod de calcul reste en veille, et une scene dont aucune image ne depasse 4 est refaite seule, deux fois au
  plus (`SEUIL_RELANCE`, `RELANCES`). L'Atelier propose la mieux notee de la serie et affiche la note sous chaque
  vignette ; le proprietaire garde le choix. Les alertes « tenue » et « en trop » s'affichent sans rien declencher.
  Un controleur en panne n'arrete rien : les images restent, sans note. Essai reel sur p0004 (2 scenes, 6 images) :
  notes 5 a 8, aucune relance, image proposee = la mieux notee ; 13,5 min en tout (8,5 min d'images, 5 min de
  controle dont 3 d'installation), 0,27 $. Defaut connu : une minute a une minute et demie par image, parce que les
  trois variantes alternent le modele d'image et le modele de retouche ; a regrouper par modele. La relance
  elle-meme n'a pas encore tourne en reel (aucune scene sous le seuil). Plus tard, vers 50 verdicts du
  proprietaire : recalculer le seuil d'apres `verdicts.json` compare a `notes_images.json`.
- 15/11 : variantes regroupees, a la demande du proprietaire. `pilot serie` fond les trois fichiers de plans en un
  seul lancement (`data/work/girls-ai-serie-<pid>.json`, chaque plan garde le nom de fichier de sa variante par
  `sortie`) et `pilot run` calcule les images creees avant les retouches. Meme essai sur p0004 (2 scenes, 6 images) :
  3 min 30 d'images au lieu de 8 min 30 (9 s par image creee et 18 s par retouche une fois le modele charge),
  8 min 30 en tout au lieu de 13 min 30 ; 0,32 $ au releve (pod de calcul a demarrer compris). Le pod du controleur demarre maintenant d'apres le nombre
  d'images. Reste lent : le controle (4 min, dont 2 d'installation a chaque pod).
- 15/11 : pose decomposee, apres l'avis du scenariste ("je peux raconter une scene, je ne peux pas la specifier").
  Modele de plan `2026-11-15b` : champs facultatifs `pose` (position, appui, bassin, genoux, mains, regard), `contact`
  et `autres` (les autres personnes visibles a l'image ; vide quand elle est seule, a la demande du proprietaire qui ne
  veut pas d'un champ "partenaire" rempli a chaque plan). Un champ rempli est ajoute a la description (pose en tete,
  `autres` a la fin) et verifie a part par le controleur (une question oui/non par champ, `champs` dans
  `notes_images.json`) ; avec `autres`, le controle ne signale plus la seconde personne. Page : bloc "Pose detaillee"
  dans "Plus". Retour au scenariste : `verifier.py --notes pNNNN` (note, points douteux ou absents, cases du
  proprietaire, sans texte libre). Limite : les champs aident a verifier, ils ne forcent pas le modele d'image ;
  seuils (0,35 et 0,6) a caler sur les verdicts.

- 15/11, pose decomposee, essai reel du controle champ par champ sur p0004 (24 images, 0,09 $, 7,8 min) : chaque champ
  faux expres (regard, mains, autre personne) sort a 0,0 sur toutes les images ; les champs vrais sortent entre 0,5 et
  0,99 (un seul a 0,15 sur une image). Les seuils 0,35 et 0,6 separent bien. Champs d'essai retires. Depense du jour
  apres l'essai : 1,90 $ sur 7,50 $.
- 15/11, LoRA par defaut des temps (modele `2026-11-15c`), a la demande du proprietaire : formulaire dans la
  Bibliotheque de LoRA (une LoRA d'image et une de clip par temps), posees sur le projet a sa creation ou au premier
  depot du temps, retirables ; alerte du controle des plans pour un temps 4 sans LoRA porno d'image ou de clip (grave,
  non bloquante) et un temps 3 sans LoRA de nu. Le choix des LoRA reste au proprietaire.
- 15/11, hub et Bibliotheque de LoRA : une correction faite dans la Bibliotheque (categorie, force, intitule, mots
  declencheurs) est maintenant recopiee dans la fiche du hub. Avant, le hub gardait l'ancienne valeur et la remettait
  au catalogue a son prochain reglage (cas vu sur une LoRA reclassee par le proprietaire, alignee a la main).
- 15/11, les deux LoRA inscrites dans `persona/production.yaml` passent dans `server/data/lora_catalog.yaml` (memes
  valeurs, licence recopiee dans leur note) : le proprietaire peut maintenant les corriger et les retirer depuis la
  Bibliotheque comme les autres. `lora_catalog` du depot reste vide.
- 15/11, alerte des LoRA : au temps 3, plus de remarque pour le clip (aucune LoRA de nu de clip n'existe, la remarque
  ne pouvait pas disparaitre) ; seule l'image est verifiee. Temps 4 inchange.
- 15/11, interface reprise pour un proprietaire qui lit et decide, sans retoucher les prompts : panneau du projet a
  gauche sur ecran large ; scenes en tuiles (image en grand, texte a l'ecran, verdict, note du controle ; le texte et
  les reglages de la scene sont replies, les remarques du controle des plans s'affichent dans la tuile avec un bouton
  pour l'ouvrir ; deplacer, dupliquer, supprimer passent dans le pli) ; LoRA en tuiles a cocher (categorie, image ou
  clip, temps, force) ; projets, Bibliotheque et LoRA par defaut en grille. Espace reseaux : choix des LoRA d'image
  tous publics du catalogue par personnage (`loras` de `reglages.json`), a defaut celles par defaut du temps 1,
  filtrees (image, tous publics, presentes sur le volume). Aucune depense GPU.
- 15/11, decoupage (passages entre scenes et camera). Constat : quatre passages seulement, un file a sens unique, une
  camera toujours lente, et des champs facultatifs que l'agent pouvait oublier. Ajoute au montage, sans GPU : file dans
  les quatre sens (flou dans le sens du mouvement), glisse lent, fondu lent, dezoom (le plan arrive de pres et recule
  vite) ; camera qui monte ou descend, et mouvement vif en debut de plan (`avance_vif`, `recul_vif`). Un passage est
  garde des que les deux plans durent plus de deux fois sa duree (avant : trois fois). Modele de plans `2026-11-15d` :
  tout plan en raccord coupe dit `transition` (sauf le premier) et `camera`, `coupe` et `fixe` compris ; depot refuse
  sinon. Controle des plans : zoom vers un cadre plus serre, dezoom vers un cadre plus large (cadre lu dans `still`),
  un seul mouvement vif, temps plat signale. Page : le decoupage est ecrit sur chaque tuile ; tuile plus compacte
  (image a gauche, verdict dessous). Essais sur p0004 (montages hors projet, planches d'images relues). Aucune depense GPU.
- 15/11, menage demande par le proprietaire : projets p0001, p0002 et p0003 supprimes (dossiers, dossiers de calcul
  `work/p000Xr*`, depots de plans qui les visaient), chaine en pause arretee. Reste p0004, projet d'essai tous publics.
  Gardes : le releve des depenses, la page Test, la Bibliotheque et les fiches de personnage.
- 15/11, une video, un fichier. Le scenariste fournit tout : modele de plans `2026-11-15e`, les quatre temps dans le
  meme fichier (chaque plan dit son `temps`, 30 plans au plus, 10 par temps). Plus de bouton « Importer » : la page
  importe toute seule un fichier accepte, nouveau ou modifie, hors calcul en cours ; un fichier refuse n'ouvre rien et
  reste affiche avec sa raison. Un plan retire du fichier quitte le projet ; l'image est gardee tant que `still` n'a
  pas change. La page refuse d'enregistrer par-dessus un projet que le depot vient de mettre a jour (elle se recharge).
  L'ancienne forme (un fichier par temps) reste lue, avec son bouton. Essais sur une copie des donnees : fichier
  entier accepte, cinq refus, import, redepot. Aucune depense GPU.
- 15/11, noms de production audiovisuelle, a la demande du proprietaire. Atelier devient Production (etapes
  Preparation, Decoupage, Tournage, Montage), Personnages devient Casting, Hub devient Materiel, Test devient Essais,
  Tri devient Rushes, Reseaux devient Diffusion ; un fichier du scenariste est un script, une fiche de personnage
  livree est une fiche de casting. Seuls les intitules changent : adresses, dossiers et champs des fichiers restent.
  Table dans `docs/agents.md` (Vocabulaire) ; consignes du scenariste et du directeur de casting mises a jour.
- 15/11, retour de tournage pour le scenariste : `verifier.py --retour` (une ligne par script importe) et
  `--retour <script>` (par scene : images faites, scene refaite ou non, image retenue, clip, note, points douteux,
  cases du proprietaire ; valeurs fermees et nombres seulement). Ancien formulaire en trois temps retire (`/nouveau`,
  `form.html`, `/api/job`) : tout script passe par la Production. Aucune depense GPU.
- 15/11, garde-robe qui grandit : modele de plans `2026-11-15f`, bloc `atelier.garder` (tenues et lieux nouveaux nes
  de la discussion avec le scenariste). La page les propose au proprietaire une fois une image retenue ; un appui les
  ajoute a la fiche du personnage, sans redeposer la fiche. Le scenariste ne touche pas a la fiche. Aucune depense GPU.
- 15/11, garde-robe, suite : le scenariste n'a plus rien a declarer. La page repere d'office la tenue et le lieu de la
  continuite absents de la fiche ; le proprietaire donne le nom francais dans une case et ajoute, ou ecarte.
  `atelier.garder` reste lu (nom francais souffle, tenue hors continuite). Aucune depense GPU.
- 15/11, fiche de Lea : « pas d'autre personne a l'image » retire de la case Limites (contredisait le champ `autres` des
  plans) ; decision du proprietaire. Les limites du profil public (`persona/bible.yaml`) sont inchangees.
- 15/11, profil public de Lea : « contenu avec d'autres personnes » retire de la liste de ses refus (`persona/bible.yaml`,
  `profile_texts.md`, `profile_texts_en.md`) ; decision du proprietaire. Un profil deja publie est a corriger a la main.
- 15/11, LoRA par defaut posees a la demande du proprietaire, d'apres son choix sur p0005 : style (realisme, cadrage)
  aux quatre temps, mouvement au temps 1, nu au temps 3, porno image et clip au temps 4. Aucune depense GPU.
- 15/11, p0005 temps 1 (chaine du proprietaire, images) : scenes 2 et 3 refusees par le controleur apres deux relances
  (pose et cadrage). Trois essais sur ces deux scenes : ni la LoRA de pose, ni la phrase de cadrage de la fiche, ni la
  force de la LoRA du visage (1,4, 1,0, 0,8), ni la LoRA de realisme ne changent l'image ; a 0,8 les tatouages
  disparaissent. Seule la redaction change tout : angle, jambes, tete et regard ecrits en tete, gros plan ecrit
  « extreme close-up portrait, her face fills the frame ». Regle ajoutee au SKILL du scenariste. Dans la page, les
  LoRA du projet et du temps se coupent d'un toucher sur une scene (`nom:0`). Depense GPU du jour : 2,96 $ sur 7,50 $
  (chaine 0,45 $ environ, essais 0,60 $ environ).
- 15/11, p0005 temps 1 : scenes 2 et 3 reecrites avec les deux textes reussis de l'essai et passees en « libre » (accord du
  proprietaire), images relancees (series r11 a r15). A l'oeil les prises sont bonnes ; le controleur note 8 une prise de la
  scene 2 et refuse toutes celles du gros plan (il y cherche le decor et la tenue entiere) : a corriger. Depense GPU du
  jour : 3,38 $ sur 7,50 $.

## 2026-11-15 (suite) : modele `2026-11-15g` deploye, video figee corrigee

- Deploye apres la fin de la chaine de p0005 : pose obligatoire (cadrage, angle, position, regard), point de vue de la
  fiche omis quand la scene dit son angle, gros plan sans la tenue entiere ni le decor au controle, note calculee du
  controleur (une scene qui atteint 7 n'est plus refaite), points de pose manques redits en tete a la relance.
  Reste a prouver sur GPU : la note d'un gros plan avec la nouvelle description, le renfort a la relance.
- Video finale de p0005 figee vers 5 s sur telephone, meme telechargee : des segments du montage sortaient en 4:4:4
  (profil High 4:4:4, illisible par les telephones) et etaient colles tels quels apres le premier. Corrige : tous les
  segments en `yuv420p`. Temps 1 remonte (`final_v2.mp4`, verifie : un seul profil, High).
### 2026-11-15 (suite) : essai comparatif texte / retouche / pose imposee (hors projet)

- Trois scenes tous publics de Lea (assise en tailleur de trois quarts ; a genoux de profil roulant un tapis ; tres gros
  plan du visage), chacune faite de trois facons a partir d'une meme image de depart. Images dans
  data/work/girls-ai-essai-comparatif, planches p0004essai_comparatif_s1/s2/s3 dans le Tri.
- Texte seul (Z-Image + LoRA du personnage, assemblage du modele g) : visage fidele, mais pose et cadrage faux sur les
  deux scenes de corps (vue de dos au lieu de trois quarts, plan moyen au lieu de large), coiffure ignoree. Gros plan juste.
- Retouche de l'image de depart (Qwen-Image-Edit) : pose, cadrage, coiffure et piece justes ; visage plus lisse, moins
  ressemblant, tatouage reduit ; pas de LoRA possible.
- Pose imposee : squelette tire de l'image retouchee (torchvision keypointrcnn, dessine au format OpenPose, rien
  d'installe), puis Z-Image + LoRA + ControlNet (`ModelPatchLoader` + `ZImageFunControlnet`, force 0,9, 9 pas). Pose et
  cadrage justes ET visage fidele ; la pose tient avec un autre lieu et une autre tenue. La piece n'est pas reprise de
  l'image de depart (redessinee d'apres le texte). 9 s par image une fois charge.
- Ajoute au volume `lea-models` (dossier `models/model_patches`, rien supprime) :
  `Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors` (6,7 Go, celui qui a servi) et
  `Z-Image-Turbo-Fun-Controlnet-Union.safetensors` (3,1 Go, repli non essaye, supprimable).
- Depense : reconnaissance 1,8 min + essai 12,6 min a 0,72 $/h, environ 0,17 $. Jour : 3,83 $ sur 7,50.

### 2026-11-15 (suite) : pose imposee branchee, import d'un script reecrit, fumee

- **Import d'un script reecrit** (`9072f39`) : une scene deja faite garde sa prise retenue, son tirage et sa coupe meme
  si son texte change ; rien n'est refait sans demande, le nouveau texte sert a la prochaine prise.
- **Fumee dans un clip** (`9755cd8`) : fumee apparue derriere une vitre sombre (temps 1 de p0005, scene 2). Fumee,
  brume et vapeur ajoutees aux choses interdites des clips (`negative_clip`). Non prouve sur GPU ; le clip existant
  n'est pas refait sans demande.
- **Pose imposee dans la chaine**. Le pilote, pour un plan qui porte `squelette` : image neutre du personnage (gardee
  dans `data/work/girls-ai-neutre-*.png`), brouillon de la scene par retouche, squelette par les noeuds integres de
  ComfyUI (`SDPoseKeypointExtractor`, `SDPoseDrawKeypoints`, aucun outil installe), puis image creee sur le squelette
  (`ZImageFunControlnet`, force 0,9). Un brouillon par scene, commun a ses variantes ; squelette vide ou fichier
  absent : image d'apres le texte seul. La Production pose le champ ; le scenariste n'a rien a changer.
  Tirage d'un temps : troisieme valeur `pose`. Temps 1 et 2 : toute image creee a part l'utilise (sauf `direct`) ;
  temps 3 et 4 : seulement si le proprietaire choisit `pose` (non verifiable par l'assistant).
  Jamais sur un gros plan ni une scene a plusieurs.
- Fichier ajoute au volume : `models/checkpoints/sdpose_wholebody_fp16.safetensors` (1,9 Go).
- Essais (tous publics, hors projet) : chaine complete sur 4 poses de yoga (pod de 19 min, environ 0,23 $), puis le
  pilote modifie sur 2 scenes en 2 variantes et 1 gros plan (6 min 30, environ 0,10 $). Poses tenues dans les deux.
  Limites vues : la coiffure ecrite est parfois ignoree ; quand le brouillon montre la personne petite dans un coin,
  l'image finale la recadre plus grande. Surcout constate : environ 0,05 $ par lancement plus 0,006 $ par scene.
  Planche : `data/inbox/p0004essai_pose_imposee.png`.
- Meme jour, a la demande du proprietaire : la pose imposee devient le tirage par defaut des temps 3 et 4 ; p0004 et
  p0005 (qui portaient l'ancien defaut `direct` enregistre) passes a `pose` sur ces deux temps. Les images deja
  retenues ne sont pas refaites. Non verifiable par l'assistant sur ces temps : le proprietaire juge.

### 2026-11-15 (suite) : plan B, lieux et tenues tenus par des images (recherche et essai, hors projet)

But du proprietaire : le contenu des temps 3 et 4. Decision : Z-Image, ses LoRA et la pose imposee y restent ; les
modeles de retouche ne servent qu'a preparer (brouillon, tenue, lieu). Rien n'est branche dans la Production.

- **Recherche** (recherche web puis Perplexity ; la recherche profonde a expire, remplacee par trois questions).
  Qwen-Image-Edit 2511 (licence libre, trois images de reference, visage mieux tenu) : meilleur choix libre, a la
  place du 2509 (environ 20 Go de plus sur le volume, non fait). Ecartes : Qwen-Image 2.1 et FLUX.2 klein 9B (usage
  commercial interdit), Z-Image-Edit (non publie), FLUX.2 klein 4B (inegal a plusieurs images). Un lieu n'est jamais
  garanti identique par la retouche seule : toujours repartir de la photo d'origine. LoRA du corps : 20 a 40 images,
  10 a 20 % en pied, fonds et tenues varies et nommes dans les legendes.
- **Pistes retenues**. Lieu : une photo de reference ; le brouillon de la pose est fabrique dans ce lieu, puis
  l'image finale part de ce brouillon. Tenue : image a plat sur fond blanc, posee dans le brouillon ; l'etat (ouverte,
  glissee) dit par le texte ; un vetement retire est d'abord place comme objet dans la photo du lieu. LoRA d'une
  tenue : deux ou trois tenues fetiches au plus. Plus tard : maquette 3D du lieu.
- **Essai** (tous publics, script `cn/planb.py` du dossier de travail, images dans
  `data/work/girls-ai-essai-planb`, planches `data/inbox/p0004essai_planb_*.png`). Une chambre et une tenue (gilet
  jaune, jupe verte) creees une fois, puis quatre scenes (assise, debout, a genoux, au sol avec le gilet retire pose
  sur la chaise). Brouillon par retouche a trois images (personnage, tenue, lieu), squelette, puis image finale
  Z-Image + LoRA du personnage + pose imposee, de six facons :
  1. texte seul (chaine actuelle) : la piece est reinventee a chaque scene (lit, miroir, angle differents) ;
  2. image de depart, force 0,6 (`VAEEncode` du brouillon, `denoise` 0,6) : piece, tenue et pose du brouillon gardees
     sur les 4 scenes, visage du personnage ;
  3. image de depart 0,8 : la piece derive deja (miroir deplace, moulure, tapis apparu) ;
  4. decor gele 1,0 (`SetLatentNoiseMask` sur la zone du personnage, recollage `ImageCompositeMasked`) : piece
     identique au pixel, mais 2 echecs sur 4 (personnage geant hors d'echelle, telephone invente dans la main) ;
  5. decor gele 0,8 : piece identique au pixel, 4 reussites sur 4, visage du personnage ;
  6. decor gele par le module de pose (`inpaint_image`, `mask`) : 3 sur 4 (telephone invente une fois).
  Tenue : couleurs, maille et boutons tenus partout ; « ouverte » et « retiree, posee sur la chaise » reussis ;
  « glissee de l'epaule » non obtenu (le brouillon la montre simplement ouverte). Le brouillon ne suit pas toujours
  la pose ecrite (scene 4 : assise de cote au lieu de genoux releves), et l'image finale suit le brouillon.
  La zone refaite (squelette de 10 px, maximum du noeud, elargi de 56 px) a suffi.
- **Conclusion**. Decor gele a 0,8 pour une piece strictement fixe, image de depart a 0,6 comme variante plus simple.
  Limite a faire juger par le proprietaire aux temps 3 et 4 : a 0,6 ou 0,8 l'image finale garde beaucoup du
  brouillon, donc aussi ses vetements ; un etat de tenue absent du brouillon risque de ne pas apparaitre.
- Depense : pod de 13,6 min, environ 0,20 $ ; total du jour 4,32 $ sur 7,50. Disque : 32 Go sur 197.

## 2026-11-15 (fin) : atelier du personnage, essai complet sur Lea

- **Outil**. Page `/atelier#/atelier/<personnage>` : Lieux, Garde-robe, Corps (planches), LoRA. Lieux et tenues
  crees par description ; ceux de la fiche de Lea sont repris sans rien reconstruire. Dans la Production, tirage
  « lieu et tenue de la bibliotheque » avec choix du lieu et de la tenue a chacun des quatre temps.
- **Lieux** : 7 lignes, 14 images (5 s par image). 3 images montraient une personne (lignes avec « her ») : les
  mentions du personnage sont retirees de la description, images refaites, plus personne. Formule « annonce
  immobiliere » ecartee (pieces nues, un bandeau de texte).
- **Tenues** : 7 lignes, 2 images chacune, vetements a plat sur fond blanc, tres bons.
- **Tirage sur p0004** (temps 1, cuisine + pull) : pull tenu ; cuisine identique entre les 3 images d'une scene,
  de la meme famille mais rearrangee d'une scene a l'autre. Controle : 2 scenes notees, aucune a refaire.
- **Planches** : 12 images habillees (cadrages, fonds et tenues varies), legendes enregistrees, toutes gardees.
- **Entrainement de preuve** : `girls-ai-lea-v1`, 12 planches, 8 passages (96 pas), 7 min sur une 5090, 0,19 $, pod
  supprime ; 6 images d'essai aux forces 1,0 / 1,3 / 1,6. LoRA faible (trop peu de passages) : preuve de la chaine,
  non adoptee. Un fichier de ce nom ajoute sur le volume RunPod.
- Reste : la mesure de place du volume affichee par l'entrainement est fausse (« 396536 Go ») ; planches nues,
  sous-vetements portes et temps 3-4 : lances et juges par le proprietaire.
- Depense de l'ensemble : environ 0,65 $ ; total du jour 4,98 $ sur 7,50. Disque : 32 Go sur 197.

## 2026-11-15 (soir) : cabine d'essayage, import par photo, comparaison des methodes

- **Cabine** (atelier du personnage, onglet Cabine) : tenue de la garde-robe portee par elle, fond neutre ou lieu,
  cinq poses. Essai : pull creme, fond neutre, debout de face, 3 images en 3,8 min ; pull fidele, visage tenu.
  Limites : l'image neutre est cadree aux cuisses ; un haut seul garde le jean de l'image neutre.
- **Import par photo** : photo d'un lieu = son image ; photo d'un vetement = vetement a plat sur fond blanc. Essai
  avec une planche d'elle en ensemble de sport : brassiere et legging a plat, fideles, 2 images en 27 s.
- **Comparaison des methodes** (page `#/cmp/<projet>`) : memes scenes, memes tirages, pose imposee seule puis lieu et
  tenue de la bibliotheque ; images a part du projet. p0004, scenes 1 et 4, 3 images chacune : nouvelle methode =
  cuisine identique entre les images d'une scene et pull tenu, mais les 3 images sont presque des copies, elle est
  plus petite dans le cadre et la cuisine change encore d'une scene a l'autre ; methode actuelle = images plus variees
  et plus nettes, cuisine reinventee a chaque image. Planches : `data/inbox/p0004essai_methodes_ancienne_nouvelle.png`,
  `p0004essai_cabine_pull.png`, `p0004essai_import_photo.png`.
- **p0005** : comparables 1 scene sur 3 au temps 1 (deux scenes libres), 4 sur 5 au temps 2, 6 sur 6 au temps 3, 0 sur
  7 au temps 4 (une autre personne a l'image partout : la methode ne pose qu'elle). Temps 1 lance par l'assistant
  (6 images, non regardees) ; temps 2 et 3 a lancer par le proprietaire depuis la page.
- Depense : environ 0,50 $ ; total du jour 5,45 $ sur 7,50 environ. Disque : 32 Go sur 197.

### 2026-11-15 (soir, suite) : comparaison, scenes a deux

- Page de comparaison : rappel de ce que le scenariste a ecrit sous chaque scene ; moments et scenes choisis par de gros boutons.
- p0005 moment 1 : 6 images, aucun echec (non regardees).
- Scenes a deux (moment 4) : la nouvelle methode part de la photo du lieu, sans brouillon. Essai sur p0004 (scene 4 avec un homme ajoute le temps de l'essai, 8 images) : a 0,8 la piece tient, personnes petites et basses ; a 0,9 cadrage meilleur, piece changee. Reglage au choix dans la page.
- Depense : environ 0,30 $ ; total du jour environ 5,80 $.

## 2026-11-15 (soir, fin) : comparaison sur six poses, plafond a 20 $

- Plafond GPU du jour porte a 20 $ a la demande du proprietaire (`persona/production.yaml`), pour les essais de l'atelier.
- Essai p0004 (tous publics), 6 poses, 2 images par methode, 24 images, 0 echec : cuisine + pull (en pied, assise de profil, de dos), studio de pilates + ensemble de sport (en tailleur, a plat ventre, a genoux bras leves). Planches : `data/inbox/p0004essai_comparaison_cuisine.png` et `_studio.png`.
- Constat : la pose est tenue par les deux methodes. Nouvelle methode : la piece est la meme d'une image a l'autre (studio : 6 sur 6 ; cuisine : meme piece, angle qui varie), mais le personnage est petit dans le cadre (plan large impose par la photo du lieu), le visage perd en detail, et un vetement non demande apparait (jean sous le pull, la ou l'ancienne laisse les jambes nues) ; le tapis change de couleur. Ancienne methode : cadrage serre et flatteur, piece reinventee a chaque image.
- Avis : garder l'ancienne par defaut ; la nouvelle pour les plans larges ou la piece doit etre reconnue. A faire pour la rendre utile en plan serre : photos du lieu de plus pres (ou recadrage de la photo autour du personnage).
- Depense : environ 0,35 $ ; total du jour 6,15 $ sur 20.
- Demande notee : file d'attente des calculs (enchainer sur un meme pod).

## 2026-11-15 (nuit) : file d'attente, finition, page Schemas

- File d'attente des calculs : faite et en ligne ; affichee en haut de la Production, sur la ligne de la depense (elle vaut pour tous les projets). Prouvee sur p0004 (un lancement mis en file est parti seul a la fin du precedent, sur le meme pod).
- Finition (seconde passe en 1088 x 1920) : essai p0004, memes tirages avec et sans, 6 images. Meme image, visage et mains nettement plus detailles ; environ 8 secondes de plus par image ; petits details inventes possibles. Activee (`finition: true`). Planche `data/inbox/p0004essai_finition.png`.
- Page Schemas (`#/schemas`) : arbre de decision de la fabrication des images ; video et son a venir.
- Avis donne sur l'arbre : manquent le controle du brouillon avant les trois images, une reprise ciblee du visage, une relance qui redit tout ce qui a manque (pas seulement la pose). En attente de l'accord du proprietaire.
- Depense : environ 0,30 $ ; total du jour 6,44 $ sur 20.

## 2026-11-15 (nuit, suite) : essai des trois chantiers, nettoyage de p0005

- Essai sur p0004 (3 scenes en pose imposee, 3 variantes, tous publics) : brouillons relus avant les images (2 sur 3
  a refaire ; 1 refait garde, 1 refait pas meilleur donc premier garde), 9 images notees 8 ou 9, aucune relance,
  6 visages petits repris (6 s chacun, sans raccord visible ; gain net mais modeste apres la finition).
  Planche : `data/inbox/p0004essai_visage_avant_apres.png`. Duree 23 min, environ 0,60 $ (dont controle 0,33 $).
- Defaut constate : chaque relecture du controleur relance son script (environ 3 min) et l'essai a retenu la file
  23 min alors que le proprietaire y avait 6 series de planches. A faire : garder le controleur charge entre deux
  relectures ; ne lancer un essai que file vide.
- p0005 nettoye a la demande du proprietaire : images, clips, montages, planches de comparaison, notes, verdicts et
  journaux deplaces dans `data/archives/girls-ai-p0005-20261115/` ; `projet.json.avant-nettoyage` garde. Son script
  date d'avant le modele `2026-11-15g` (aucun champ de pose) : a redeposer par le scenariste.
- Scenariste : les champs de pose facultatifs (appui, bassin, genoux, mains) sont a remplir pour les poses difficiles.
- Decide avec le proprietaire, a faire au debut du chantier video : le rendu (« filme a la main » ou « camera
  posee ») se choisit une fois par video, propose par le script (champ `rendu`), modifiable dans la page ; la phrase
  ajoutee aux clips et le reglage du montage suivent ce choix. Ordre des chantiers : videos et leur qualite, son,
  voix, synchro des levres.
- Depense du jour : 7,50 $ sur 20.

## 2026-11-15 (fin de soiree) : rendu par video, planches

- Rendu de la video (modele `2026-11-15h`) mis en ligne apres la fin des planches du proprietaire : `rendu: main` ou `pose` propose par le script, clips en camera posee quand le rendu n'est pas « main ». Non essaye a l'image.
- Planches : « wearing » retire cote serveur devant un etat sans vetement ; bouton « Supprimer la serie » ; « Tout garder / Tout ecarter » visibles aussitot ; file d'attente sur une ligne qui defile ; portrait de depart annonce « sans objet » quand le personnage a une LoRA.
- Verification des 8 dernieres series du proprietaire (fiches et journaux seulement) : LoRA du personnage et LoRA en plus appliquees partout, force 0,6, aucune erreur. Aucune depense de ma part.

## 2026-11-16 (nuit) : voie selon le cadrage, controleur garde charge, images d'origine

- Tirage `auto` d'un temps (« Choisies selon le cadrage de chaque scene ») : plan large = lieu et tenue de la bibliotheque, plan moyen = pose imposee, gros plan = texte seul ; champ `voie` d'une scene pour forcer. En service a 01 h 37, defauts du proprietaire inchanges. Verifie hors ligne seulement (pas encore a l'image).
- Controleur garde charge entre deux relectures : essai sur 7 images de p0004 en trois lots, 282 s puis 23 s puis 7 s. Depense : 0,07 $.
- Images d'origine de Lea retrouvees sur le volume : 57 dans la sortie de ComfyUI (40 `set_*`, 17 `nm_*`) et le jeu exact de sa premiere LoRA (`lea_ds/images`, 47 images et leurs legendes). Tout est copie dans `server/data/girls-ai-origine/` ; les 47 sont rangees dans son atelier en serie 21 « planche initiale », aucune gardee d'office, 4 sans legende (lecture echouee). Rien supprime sur le volume. Depense : 0,02 $ (trois pods de moins d'une minute).
- Entrainement : 10 et 15 passages ajoutes au choix (la v2 a 30 passages sur 41 planches parait moins detaillee au proprietaire).
- 16/11, chantier continuite (`docs/chantier-continuite.md`), essai 1 « brouillons enchaines » : 5 scenes tous publics sur le canape de la bibliotheque de Lea, 22 images, pod de 17,9 min, 0,21 $. Planches : `data/inbox/p0004essai_chaine1_brouillons.jpg` et `p0004essai_chaine1_finales.jpg`. Resultat : enchainer les brouillons (chacun tire du precedent) ne marche pas : les couleurs foncent, la veste change de couleur, la pose de la scene d'avant colle (elle reste allongee quand elle doit s'asseoir). L'ancienne voie (image neutre + photo du lieu + etat dit par le texte) tient mieux l'etat des habits mais change la robe d'une scene a l'autre. Image finale : texte seul = piece et robe reinventees ; decor gele depuis le brouillon = piece et habits du brouillon, 3 sur 3 ; scene a deux par « image de depart » depuis le brouillon : bonne a 0,6, defaite a 0,7. Suite : reference fixe (la premiere image, tenue complete) + etat cumule ecrit, essai 2 lance.
