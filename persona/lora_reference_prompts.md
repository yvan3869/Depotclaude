# Prompts de reference - LoRA Lea

Prompts en anglais (meilleurs resultats). Jeu de reference habille : le LoRA doit
apprendre l'identite, pas une tenue ni une pose. Objectif : 30 a 40 images retenues.

## Bloc identite (a coller au debut de chaque prompt)
```
realistic smartphone photo of a 27 year old woman, wavy shoulder-length auburn hair
with copper highlights, green almond-shaped eyes, full eyebrows, freckles across the
nose, slightly asymmetric smile, athletic toned
build with a full bust, thin gold chain with a small crescent moon pendant, fine-line
black peony tattoo from right collarbone to shoulder, natural light, visible skin
texture, no retouching
```

## Negatif
```
plastic skin, airbrushed, studio lighting, cgi, 3d render, doll, teenager, childlike,
extra fingers, deformed hands, text, watermark, perfectly symmetric face
```

## A. Casting (choisir le visage - 40 a 60 essais, seeds differents)
- `<identite>, front-facing head and shoulders portrait, neutral expression, plain white wall, soft window light`

## B. Angles (8 images)
- `front portrait, looking at camera`
- `three-quarter left`, `three-quarter right`
- `left profile`, `right profile`
- `slightly from above, looking up at camera`
- `slightly from below, chin raised`
- `over the shoulder, looking back`

## C. Expressions (8 images, cadrage buste)
- `soft closed-mouth smile`
- `laughing, eyes half closed`
- `biting lower lip, concentrated`
- `teasing look, one eyebrow raised`
- `sleepy, just woke up, messy hair`
- `surprised, lips parted`
- `serious, calm, coach face`
- `looking away then smiling`

## D. Cadrages et tenues (10 images)
- `full body, standing, sage green sports set, pilates studio, white walls, plants`
- `full body, on a reformer, terracotta sports set, mid movement`
- `medium shot, oversized cream sweater over a bralette, thick socks, sitting on wooden floor`
- `medium shot, oversized men's shirt, holding a coffee cup with both hands, kitchen`
- `medium shot, thin low-cut tank top, leaning toward the camera, apartment window light`
- `medium shot, wrap top, cafe table by the window`
- `full body, light summer dress, white sneakers, walking on a riverside quay`
- `medium shot, linen bathrobe, bathroom with green tiles`
- `hair in a messy bun, tying hair up with both arms raised, beige hair tie on left wrist`
- `high ponytail, stretching neck and shoulders, studio`

## E. Lumieres et decors (6 images)
- `golden hour through tall window, old Lyon apartment, parquet floor, unmade bed in background`
- `overcast daylight, street on a hillside, stone stairs`
- `warm lamp light at night, sofa, ginger cat beside her`
- `bright morning light, cluttered narrow kitchen`
- `soft diffused light, pilates studio mirror`
- `candlelight, antique bathtub in background`

## F. Tatouages (4 images de detail, pour les ancrer)
- `close-up of right collarbone and shoulder, fine-line black peony branch tattoo, gold chain`
- `close-up of neckline, tiny crescent moon tattoo on the sternum echoing the pendant`
- `side view, arm raised, sports bra, vertical fine-line lavender stem tattoo along right ribs`
- `close-up of right inner wrist, small cursive word tattoo, hand holding a cup`

## Controle avant entrainement
- [ ] meme visage sur toutes les images (yeux verts, taches de rousseur)
- [ ] tatouages au bon endroit et du bon cote (attention aux images en miroir)
- [ ] apparence clairement adulte partout
- [ ] varietes d'angles, de lumieres et de tenues ; aucun doublon
- [ ] aucune ressemblance avec une personne reelle identifiable
