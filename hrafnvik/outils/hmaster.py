import hraf,sys
STYLE="masterpiece, western comics (style), 3d, toon shading, cel shading, (thick black outlines:1.3), (bold lineart:1.2), outline, flat color, "
FACE=("solo, 1woman, mature female, 34 years old, adult human warrior woman, clan chief, beautiful woman, attractive face, striking beauty, realistic facial features, defined cheekbones, strong jaw, hard confident gaze, serious, closed mouth, full lips, oval face, realistic proportions, toned adult body, "
      "very long wavy bright vivid purple hair, saturated purple hair, hair down, one dark red-brown tattoo of concentric rings above two bands on upper arm, one small dark knot tattoo on sternum, bare forearms, "
      "bronze chain necklace with large round bronze medallion, stacked bronze bracelets, ")
COST=("fitted dark brown leather bodice with low neckline, cleavage, bare shoulders, bare arms, midriff, black fishnet shoulder cape, fishnet top under bodice, thick grey braided rope belt, dark brown leather skirt, grey wolf fur draped on one shoulder, ")
GRIME="sweat, shiny skin, sweaty skin, (soot smudges on arms:1.2), dirty hands, dirty arms, stained clothes, clean face, "
VIEW="upper body, three-quarter view, head turned, neutral expression, looking away, "
WARM="indoors, wooden viking longhouse, hearth fire, firelight, thick smoke, smoky air, damp dark wood, warm brown and ochre tones, dim lighting, soot, grime"
NEG=("anime, manga, big eyes, big head, chibi, hatching, linear hatching, crosshatching, sketch, photorealistic, realistic, photo, loli, child, teenager, young, youthful, low quality, worst quality, nude, nipples, looking at viewer, "
     "facial tattoo, forehead tattoo, forehead mark, facial mark, facepaint, scar, animal ears, furry, wolf girl, caricature, pointy chin, long face, smirk, smile, lamp, old, wrinkles, aged, sad, frown, full sleeve tattoo, neck tattoo, exaggerated expression, heavy makeup, eyeshadow, braid, text, watermark, signature, multiple views, orange clothes")
POS=STYLE+FACE+COST+GRIME+VIEW+WARM
WTS=(0,0.6,0.8,1.0)
if __name__=="__main__":
    names=[]
    for sd in [int(x) for x in sys.argv[1:]]:
        for wt in WTS:
            n=f"m_{sd}_w{int(wt*10):02d}"; names.append(n)
            hraf.make(n,POS,sd,832,1216,neg=NEG,lora=("cel_rendering_25d.safetensors" if wt else None),ls=wt)
    hraf.sheet(names,"sh_master_"+"_".join(sys.argv[1:]),w=416,h=608,cols=4)
