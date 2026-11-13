# Ylva : prompts et reglages des images retenues (13/11/2026)

Chaine : 1) image maitresse brute (Arthemy Comics Illustrious v8.0 + LoRA 2.5D Cel Shading a 0,4) ; 2) correction par edition ; 3) vues derivees de l'image corrigee.
Edition : Qwen-Image-Edit 2509 + LoRA Lightning 8 pas, CFG 1, euler / simple, shift 3.

## 0a_maitresse_brute.png
- Modele : ArthemyComics-Illustrious_v80.safetensors, LoRA cel_rendering_25d.safetensors poids 0,4
- Seed 5302, 832x1216, 28 pas, CFG 5.5, euler_ancestral/normal, clip skip 2
- Prompt :
```
masterpiece, western comics (style), 3d, toon shading, cel shading, (thick black outlines:1.3), (bold lineart:1.2), outline, flat color, solo, 1woman, mature female, 33 years old, adult human woman, seer, beautiful woman, attractive face, realistic facial features, defined cheekbones, playful knowing gaze, faint closed-mouth smile, full lips, oval face, hard confident beauty, realistic proportions, toned adult body, very long wavy bright turquoise hair, saturated turquoise blue hair, hair down, loose hair, two short black horizontal paint stripes under each eye, golden bronze chain necklace with one turquoise stone pendant, stacked golden bronze bracelets, black raven feather cape on shoulders, fitted dark brown leather laced bodice with low neckline, cleavage, bare arms, black fishnet sleeves, thick braided rope belt, dark leather skirt, sweat, shiny skin, (soot smudges on arms:1.2), dirty hands, stained clothes, clean face, upper body, three-quarter view, head turned, looking away, indoors, night, dark wooden viking longhouse, hearth fire in background, flames, firelight, damp dark wood walls, warm brown and ochre tones, dim lighting, soot, grime
```
- Negatif :
```
anime, manga, big eyes, big head, chibi, hatching, linear hatching, crosshatching, sketch, photorealistic, realistic, photo, loli, child, teenager, young, youthful, low quality, worst quality, nude, nipples, looking at viewer, scar, animal ears, furry, old, wrinkles, aged, caricature, pointy chin, long face, exaggerated expression, lamp, window, daylight, silver, silver jewelry, steel, smirk, grin, text, watermark, signature, multiple views, smoke, forehead tattoo, forehead mark, tattoo, purple hair, heavy makeup, braid, wings, bird
```

## 0b_maitresse_corrigee.png
- Image de reference : ylva_m_5302
- Seed 53, 832x1216
- Prompt :
```
Keep exactly the same image, same woman, same pose, same face, same art style. Make only these changes: 1) add two short black horizontal paint stripes on each cheek just under each eye, ritual face paint. 2) the leather bodice becomes dark brown instead of orange-brown, with a few soot stains. 3) add a piece of braided fishing net tied at her rope belt. Her hair stays the same bright turquoise.
```

## vue1_portrait_face.png
- Image de reference : ylva_fix_53
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same long wavy bright turquoise hair, same two black paint stripes under each eye, same bronze chain necklace with turquoise stone pendant, same bronze bracelets, same soot smudges on her arms, clean face. She wears the same black raven feather cape on her shoulders, the same fitted dark brown leather laced bodice, bare arms with fishnet forearm sleeves, the braided rope belt with a piece of fishing net. Change the camera angle: she now faces the camera directly, shoulders square to the camera, symmetrical front view, head and shoulders close-up portrait, neutral calm expression, eyes looking past the viewer. Background: inside a dark wooden viking longhouse at night lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke anywhere in the picture.
```

## vue2a_trois_quarts.png
- Image de reference : ylva_fix_53
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same long wavy bright turquoise hair, same two black paint stripes under each eye, same bronze chain necklace with turquoise stone pendant, same bronze bracelets, same soot smudges on her arms, clean face. She wears the same black raven feather cape on her shoulders, the same fitted dark brown leather laced bodice, bare arms with fishnet forearm sleeves, the braided rope belt with a piece of fishing net. Change the camera angle: upper body in three-quarter view turned toward the right side of the picture, looking to the right, a faint knowing smile. Background: inside a dark wooden viking longhouse at night lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke anywhere in the picture.
```

## vue2b_profil.png
- Image de reference : ylva_fix_53
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same long wavy bright turquoise hair, same two black paint stripes under each eye, same bronze chain necklace with turquoise stone pendant, same bronze bracelets, same soot smudges on her arms, clean face. She wears the same black raven feather cape on her shoulders, the same fitted dark brown leather laced bodice, bare arms with fishnet forearm sleeves, the braided rope belt with a piece of fishing net. Change the camera angle: rotate the camera 90 degrees to show her strict side profile, nose pointing to the left edge of the picture, only one eye visible, upper body, neutral expression. Background: inside a dark wooden viking longhouse at night lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke anywhere in the picture.
```

## vue3a_plein_pied_hiver.png
- Image de reference : ylva_fix_53
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same long wavy bright turquoise hair, same two black paint stripes under each eye, same bronze chain necklace with turquoise stone pendant, same bronze bracelets, same soot smudges on her arms, clean face. She wears a long thick black raven feather cloak wrapped around her shoulders over the same dark brown leather laced bodice, the braided rope belt, a long dark wool skirt and fur boots. Full body view from head to feet, standing with arms crossed, looking away to the side. Background: on a wooden palisade facing a frozen fjord, snow, overcast sky, cold desaturated blue-grey palette, dirty trampled snow and wet wood. No smoke.
```

## vue3b_plein_pied_interieur.png
- Image de reference : ylva_fix_53
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same long wavy bright turquoise hair, same two black paint stripes under each eye, same bronze chain necklace with turquoise stone pendant, same bronze bracelets, same soot smudges on her arms, clean face. She wears the same black raven feather cape on her shoulders, the same fitted dark brown leather laced bodice, bare arms with fishnet forearm sleeves, the braided rope belt with a piece of fishing net. She also wears a long dark leather skirt split on the side and leather boots. Full body view from head to feet, standing with one hand on the hip, looking away to the side. The wooden floor is worn and dirty. Background: inside a dark wooden viking longhouse at night lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke anywhere in the picture.
```

## vue4a_grande_salle.png
- Image de reference : ylva_fix_53
- Seed 11, 1216x832
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same long wavy bright turquoise hair, same two black paint stripes under each eye, same bronze chain necklace with turquoise stone pendant, same bronze bracelets, same soot smudges on her arms, clean face. She wears the same black raven feather cape on her shoulders, the same fitted dark brown leather laced bodice, bare arms with fishnet forearm sleeves, the braided rope belt with a piece of fishing net. Change the pose and framing: wide shot of the great hall, she sits on a bench by the hearth casting small carved rune stones onto a cloth on her knees, her eyes looking down at the runes, seen from the side in three-quarter view, calm expression. Background: inside a dark wooden viking longhouse at night lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke anywhere in the picture.
```

## vue4b_palissade.png
- Image de reference : ylva_fix_53
- Seed 11, 1216x832
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same long wavy bright turquoise hair, same two black paint stripes under each eye, same bronze chain necklace with turquoise stone pendant, same bronze bracelets, same soot smudges on her arms, clean face. She wears a long thick black raven feather cloak wrapped around her shoulders over the same dark brown leather laced bodice, the braided rope belt, a long dark wool skirt and fur boots. Medium wide shot: she stands on the palisade walkway with one hand on the wooden railing, looking at the horizon over the frozen fjord, wind in her hair. Background: on a wooden palisade facing a frozen fjord, snow, overcast sky, cold desaturated blue-grey palette, dirty trampled snow and wet wood. No smoke.
```
