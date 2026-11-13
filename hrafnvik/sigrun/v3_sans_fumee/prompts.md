# Sigrun v3 (sans fumee) : prompts et reglages (13/11/2026)

Meme chaine que v2 (voir ../v2/prompts.md). La fumee a ete retiree de l'image maitresse par edition, puis les vues d'interieur ont ete derivees de cette image. Les deux vues d'exterieur sont celles de la v2 (derivees de la maitresse v2, sans fumee).
Edition : Qwen-Image-Edit 2509 + LoRA Lightning 8 pas, CFG 1, euler / simple, shift 3.

## 0_maitresse_v3.png
- Image de reference : fix_31
- Seed 41, 832x1216
- Prompt :
```
Keep exactly the same image, same character, same pose, same face, same art style, same colors. Make only one change: remove all the smoke wisps and smoke from the picture, showing the wooden wall and ceiling behind instead. Nothing else changes.
```

## vue1_portrait_face.png
- Image de reference : fix_31_ns
- Seed 13, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears the same fitted dark brown leather laced bodice with a small fishnet panel at the top edge of the bodice only, bare skin on her neck, collarbones and upper chest so the small knot tattoo on her sternum is clearly visible, bare arms, the same braided rope belt and the grey wolf fur on one shoulder. Change the camera angle: she now faces the camera directly, shoulders square to the camera, symmetrical front view, head and shoulders close-up portrait, neutral calm expression, eyes looking past the viewer. Background: inside a dark wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke, no smoke wisps, no steam anywhere in the picture.
```

## vue2a_trois_quarts.png
- Image de reference : fix_31_ns
- Seed 12, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears the same fitted dark brown leather laced bodice with a small fishnet panel at the top edge of the bodice only, bare skin on her neck, collarbones and upper chest so the small knot tattoo on her sternum is clearly visible, bare arms, the same braided rope belt and the grey wolf fur on one shoulder. Change the camera angle: upper body in three-quarter view turned toward the right side of the picture, looking to the right, neutral expression. Background: inside a dark wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke, no smoke wisps, no steam anywhere in the picture.
```

## vue2b_profil.png
- Image de reference : fix_31_ns
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears the same fitted dark brown leather laced bodice with fishnet at the neckline, bare arms, the same braided rope belt and the grey wolf fur on one shoulder. Change the camera angle: rotate the camera 90 degrees to show her in strict side profile, her nose pointing to the left edge of the picture, only one eye visible, upper body, neutral expression. Background: inside a dark wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke, no smoke wisps, no steam anywhere in the picture.
```

## vue3a_plein_pied_hiver.png
- Image de reference : fix_31
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears a long thick grey wolf fur cloak pushed back behind her shoulders, leaving her tattooed upper arms visible, over the same fitted dark brown leather laced bodice with the braided rope belt, dark brown leather trousers and fur boots. Full body view from head to feet, standing with arms crossed, looking away to the side. Background: on a wooden palisade facing a frozen fjord, snow, overcast sky, cold desaturated blue-grey palette, dirty trampled snow and wet wood.
```

## vue3b_plein_pied_interieur.png
- Image de reference : fix_31_ns
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears the same fitted dark brown leather laced bodice with a small fishnet panel at the top edge of the bodice only, bare skin on her neck, collarbones and upper chest so the small knot tattoo on her sternum is clearly visible, bare arms, the same braided rope belt and the grey wolf fur on one shoulder. She also wears a long dark brown leather skirt split on the side over dark trousers and leather boots, with a piece of braided fishing net hanging from the belt. Full body view from head to feet, standing with one hand on her hip, looking away to the side. The wooden floor is worn and dirty but has no black spots or drops. Background: inside a dark wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke, no smoke wisps, no steam anywhere in the picture.
```

## vue4a_grande_salle.png
- Image de reference : fix_31_ns
- Seed 12, 1216x832
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears the same fitted dark brown leather laced bodice with fishnet at the neckline, bare arms, the same braided rope belt and the grey wolf fur on one shoulder. Change the pose and framing: wide shot of the great hall, she is sitting down on a wooden bench beside the hearth, seen from the side in three-quarter view, sharpening an axe blade with a whetstone on her knees, her eyes looking down at the axe, calm neutral expression. Background: inside a dark wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke, no smoke wisps, no steam anywhere in the picture.
```

## vue4b_palissade.png
- Image de reference : fix_31
- Seed 11, 1216x832
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears a long thick grey wolf fur cloak pushed back behind her shoulders, leaving her tattooed upper arms visible, over the same fitted dark brown leather laced bodice with the braided rope belt, dark brown leather trousers and fur boots. Medium wide shot: she stands on the palisade walkway with one hand on the wooden railing, looking at the horizon over the frozen fjord, wind in her hair. Background: on a wooden palisade facing a frozen fjord, snow, overcast sky, cold desaturated blue-grey palette, dirty trampled snow and wet wood.
```
