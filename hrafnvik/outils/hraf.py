"""Hrafnvik : generation Illustrious (SDXL) via ComfyUI. gen(pos, out, seed, w, h)"""
import gen,os,json
S=gen.S
CK="ArthemyComics-Illustrious_v80.safetensors"
STYLE="masterpiece, western comics (style), flat color, thick outlines, bold lineart, cel shading, 3d, "
NEG="anime, big head, chibi, hatching, linear hatching, crosshatching, sketch, photorealistic, realistic, photo, loli, child, teenager, young, low quality, worst quality, nude, cleavage, looking at viewer, facial tattoo, forehead tattoo, forehead mark, facial mark, facepaint, scar, animal ears, furry, wolf girl, wrinkles, old, angry, exaggerated expression, braid, text, watermark, signature, multiple views"
FACE=("solo, 1woman, mature female, 34 years old, adult human warrior woman, beautiful face, clean face, bare forehead, sharp facial features, defined cheekbones, stern confident gaze, realistic proportions, "
      "very long wavy vivid purple hair, hair down, three dark band tattoos on each upper arm, "
      "bronze chain necklace with large round bronze medallion, stacked bronze bracelets, ")
INDOOR="sleeveless brown leather viking tunic, bare arms, thick grey braided rope belt, braided fishing net shawl, "
WINTER="thick grey wolf fur cloak over shoulders, sleeveless brown leather viking tunic, bare arms, thick grey braided rope belt, fishing net sash, fur boots, "
SIGRUN=FACE+INDOOR
WARM="indoors, wooden viking longhouse, hearth fire, firelight, smoke, warm brown and ochre tones, soot, grime"
COLD="outdoors, wooden palisade, snow, frozen fjord, cold desaturated blue-grey tones, overcast"
def graph(pos,seed,w=832,h=1216,steps=28,cfg=5.5,neg=NEG,lora=None,ls=0.7):
    g={"c":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":CK}},
       "cs":{"class_type":"CLIPSetLastLayer","inputs":{"clip":["c",1],"stop_at_clip_layer":-2}},
       "p":{"class_type":"CLIPTextEncode","inputs":{"clip":["cs",0],"text":pos}},
       "n":{"class_type":"CLIPTextEncode","inputs":{"clip":["cs",0],"text":neg}},
       "l":{"class_type":"EmptyLatentImage","inputs":{"width":w,"height":h,"batch_size":1}},
       "k":{"class_type":"KSampler","inputs":{"model":["c",0],"seed":seed,"steps":steps,"cfg":cfg,"sampler_name":"euler_ancestral","scheduler":"normal","positive":["p",0],"negative":["n",0],"latent_image":["l",0],"denoise":1.0}},
       "d":{"class_type":"VAEDecode","inputs":{"samples":["k",0],"vae":["c",2]}},
       "o":{"class_type":"SaveImage","inputs":{"images":["d",0],"filename_prefix":"hraf"}}}
    if lora:
        g["lo"]={"class_type":"LoraLoader","inputs":{"model":["c",0],"clip":["c",1],"lora_name":lora,"strength_model":ls,"strength_clip":ls}}
        g["k"]["inputs"]["model"]=["lo",0]; g["cs"]["inputs"]["clip"]=["lo",1]
    return g
LOG=S+"/hraf/log.jsonl"
def make(name,pos,seed,w=832,h=1216,**kw):
    t=gen.run(graph(pos,seed,w,h,**kw),f"{S}/hraf/{name}.png")
    open(LOG,"a").write(json.dumps({"name":name,"prompt":pos,"negative":kw.get("neg",NEG),"seed":seed,"w":w,"h":h,"model":CK,"steps":kw.get("steps",28),"cfg":kw.get("cfg",5.5),"sampler":"euler_ancestral/normal","clip_skip":2,"lora":kw.get("lora")})+"\n")
    print(name,t,flush=True)
def sheet(names,out,w=416,h=608,cols=4):
    from PIL import Image, ImageDraw
    rows=(len(names)+cols-1)//cols; sh=Image.new("RGB",(w*cols,h*rows))
    for i,n in enumerate(names):
        im=Image.open(f"{S}/hraf/{n}.png").convert("RGB"); im.thumbnail((w,h)); sh.paste(im,((i%cols)*w,(i//cols)*h)); ImageDraw.Draw(sh).text(((i%cols)*w+5,(i//cols)*h+5),n,fill=(255,255,0))
    sh.save(f"{S}/hraf/{out}.jpg",quality=85)
VIEWS={
 "1_portrait":(FACE+INDOOR+"portrait, upper body, facing front, straight-on, neutral expression, looking to the side, "+WARM,832,1216),
 "2a_troisquarts":(FACE+INDOOR+"upper body, three-quarter view, head turned, neutral expression, looking away, "+WARM,832,1216),
 "2b_profil":(FACE+INDOOR+"upper body, profile, from side, side view, neutral expression, "+WARM,832,1216),
 "3a_pied_hiver":(FACE+WINTER+"full body, standing, arms crossed, looking away, "+COLD,832,1216),
 "3b_pied_interieur":(FACE+INDOOR+"full body, standing, hand on hip, looking away, "+WARM,832,1216),
 "4a_salle":(FACE+INDOOR+"cowboy shot, sitting by the hearth, sharpening an axe, looking at the fire, wide shot of great hall, "+WARM,1216,832),
 "4b_palissade":(FACE+WINTER+"cowboy shot, standing on wooden palisade walkway, hand on railing, looking at the horizon, wind, "+COLD,1216,832)}
if __name__=="__main__":
    import sys
    seeds=[int(x) for x in sys.argv[1:]] or [3201]
    for sd in seeds:
        names=[]
        for k,(pos,w,h) in VIEWS.items():
            n=f"sig_{k}_{sd}"; names.append(n); make(n,STYLE+pos,sd,w,h)
        sheet(names,f"sh_views_{sd}",w=416,h=416,cols=4)
