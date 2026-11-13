import edit,hraf,os,json,sys
S=edit.S
KEEP=("Keep exactly the same character and the same comic book art style with thick black ink outlines, flat colors and cel shading, no hatching: "
      "same adult woman, same face, same very long wavy purple hair, same dark red-brown tattoo on each bare upper arm (concentric rings above two horizontal bands), clearly visible, same bronze necklace with round medallion, same bronze bracelets. ")
IN="She wears the same sleeveless brown leather tunic with bare arms and the grey braided rope belt, with a piece of braided fishing net hanging from the belt. "
WI="She wears a thick grey wolf fur cloak pushed back behind her shoulders, leaving her tattooed upper arms visible, over the same sleeveless brown leather tunic with the grey braided rope belt, brown wool trousers and fur boots. "
WARM="Background: inside a wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, smoke and soot."
COLD="Background: on a wooden palisade facing a frozen fjord, snow, overcast sky, cold desaturated blue-grey palette."
V={"1_portrait":(IN+"Change the camera angle: she now faces the camera directly, symmetrical front view of her face and shoulders, close-up portrait, neutral expression, eyes looking past the viewer. "+WARM,832,1216),
 "2a_troisquarts":(IN+"Change the camera angle: upper body in three-quarter view turned toward the right side of the picture, looking to the right, neutral expression. "+WARM,832,1216),
 "2b_profil":(IN+"Change the camera angle: rotate the camera 90 degrees to show her in strict side profile, her nose pointing to the left edge of the picture, only one eye visible, upper body, neutral expression. "+WARM,832,1216),
 "3a_pied_hiver":(WI+"Full body view from head to feet, standing with arms crossed, looking away to the side. "+COLD,832,1216),
 "3b_pied_interieur":(IN+"She also wears brown wool trousers and leather boots. Full body view from head to feet, standing with one hand on her hip, looking away to the side. "+WARM,832,1216),
 "4a_salle":(IN+"Medium wide shot: she sits on a bench by the hearth in the great hall sharpening an axe, looking at the fire. "+WARM,1216,832),
 "4b_palissade":(WI+"Medium wide shot: she stands on the palisade walkway with one hand on the wooden railing, looking at the horizon over the frozen fjord, wind in her hair. "+COLD,1216,832)}
if __name__=="__main__":
    master=sys.argv[1]; tag=sys.argv[2]; seed=int(sys.argv[3]) if len(sys.argv)>3 else 11
    ref=edit.upload(f"{S}/hraf/{master}.png"); names=[]
    for k,(p,w,h) in V.items():
        n=f"{tag}_{k}"; names.append(n)
        t=edit.run(edit.build(ref,KEEP+p,w,h,seed,prefix="hq"),f"{S}/hraf/{n}.png")
        open(hraf.LOG,"a").write(json.dumps({"name":n,"method":"qwen-image-edit-2509 + lightning 8 steps","reference":master,"prompt":KEEP+p,"seed":seed,"w":w,"h":h})+"\n"); print(n,t,flush=True)
    hraf.sheet(names,f"sh_{tag}",w=416,h=416,cols=4)
