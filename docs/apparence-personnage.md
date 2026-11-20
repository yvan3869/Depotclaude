# Apparence d'un personnage : les étapes

Procédé retenu le 19/11/2026, après l'échec de la tête « posée après coup » sur les planches nues de Luz
(aucune planche ressemblante sur 12). Principe : le visage s'apprend d'abord, seul ; tout le reste est ensuite
**dessiné en une fois** par Z-Image avec la LoRA du visage, les LoRA du propriétaire et le texte de la fiche.
Plus de retouche sur le corps.

Tout se passe dans l'atelier du personnage (Production, onglets Débuter, Corps, LoRA).

## Les étapes

| # | Étape | Avec quoi | Ce qu'on garde |
|---|-------|-----------|----------------|
| 1 | **Fiche** | quatre cases : identité, allure, visage, corps | le texte, redit à toutes les étapes |
| 2 | **Visage de référence** | fiche (identité + visage), 8 portraits tirés | 1 portrait |
| 3 | **Expressions** | le portrait, changé d'expression par retouche (visage seul, habillé) | 20 à 25 images où on la reconnaît |
| 4 | **LoRA du visage** | expressions gardées + portrait, 60 passages | une LoRA « visage », adoptée à la force qui ressemble |
| 5 | **Corps de référence** : face, dos, angles | LoRA du visage + LoRA de nu + fiche (identité, allure, corps) | 1 face, 1 dos, 1 tour d'angles |
| 6 | **Planches du corps** (nues) | LoRA du visage + LoRA de nu + fiche + traits du corps retenu | celles où visage et corps sont justes |
| 7 | **Planches habillées** | LoRA du visage + fiche + tenues de la garde-robe (LoRA de nu retirées) | idem |
| 8 | **Tri** | — | 20 à 40 images, dont 10 à 20 % en pied, plus les expressions et le portrait |
| 9 | **LoRA complète** (visage + corps) | toutes les images gardées, 30 passages | une LoRA « personnage », qui remplace celle du visage |
| 10 | **Vérification** | images d'essai habillées à trois forces, puis une série par le propriétaire | adoption, ou retour à la précédente |

Réglages des étapes 5 et 6 (personnage avec la LoRA du visage) : la force de sa LoRA se règle à part pour le corps de référence et pour chaque série ; les LoRA en plus ont chacune leur force ; une série reprend les réglages de la précédente ; « Peau refaite sans les LoRA en plus » redessine la peau par Z-Image seul après coup (visage gardé, coût doublé), à utiliser quand la LoRA de nu lisse la peau.

## Ce qui tient quoi

- **Le visage** : la LoRA du visage (étape 4), puis la LoRA complète (étape 9).
- **Le corps** : la case Corps de la fiche + les LoRA de nu du propriétaire + les **traits du corps retenu**.
  Z-Image ne lit pas d'image : les références de corps (étape 5) ne sont pas « montrées » au modèle. Elles servent
  à choisir un corps ; les traits tirés au sort de la face et du dos retenus sont ensuite réécrits dans le texte
  de chaque planche (fait automatiquement).
- **La peau** : dessinée par Z-Image, jamais retouchée. Mots de peau légers de près, appuyés de loin.

## Réponses aux « réappuis » de l'étape 9

- **Réappui de la LoRA du visage pendant l'entraînement : non.** On n'entraîne pas par-dessus une LoRA ; son apport
  est déjà dans les images du jeu (elles ont été dessinées avec elle), et les expressions et le portrait y restent.
  À l'usage, la LoRA complète **remplace** celle du visage : ne pas empiler les deux (visage durci).
- **Réappui de la LoRA de nu : pas à l'entraînement, oui à l'usage.** Elle reste dans les scènes des temps 3 et
  suivants, souvent à force plus basse puisque la LoRA complète connaît déjà son corps. À régler sur une série.
- **Réappui du texte de la fiche : oui, toujours.** Chaque légende du jeu commence par la fiche ; la LoRA est
  donc liée à ces mots, et les scènes doivent continuer à les dire (c'est déjà le cas).

## Points d'attention

- Étape 3 : ne garder que les expressions vraiment ressemblantes. C'est le seul jeu de la LoRA du visage ;
  une image douteuse gardée se paie sur toute la suite.
- Étape 4 : juger sur les essais en plan moyen **et** en pied. Trop faible : elle ne ressemble pas de loin ;
  trop forte : visage figé, cadrage tiré vers le gros plan.
- Étapes 5 et 6 : trois LoRA empilées (visage, nu, style) peuvent abîmer le visage. Baisser d'abord la LoRA
  de nu, pas celle du visage.
- Étape 8 : la LoRA complète apprend des images déjà générées. Toute dérive gardée (visage approximatif,
  peau trop lisse, mains ratées) est apprise : tri sévère.
- Vues de dos : le visage n'y est pas ; ce sont les cheveux qui comptent.
- Ce qui a été écarté : planche faite par retouche puis finie (peau colorée et marquée), tête posée par
  retouche sur un corps dessiné (visage perdu en nu avec LoRA).

## Qui fait quoi

L'assistant fournit l'outil et prouve en habillé. Les séries nues, le choix des LoRA pour adultes et le
jugement des images sont l'affaire du propriétaire.
