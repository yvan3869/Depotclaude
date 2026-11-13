import hraf,hmaster,sys
STYLE=hmaster.STYLE
GRIME="sweat, shiny skin, (soot smudges on arms:1.2), dirty hands, stained clothes, clean face, "
VIEW="upper body, three-quarter view, head turned, looking away, "
WARM="indoors, night, dark wooden viking longhouse, hearth fire in background, flames, firelight, damp dark wood walls, warm brown and ochre tones, dim lighting, soot, grime"
BASENEG=("anime, manga, big eyes, big head, chibi, hatching, linear hatching, crosshatching, sketch, photorealistic, realistic, photo, loli, child, teenager, young, youthful, low quality, worst quality, nude, nipples, looking at viewer, "
         "scar, animal ears, furry, old, wrinkles, aged, caricature, pointy chin, long face, exaggerated expression, lamp, window, daylight, silver, silver jewelry, steel, smirk, grin, text, watermark, signature, multiple views, smoke, ")
C={
 "ylva":(STYLE+"solo, 1woman, mature female, 33 years old, adult human woman, seer, beautiful woman, attractive face, realistic facial features, defined cheekbones, playful knowing gaze, faint closed-mouth smile, full lips, oval face, hard confident beauty, realistic proportions, toned adult body, "
   "very long wavy bright turquoise hair, saturated turquoise blue hair, hair down, loose hair, two short black horizontal paint stripes under each eye, "
   "golden bronze chain necklace with one turquoise stone pendant, stacked golden bronze bracelets, "
   "black raven feather cape on shoulders, fitted dark brown leather laced bodice with low neckline, cleavage, bare arms, black fishnet sleeves, thick braided rope belt, dark leather skirt, "
   +GRIME+VIEW+WARM, BASENEG+"forehead tattoo, forehead mark, tattoo, purple hair, heavy makeup, braid, wings, bird"),
 "eirik":(STYLE+"solo, 1man, mature male, 36 years old, adult human man, exile, handsome man in his thirties, attractive rugged face, realistic facial features, strong jaw, weary guarded gaze, serious, closed mouth, smooth skin, realistic proportions, broad shoulders, muscular adult body, "
   "ash blond hair, undercut, shaved sides, short hair on top swept back, short trimmed blond beard, one dark snake tattoo on the side of neck, "
   "thick golden bronze torc bracelets on both wrists, "
   "brown bear fur coat on shoulders, dark brown linen tunic with open collar, covered chest, rolled sleeves, dark leather trousers, thick braided rope belt, braided fishing net sash across chest, "
   +GRIME+VIEW+WARM, BASENEG+"facial tattoo, forehead tattoo, facepaint, long beard, braid, ponytail, long hair, arm tattoo, chest tattoo, full sleeve tattoo, shirtless, bare chest, topless male, snake, animal, smile, 1girl, breasts, purple hair, grey hair"),
}
if __name__=="__main__":
    who=sys.argv[1]; pos,neg=C[who]; names=[]
    for sd in [int(x) for x in sys.argv[2:]]:
        n=f"{who}_m_{sd}"; names.append(n); hraf.make(n,pos,sd,832,1216,neg=neg,lora="cel_rendering_25d.safetensors",ls=0.4)
    hraf.sheet(names,f"sh_{who}_m",w=416,h=608,cols=4)
