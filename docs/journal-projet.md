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

## Couts constates
- Volume : ~0,35 $/jour. Sessions de generation : 0,20 a 0,30 $ chacune.
- Entrainement du LoRA : ~3 $ (RTX 5090 a 1,39 $/h, ~2 h 15 installation comprise).
- Session du 13/11 apres-midi (controle qualite, tests de rendu, LoRA d'animation rate, tests du pilote) : ~2,30 $.
- Session type du pilote : 2 plans en 9 a 17 min, 0,10 a 0,20 $.

## Comptes (13/11/2026)
- Gmail `lea.morel.ai@gmail.com` (nom affiche Lea Morel).
- Instagram : suspendu a la creation, contestation a faire, ne pas recreer de compte tout de suite.
- TikTok : a creer depuis le telephone, un autre jour.
- Fanvue : Fully AI, NSFW ; verification d'identite envoyee, fiche Creator Personality complete,
  coordonnees bancaires renseignees ; en attente de validation du compte.

## Limites et points ouverts
- Rendu encore trop lisse ("studio") ; grain smartphone a travailler.
- Clips de 5 s sans son : montage et voix a construire.
- Le contenu explicite n'est pas produit par l'assistant : a piloter soi-meme dans ComfyUI.
- Generateur de textes de profil (`pipeline/profile_texts.py`) : produit aussi la fiche Fanvue complete
  (17 champs, FR + EN) et signale les manques de la bible. Requete verifiee avec --dry-run ; appel a
  l'API non teste (pas de cle Anthropic dans l'environnement de developpement).
- Tranche le 13/11 : la petite puce a l'oreille droite, visible sur les images de reference, est assumee
  (lobes perces). La fiche Fanvue "Mes modifications corporelles" ne la mentionne pas : a completer si souhaite.
- A faire : LoRA d'animation a valider, planification du pilote, branchement du controle qualite,
  montage et voix, contestation Instagram, compte TikTok, fin d'inscription Fanvue, publication.
