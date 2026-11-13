# Sigrun v2 : prompts et reglages des images retenues (13/11/2026)

Chaine : 1) variante C (maitresse_v2/C_lora_04.png, voir maitresse_v2/prompts_v2.md : Arthemy Comics Illustrious v8.0 + LoRA 2.5D Cel Shading a 0,4, seed 4302) ; 2) correction de cette image par edition ; 3) vues derivees de l'image corrigee.
Edition : Qwen-Image-Edit 2509 + LoRA Lightning 8 pas, CFG 1, euler / simple, shift 3.

## 0_maitresse_v2.png
- Image de reference : m_4302_w04 (C_lora_04)
- Seed 31, 832x1216
- Prompt :
```
Keep exactly the same image, the same character, the same pose, the same face and the same 3D toon comic art style with black ink outlines and cel shading. Make only these changes: 1) the fur on her shoulder becomes thick grey wolf fur instead of black. 2) the dark red-brown tattoo on her upper arm becomes three concentric rings with two horizontal bands tattooed just below them. 3) shorten the necklace so the round bronze medallion sits higher at the base of her neck, and add one small simple dark red-brown knot tattoo on her sternum, visible on the bare skin above the bodice. 4) make her slightly grimier: a few soft grey soot smudges on her forearms, hands and shoulder and on the leather bodice, a greasy sweaty sheen on her skin, and a thin grey haze of smoke in the air near the ceiling. No ink splatter, no black clouds. Her face stays perfectly clean. Her hair stays the same vivid purple.
```

## vue1_portrait_face.png
- Image de reference : fix_31
- Seed 13, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears the same fitted dark brown leather laced bodice with a small fishnet panel at the top edge of the bodice only, bare skin on her neck, collarbones and upper chest so the small knot tattoo on her sternum is clearly visible, bare arms, the same braided rope belt and the grey wolf fur on one shoulder. Change the camera angle: she now faces the camera directly, shoulders square to the camera, symmetrical front view, head and shoulders close-up portrait, neutral calm expression, eyes looking past the viewer. Background: inside a dark wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, thin haze of smoke, soot, damp wood.
```

## vue2a_trois_quarts.png
- Image de reference : fix_31
- Seed 12, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears the same fitted dark brown leather laced bodice with a small fishnet panel at the top edge of the bodice only, bare skin on her neck, collarbones and upper chest so the small knot tattoo on her sternum is clearly visible, bare arms, the same braided rope belt and the grey wolf fur on one shoulder. Change the camera angle: upper body in three-quarter view turned toward the right side of the picture, looking to the right, neutral expression. Background: inside a dark wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, thin haze of smoke, soot, damp wood.
```

## vue2b_profil.png
- Image de reference : fix_31
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears the same fitted dark brown leather laced bodice with fishnet at the neckline, bare arms, the same braided rope belt and the grey wolf fur on one shoulder. Change the camera angle: rotate the camera 90 degrees to show her in strict side profile, her nose pointing to the left edge of the picture, only one eye visible, upper body, neutral expression. Background: inside a dark wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, thin haze of smoke, soot, damp wood.
```

## vue3a_plein_pied_hiver.png
- Image de reference : fix_31
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears a long thick grey wolf fur cloak pushed back behind her shoulders, leaving her tattooed upper arms visible, over the same fitted dark brown leather laced bodice with the braided rope belt, dark brown leather trousers and fur boots. Full body view from head to feet, standing with arms crossed, looking away to the side. Background: on a wooden palisade facing a frozen fjord, snow, overcast sky, cold desaturated blue-grey palette, dirty trampled snow and wet wood.
```

## vue3b_plein_pied_interieur.png
- Image de reference : fix_31
- Seed 11, 832x1216
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears the same fitted dark brown leather laced bodice with fishnet at the neckline, bare arms, the same braided rope belt and the grey wolf fur on one shoulder. She also wears a long dark brown leather skirt split on the side over dark trousers and leather boots, with a piece of braided fishing net hanging from the belt. Full body view from head to feet, standing with one hand on her hip, looking away to the side. Background: inside a dark wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, thin haze of smoke, soot, damp wood.
```

## vue4a_grande_salle.png
- Image de reference : fix_31
- Seed 12, 1216x832
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears the same fitted dark brown leather laced bodice with fishnet at the neckline, bare arms, the same braided rope belt and the grey wolf fur on one shoulder. Change the pose and framing: wide shot of the great hall, she is sitting down on a wooden bench beside the hearth, seen from the side in three-quarter view, sharpening an axe blade with a whetstone on her knees, her eyes looking down at the axe, calm neutral expression. Background: inside a dark wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, thin haze of smoke, soot, damp wood.
```

## vue4b_palissade.png
- Image de reference : fix_31
- Seed 11, 1216x832
- Prompt :
```
Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. She wears a long thick grey wolf fur cloak pushed back behind her shoulders, leaving her tattooed upper arms visible, over the same fitted dark brown leather laced bodice with the braided rope belt, dark brown leather trousers and fur boots. Medium wide shot: she stands on the palisade walkway with one hand on the wooden railing, looking at the horizon over the frozen fjord, wind in her hair. Background: on a wooden palisade facing a frozen fjord, snow, overcast sky, cold desaturated blue-grey palette, dirty trampled snow and wet wood.
```
