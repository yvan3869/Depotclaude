# Sigrun : prompts et reglages des images retenues (13/11/2026)

## Image maitresse (0_maitresse.png)

- Modele : ArthemyComics-Illustrious_v80.safetensors (Civitai 1273254, v8.0), sans LoRA
- Seed 3202, 832x1216, 28 pas, CFG 5.5, euler_ancestral/normal, clip skip 2
- Prompt :
```
masterpiece, western comics (style), flat color, thick outlines, bold lineart, cel shading, 3d, solo, 1woman, mature female, 34 years old, adult human warrior woman, beautiful face, clean face, bare forehead, sharp facial features, defined cheekbones, stern confident gaze, realistic proportions, very long wavy vivid purple hair, hair down, three dark band tattoos on each upper arm, bronze chain necklace with large round bronze medallion, stacked bronze bracelets, sleeveless brown leather viking tunic, bare arms, thick grey braided rope belt, braided fishing net shawl, upper body, three-quarter view, head turned, neutral expression, looking away, indoors, wooden viking longhouse, hearth fire, firelight, smoke, warm brown and ochre tones, soot, grime
```
- Negatif :
```
anime, big head, chibi, hatching, linear hatching, crosshatching, sketch, photorealistic, realistic, photo, loli, child, teenager, young, low quality, worst quality, nude, cleavage, looking at viewer, facial tattoo, forehead tattoo, forehead mark, facial mark, facepaint, scar, animal ears, furry, wolf girl, wrinkles, old, angry, exaggerated expression, braid, text, watermark, signature, multiple views
```

## Vues derivees de l'image maitresse
Methode : Qwen-Image-Edit 2509 + LoRA Lightning 8 pas (CFG 1, euler/simple, shift 3), image de reference = 0_maitresse.png.

### vue1_portrait_face.png
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same comic book art style with thick black ink outlines, flat colors and cel shading, no hatching: same adult woman, same face, same very long wavy purple hair, same dark red-brown tattoo on each bare upper arm (concentric rings above two horizontal bands), clearly visible, same bronze necklace with round medallion, same bronze bracelets. She wears the same sleeveless brown leather tunic with bare arms and the grey braided rope belt, with a piece of braided fishing net hanging from the belt. Change the camera angle: she now faces the camera directly, symmetrical front view of her face and shoulders, close-up portrait, neutral expression, eyes looking past the viewer. Background: inside a wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, smoke and soot.
```

### vue2a_trois_quarts.png
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same comic book art style with thick black ink outlines, flat colors and cel shading, no hatching: same adult woman, same face, same very long wavy purple hair, same dark red-brown tattoo on each bare upper arm (concentric rings above two horizontal bands), clearly visible, same bronze necklace with round medallion, same bronze bracelets. She wears the same sleeveless brown leather tunic with bare arms and the grey braided rope belt, with a piece of braided fishing net hanging from the belt. Change the camera angle: upper body in three-quarter view turned toward the right side of the picture, looking to the right, neutral expression. Background: inside a wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, smoke and soot.
```

### vue2b_profil.png
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same comic book art style with thick black ink outlines, flat colors and cel shading, no hatching: same adult woman, same face, same very long wavy purple hair, same dark red-brown tattoo on each bare upper arm (concentric rings above two horizontal bands), clearly visible, same bronze necklace with round medallion, same bronze bracelets. She wears the same sleeveless brown leather tunic with bare arms and the grey braided rope belt, with a piece of braided fishing net hanging from the belt. Change the camera angle: rotate the camera 90 degrees to show her in strict side profile, her nose pointing to the left edge of the picture, only one eye visible, upper body, neutral expression. Background: inside a wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, smoke and soot.
```

### vue3a_plein_pied_hiver.png
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same comic book art style with thick black ink outlines, flat colors and cel shading, no hatching: same adult woman, same face, same very long wavy purple hair, same dark red-brown tattoo on each bare upper arm (concentric rings above two horizontal bands), clearly visible, same bronze necklace with round medallion, same bronze bracelets. She wears a thick grey wolf fur cloak pushed back behind her shoulders, leaving her tattooed upper arms visible, over the same sleeveless brown leather tunic with the grey braided rope belt, brown wool trousers and fur boots. Full body view from head to feet, standing with arms crossed, looking away to the side. Background: on a wooden palisade facing a frozen fjord, snow, overcast sky, cold desaturated blue-grey palette.
```

### vue3b_plein_pied_interieur.png
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same comic book art style with thick black ink outlines, flat colors and cel shading, no hatching: same adult woman, same face, same very long wavy purple hair, same dark red-brown tattoo on each bare upper arm (concentric rings above two horizontal bands), clearly visible, same bronze necklace with round medallion, same bronze bracelets. She wears the same sleeveless brown leather tunic with bare arms and the grey braided rope belt, with a piece of braided fishing net hanging from the belt. She also wears brown wool trousers and leather boots. Full body view from head to feet, standing with one hand on her hip, looking away to the side. Background: inside a wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, smoke and soot.
```

### vue4a_grande_salle.png
- Seed 11, 1216x832
- Prompt :
```
Keep exactly the same character and the same comic book art style with thick black ink outlines, flat colors and cel shading, no hatching: same adult woman, same face, same very long wavy purple hair, same dark red-brown tattoo on each bare upper arm (concentric rings above two horizontal bands), clearly visible, same bronze necklace with round medallion, same bronze bracelets. She wears the same sleeveless brown leather tunic with bare arms and the grey braided rope belt, with a piece of braided fishing net hanging from the belt. Medium wide shot: she sits on a bench by the hearth in the great hall sharpening an axe, looking at the fire. Background: inside a wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, smoke and soot.
```

### vue4b_palissade.png
- Seed 11, 1216x832
- Prompt :
```
Keep exactly the same character and the same comic book art style with thick black ink outlines, flat colors and cel shading, no hatching: same adult woman, same face, same very long wavy purple hair, same dark red-brown tattoo on each bare upper arm (concentric rings above two horizontal bands), clearly visible, same bronze necklace with round medallion, same bronze bracelets. She wears a thick grey wolf fur cloak pushed back behind her shoulders, leaving her tattooed upper arms visible, over the same sleeveless brown leather tunic with the grey braided rope belt, brown wool trousers and fur boots. Medium wide shot: she stands on the palisade walkway with one hand on the wooden railing, looking at the horizon over the frozen fjord, wind in her hair. Background: on a wooden palisade facing a frozen fjord, snow, overcast sky, cold desaturated blue-grey palette.
```
