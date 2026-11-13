# Eirik : prompts et reglages des images retenues (13/11/2026)

Chaine : 1) image maitresse brute (Arthemy Comics Illustrious v8.0 + LoRA 2.5D Cel Shading a 0,4) ; 2) correction par edition ; 3) vues derivees de l'image corrigee.
Edition : Qwen-Image-Edit 2509 + LoRA Lightning 8 pas, CFG 1, euler / simple, shift 3.

## 0a_maitresse_brute.png
- Modele : ArthemyComics-Illustrious_v80.safetensors, LoRA cel_rendering_25d.safetensors poids 0,4
- Seed 5402, 832x1216, 28 pas, CFG 5.5, euler_ancestral/normal, clip skip 2
- Prompt :
```
masterpiece, western comics (style), 3d, toon shading, cel shading, (thick black outlines:1.3), (bold lineart:1.2), outline, flat color, solo, 1man, mature male, 36 years old, adult human man, exile, handsome man in his thirties, attractive rugged face, realistic facial features, strong jaw, weary guarded gaze, serious, closed mouth, smooth skin, realistic proportions, broad shoulders, muscular adult body, ash blond hair, undercut, shaved sides, short hair on top swept back, short trimmed blond beard, one dark snake tattoo on the side of neck, thick golden bronze torc bracelets on both wrists, brown bear fur coat on shoulders, dark brown linen tunic with open collar, covered chest, rolled sleeves, dark leather trousers, thick braided rope belt, braided fishing net sash across chest, sweat, shiny skin, (soot smudges on arms:1.2), dirty hands, stained clothes, clean face, upper body, three-quarter view, head turned, looking away, indoors, night, dark wooden viking longhouse, hearth fire in background, flames, firelight, damp dark wood walls, warm brown and ochre tones, dim lighting, soot, grime
```
- Negatif :
```
anime, manga, big eyes, big head, chibi, hatching, linear hatching, crosshatching, sketch, photorealistic, realistic, photo, loli, child, teenager, young, youthful, low quality, worst quality, nude, nipples, looking at viewer, scar, animal ears, furry, old, wrinkles, aged, caricature, pointy chin, long face, exaggerated expression, lamp, window, daylight, silver, silver jewelry, steel, smirk, grin, text, watermark, signature, multiple views, smoke, facial tattoo, forehead tattoo, facepaint, long beard, braid, ponytail, long hair, arm tattoo, chest tattoo, full sleeve tattoo, shirtless, bare chest, topless male, snake, animal, smile, 1girl, breasts, purple hair, grey hair
```

## 0b_maitresse_corrigee.png
- Image de reference : eirik_m_5402
- Seed 51, 832x1216
- Prompt :
```
Keep exactly the same image, same man, same pose, same face, same art style. Make only these changes: 1) add a braided fishing net sash worn across his chest over the tunic, from one shoulder to the opposite hip. 2) make the dark snake tattoo on the side of his neck clearer: a simple snake shape rising from the collar to below the ear. His hair and beard stay the same ash blond.
```

## vue1_portrait_face.png
- Image de reference : eirik_fix_51
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult man in his mid-thirties, same face, same ash blond hair with shaved sides, same short blond beard, same dark snake tattoo on the side of his neck, same thick bronze torc bracelets on both wrists, same soot stains. He wears the same dark brown linen tunic with laced open collar and rolled sleeves, the fishing net sash across his chest, the braided rope belt and dark leather trousers, with the brown bear fur coat on his shoulders. Change the camera angle: he now faces the camera directly, shoulders square to the camera, symmetrical front view, head and shoulders close-up portrait, neutral calm expression, eyes looking past the viewer. Background: inside a dark wooden viking longhouse at night lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke anywhere in the picture.
```

## vue2a_trois_quarts.png
- Image de reference : eirik_fix_51
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult man in his mid-thirties, same face, same ash blond hair with shaved sides, same short blond beard, same dark snake tattoo on the side of his neck, same thick bronze torc bracelets on both wrists, same soot stains. He wears the same dark brown linen tunic with laced open collar and rolled sleeves, the fishing net sash across his chest, the braided rope belt and dark leather trousers, with the brown bear fur coat on his shoulders. Change the camera angle: upper body in three-quarter view turned toward the right side of the picture, looking to the right, a weary guarded expression. Background: inside a dark wooden viking longhouse at night lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke anywhere in the picture.
```

## vue2b_profil.png
- Image de reference : eirik_fix_51
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult man in his mid-thirties, same face, same ash blond hair with shaved sides, same short blond beard, same dark snake tattoo on the side of his neck, same thick bronze torc bracelets on both wrists, same soot stains. He wears the same dark brown linen tunic with laced open collar and rolled sleeves, the fishing net sash across his chest, the braided rope belt and dark leather trousers, with the brown bear fur coat on his shoulders. Change the camera angle: rotate the camera 90 degrees to show his strict side profile, nose pointing to the left edge of the picture, only one eye visible, upper body, neutral expression. Background: inside a dark wooden viking longhouse at night lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke anywhere in the picture.
```

## vue3a_plein_pied_hiver.png
- Image de reference : eirik_fix_51
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult man in his mid-thirties, same face, same ash blond hair with shaved sides, same short blond beard, same dark snake tattoo on the side of his neck, same thick bronze torc bracelets on both wrists, same soot stains. He wears the same heavy brown bear fur coat closed over the dark brown tunic, the fishing net sash, the braided rope belt, dark leather trousers and fur-lined boots. Full body view from head to feet, standing with arms crossed, looking away to the side. Background: on a wooden palisade facing a frozen fjord, snow, overcast sky, cold desaturated blue-grey palette, dirty trampled snow and wet wood. No smoke.
```

## vue3b_plein_pied_interieur.png
- Image de reference : eirik_fix_51
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult man in his mid-thirties, same face, same ash blond hair with shaved sides, same short blond beard, same dark snake tattoo on the side of his neck, same thick bronze torc bracelets on both wrists, same soot stains. He wears the same dark brown linen tunic with laced open collar and rolled sleeves, the fishing net sash across his chest, the braided rope belt and dark leather trousers, with the brown bear fur coat on his shoulders. He also wears leather boots. Full body view from head to feet, standing with one hand on the hip, looking away to the side. The wooden floor is worn and dirty. Background: inside a dark wooden viking longhouse at night lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke anywhere in the picture.
```

## vue4a_grande_salle.png
- Image de reference : eirik_fix_51
- Seed 11, 1216x832
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult man in his mid-thirties, same face, same ash blond hair with shaved sides, same short blond beard, same dark snake tattoo on the side of his neck, same thick bronze torc bracelets on both wrists, same soot stains. He wears the same dark brown linen tunic with laced open collar and rolled sleeves, the fishing net sash across his chest, the braided rope belt and dark leather trousers, with the brown bear fur coat on his shoulders. Change the pose and framing: wide shot of the great hall, he sits on a bench by the hearth mending a fishing net with his hands, his eyes looking down at the net, seen from the side in three-quarter view, calm expression. Background: inside a dark wooden viking longhouse at night lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke anywhere in the picture.
```

## vue4b_palissade.png
- Image de reference : eirik_fix_51
- Seed 11, 1216x832
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult man in his mid-thirties, same face, same ash blond hair with shaved sides, same short blond beard, same dark snake tattoo on the side of his neck, same thick bronze torc bracelets on both wrists, same soot stains. He wears the same heavy brown bear fur coat closed over the dark brown tunic, the fishing net sash, the braided rope belt, dark leather trousers and fur-lined boots. Medium wide shot: he stands on the palisade walkway with one hand on the wooden railing, looking at the horizon over the frozen fjord, wind in his hair. Background: on a wooden palisade facing a frozen fjord, snow, overcast sky, cold desaturated blue-grey palette, dirty trampled snow and wet wood. No smoke.
```
