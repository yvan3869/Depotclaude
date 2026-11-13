import edit,hraf,os,json,sys
S=edit.S
KEEP=("Keep exactly the same character and the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching: "
      "same adult woman in her thirties, same face, same very long wavy vivid purple hair, same dark red-brown tattoo on her upper arm (concentric rings above three horizontal bands), same small dark red-brown knot tattoo on her sternum, "
      "same bronze chain necklace with round medallion, same bronze bracelets, same soot smudges on her forearms and sweaty skin, clean face. ")
IN="She wears the same fitted dark brown leather laced bodice with fishnet at the neckline, bare arms, the same braided rope belt and the grey wolf fur on one shoulder. "
WI="She wears a long thick grey wolf fur cloak pushed back behind her shoulders, leaving her tattooed upper arms visible, over the same fitted dark brown leather laced bodice with the braided rope belt, dark brown leather trousers and fur boots. "
WARM="Background: inside a dark wooden viking longhouse lit by a hearth fire, warm ochre and brown palette, thin haze of smoke, soot, damp wood."
COLD="Background: on a wooden palisade facing a frozen fjord, snow, overcast sky, cold desaturated blue-grey palette, dirty trampled snow and wet wood."
V={"1_portrait":(IN+"Change the camera angle: she now faces the camera directly, symmetrical front view of her face and shoulders, close-up portrait, neutral expression, eyes looking past the viewer. "+WARM,832,1216),
 "2a_troisquarts":(IN+"Change the camera angle: upper body in three-quarter view turned toward the right side of the picture, looking to the right, neutral expression. "+WARM,832,1216),
 "2b_profil":(IN+"Change the camera angle: rotate the camera 90 degrees to show her in strict side profile, her nose pointing to the left edge of the picture, only one eye visible, upper body, neutral expression. "+WARM,832,1216),
 "3a_pied_hiver":(WI+"Full body view from head to feet, standing with arms crossed, looking away to the side. "+COLD,832,1216),
 "3b_pied_interieur":(IN+"She also wears a long dark brown leather skirt split on the side over dark trousers and leather boots, with a piece of braided fishing net hanging from the belt. Full body view from head to feet, standing with one hand on her hip, looking away to the side. "+WARM,832,1216),
 "4a_salle":(IN+"Medium wide shot: she sits on a bench by the hearth in the great hall sharpening an axe, looking at the fire. "+WARM,1216,832),
 "4b_palissade":(WI+"Medium wide shot: she stands on the palisade walkway with one hand on the wooden railing, looking at the horizon over the frozen fjord, wind in her hair. "+COLD,1216,832)}
if __name__=="__main__":
    master=sys.argv[1]; tag=sys.argv[2]; seed=int(sys.argv[3]) if len(sys.argv)>3 else 11
    only=sys.argv[4:] 
    ref=edit.upload(f"{S}/hraf/{master}.png"); names=[]
    for k,(p,w,h) in V.items():
        n=f"{tag}_{k}"; names.append(n)
        if only and k not in only: continue
        t=edit.run(edit.build(ref,KEEP+p,w,h,seed,prefix="hq"),f"{S}/hraf/{n}.png")
        open(hraf.LOG,"a").write(json.dumps({"name":n,"method":"qwen-image-edit-2509 + lightning 8 steps","reference":master,"prompt":KEEP+p,"seed":seed,"w":w,"h":h})+"\n"); print(n,t,flush=True)
    hraf.sheet(names,f"sh_{tag}",w=416,h=416,cols=4)
