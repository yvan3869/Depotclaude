import edit,hraf,json,sys
S=edit.S
STY="the same 3D toon comic art style with black ink outlines, cel shading and modeled volumes, no hatching"
WARM="Background: inside a dark wooden viking longhouse at night lit by a hearth fire, warm ochre and brown palette, soot-stained damp wood. Clear air: no smoke anywhere in the picture."
COLD="Background: on a wooden palisade facing a frozen fjord, snow, overcast sky, cold desaturated blue-grey palette, dirty trampled snow and wet wood. No smoke."
CH={
"ylva":dict(master="ylva_m_5302",
 fix="Keep exactly the same image, same woman, same pose, same face, same art style. Make only these changes: 1) add two short black horizontal paint stripes on each cheek just under each eye, ritual face paint. 2) the leather bodice becomes dark brown instead of orange-brown, with a few soot stains. 3) add a piece of braided fishing net tied at her rope belt. Her hair stays the same bright turquoise.",
 keep=f"Keep exactly the same character and {STY}: same adult woman in her thirties, same face, same long wavy bright turquoise hair, same two black paint stripes under each eye, same bronze chain necklace with turquoise stone pendant, same bronze bracelets, same soot smudges on her arms, clean face. ",
 ind="She wears the same black raven feather cape on her shoulders, the same fitted dark brown leather laced bodice, bare arms with fishnet forearm sleeves, the braided rope belt with a piece of fishing net. ",
 win="She wears a long thick black raven feather cloak wrapped around her shoulders over the same dark brown leather laced bodice, the braided rope belt, a long dark wool skirt and fur boots. ",
 expr="a faint knowing smile", act_hall="she sits on a bench by the hearth casting small carved rune stones onto a cloth on her knees, her eyes looking down at the runes", extra_in="She also wears a long dark leather skirt split on the side and leather boots. "),
"eirik":dict(master="eirik_m_5402",
 fix="Keep exactly the same image, same man, same pose, same face, same art style. Make only these changes: 1) add a braided fishing net sash worn across his chest over the tunic, from one shoulder to the opposite hip. 2) make the dark snake tattoo on the side of his neck clearer: a simple snake shape rising from the collar to below the ear. His hair and beard stay the same ash blond.",
 keep=f"Keep exactly the same character and {STY}: same adult man in his mid-thirties, same face, same ash blond hair with shaved sides, same short blond beard, same dark snake tattoo on the side of his neck, same thick bronze torc bracelets on both wrists, same soot stains. ",
 ind="He wears the same dark brown linen tunic with laced open collar and rolled sleeves, the fishing net sash across his chest, the braided rope belt and dark leather trousers, with the brown bear fur coat on his shoulders. ",
 win="He wears the same heavy brown bear fur coat closed over the dark brown tunic, the fishing net sash, the braided rope belt, dark leather trousers and fur-lined boots. ",
 expr="a weary guarded expression", act_hall="he sits on a bench by the hearth mending a fishing net with his hands, his eyes looking down at the net", extra_in="He also wears leather boots. "),
}
def run(refname,name,pp,w,h,sd):
    ref=edit.upload(f"{S}/hraf/{refname}.png")
    t=edit.run(edit.build(ref,pp,w,h,sd,prefix="hq"),f"{S}/hraf/{name}.png")
    open(hraf.LOG,"a").write(json.dumps({"name":name,"method":"qwen-image-edit-2509 + lightning 8 steps","reference":refname,"prompt":pp,"seed":sd,"w":w,"h":h})+"\n"); print(name,t,flush=True)
def views(c):
    P="She" if "woman" in c["keep"] else "He"; p="her" if P=="She" else "his"; s=P.lower()
    return {"1_portrait":(c["ind"]+f"Change the camera angle: {s} now faces the camera directly, shoulders square to the camera, symmetrical front view, head and shoulders close-up portrait, neutral calm expression, eyes looking past the viewer. "+WARM,832,1216),
     "2a_troisquarts":(c["ind"]+f"Change the camera angle: upper body in three-quarter view turned toward the right side of the picture, looking to the right, {c['expr']}. "+WARM,832,1216),
     "2b_profil":(c["ind"]+f"Change the camera angle: rotate the camera 90 degrees to show {p} strict side profile, nose pointing to the left edge of the picture, only one eye visible, upper body, neutral expression. "+WARM,832,1216),
     "3a_pied_hiver":(c["win"]+"Full body view from head to feet, standing with arms crossed, looking away to the side. "+COLD,832,1216),
     "3b_pied_interieur":(c["ind"]+c["extra_in"]+"Full body view from head to feet, standing with one hand on the hip, looking away to the side. The wooden floor is worn and dirty. "+WARM,832,1216),
     "4a_salle":(c["ind"]+f"Change the pose and framing: wide shot of the great hall, {c['act_hall']}, seen from the side in three-quarter view, calm expression. "+WARM,1216,832),
     "4b_palissade":(c["win"]+f"Medium wide shot: {s} stands on the palisade walkway with one hand on the wooden railing, looking at the horizon over the frozen fjord, wind in {p} hair. "+COLD,1216,832)}
if __name__=="__main__":
    who,step=sys.argv[1],sys.argv[2]; c=CH[who]
    if step=="fix":
        names=[]
        for sd in (51,52,53):
            n=f"{who}_fix_{sd}"; names.append(n); run(c["master"],n,c["fix"],832,1216,sd)
        hraf.sheet([c["master"]]+names,f"sh_{who}_fix",w=416,h=608,cols=4)
    else:
        ref=sys.argv[3]; sd=int(sys.argv[4]) if len(sys.argv)>4 else 11; only=sys.argv[5:]; names=[]
        for k,(pp,w,h) in views(c).items():
            n=f"{who}_v_{k}"; names.append(n)
            if only and k not in only: continue
            run(ref,n,c["keep"]+pp,w,h,sd)
        hraf.sheet([ref]+names,f"sh_{who}_v",w=416,h=416,cols=4)
