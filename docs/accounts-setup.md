# Comptes et acces

Regle generale : ne jamais partager de mot de passe (ni dans le chat, ni dans un
fichier, ni dans ce depot). Les acces passent par des cles API ou OAuth, revocables.

## Ordre conseille (du moins cher au plus engageant)
1. Adresse e-mail dediee au projet + reservation du pseudo partout (`lea.morel.ai` ou proche).
2. Fanvue (c'est le seul compte qui rapporte) :
   - Inscription createur, verification d'identite (piece + selfie). Ton identite
     n'apparait pas sur le profil.
   - Type de compte : "Fully AI". Choisir NSFW a l'inscription (condition d'acces a
     AI Messaging).
   - Remplir "Creator Personality" a partir de `persona/bible.yaml` : c'est ce qui
     donne sa voix aux messages automatiques.
   - Activer : message de bienvenue automatique, AI Messaging ; demander l'acces au
     AI Chatbot (beta, sur selection).
   - Bio : rien qui suggere une personne reelle. Le tag IA du profil vaut divulgation.
3. Instagram (compte professionnel "createur") et TikTok :
   - Activer le label "contenu genere par IA" sur chaque publication.
   - Pas de lien direct vers Fanvue dans les posts ; un lien en bio via une page
     intermediaire. Contenu suggestif mais sans nudite, sinon restriction de portee ou ban.
4. Statut fiscal : revenus a declarer (micro-entreprise en general) ; a confirmer avec
   un comptable avant le premier versement.

## Acces a donner a l'outil d'automatisation
| Service | Mecanisme | Ou le creer |
|---|---|---|
| RunPod | cle API (droits limites aux pods si possible) | Settings > API Keys |
| Fanvue | application OAuth "API only" ; scopes `write:media`, `write:post`, `read:chat`, `write:chat`, `read:insights` | fanvue.com/dev |
| Instagram / TikTok | outil de programmation (Metricool, Buffer) et sa cle API | compte de l'outil |
| Claude (planification) | cle API Anthropic | console.anthropic.com |

Notes :
- Fanvue n'a pas de cle API : tu autorises l'application une fois dans ton navigateur
  (OAuth), l'outil conserve un jeton de renouvellement. Revocable a tout moment.
- Les API de publication directe d'Instagram et de TikTok exigent une validation
  d'application longue ; un outil de programmation evite cette etape. Au debut,
  publier a la main coute zero et suffit pour 3 a 5 shorts par semaine.
- Scripts non officiels, extensions de navigateur et partage de mot de passe sont
  interdits par les conditions de Fanvue : uniquement l'API officielle et ses outils integres.

## Regles Fanvue verifiees (sources officielles, oct.-nov. 2026)
- Les comptes entierement IA sont une categorie reconnue ; seule ta verification
  d'identite est requise. Jusqu'a 15 comptes IA par identite.
- Divulgation obligatoire ; ne jamais dire a un fan que le personnage est reel, y
  compris en message. Si un fan demande "es-tu une IA ?", repondre oui clairement.
- Personnage d'apparence clairement adulte ; aucune ressemblance avec une personne reelle.
- Contenu adulte autorise s'il est marque 18+ et conforme aux Community Guidelines.
- Messages IA autorises via les outils Fanvue ou une application passant par l'API :
  tu dois pouvoir relire, suspendre et couper la messagerie IA ; tu restes responsable
  de tout ce qui part du compte.
- Sanctions possibles : retrait, gel des versements, deduction de gains, fermeture.
Sources : help.fanvue.com (AI content on Fanvue, AI labels and disclosure, AI tools,
Verifying your AI account), legal.fanvue.com (Community Guidelines section D, API
policy 4.3), api.fanvue.com/docs. A relire avant le lancement.
