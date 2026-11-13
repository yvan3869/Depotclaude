# Architecture d'automatisation (serveur Oracle + RunPod)

Principe : le serveur Oracle, allume en permanence et sans GPU, orchestre tout.
RunPod n'est allume que le temps de generer, puis supprime.

## Composants sur le serveur Oracle
| Composant | Role | Outil |
|---|---|---|
| Planificateur | genere le plan de la semaine depuis `persona/bible.yaml` | `pipeline/plan_week.py` + cron |
| Pilote GPU | cree le pod, attend ComfyUI, envoie les workflows, rapatrie les fichiers, supprime le pod | script Python + API RunPod |
| Stockage | clips et images valides, archives | disque du serveur (ou Object Storage Oracle) |
| Tri | interface web, accessible depuis le telephone | `tools/triage/` derriere HTTPS + jeton |
| Montage | assemble 3 a 6 plans, sous-titres, voix | ffmpeg + TTS |
| Publication Fanvue | televerse medias, programme les posts | API officielle Fanvue (OAuth) |
| Publication sociale | shorts Instagram / TikTok avec label IA | outil de programmation ou manuel |
| Messages | brouillons et reponses aux abonnes | outils IA de Fanvue en priorite |
| Suivi | couts GPU, revenus, taux de rejet | petit tableau de bord |
| Proxy HTTPS | certificat, adresse fixe pour le retour OAuth | Caddy |

## Cycle hebdomadaire vise
1. Dimanche : le planificateur ecrit le plan de la semaine.
2. Lundi : le pilote lance un pod, genere images puis clips, rapatrie, supprime le pod.
3. Notification : "N clips a trier".
4. Tri humain sur telephone (10 minutes).
5. Montage automatique des clips gardes.
6. Programmation des publications de la semaine (Fanvue + shorts).
7. Rapport : cout, nombre de clips, revenus.

## Ce qui reste humain
- Le tri et la validation finale avant publication.
- Le contenu explicite (prompts et generation).
- La surveillance des messages sensibles et des demandes sur mesure.

## Garde-fous
- Plafond de depense GPU par semaine ; arret automatique du pod apres une duree maximale.
- Aucune cle dans le depot : fichier d'environnement sur le serveur, droits restreints.
- Journal de chaque action (pod cree/supprime, publication).

## Informations necessaires sur le serveur
A lancer sur le serveur, puis coller le resultat (aucun secret n'y figure) :
```bash
uname -m; cat /etc/os-release | head -2; nproc; free -h | head -2; df -h / | tail -1
docker --version 2>/dev/null; python3 --version; sudo ss -tlnp 2>/dev/null | awk 'NR>1{print $4, $6}' | head -20
```
Plus : un nom de domaine eventuel pointant vers le serveur, et les ports ouverts dans la
"Security List" Oracle (80 et 443 seront necessaires).
