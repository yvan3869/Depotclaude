import edit,hraf,json,sys
S=edit.S
STY="Keep exactly the same image, the same character, the same pose, the same face and the same 3D toon comic art style with black ink outlines and cel shading. "
FIX=(STY+"Make only these changes: 1) the fur on her shoulder becomes thick grey wolf fur instead of black. "
 "2) the dark red-brown tattoo on her upper arm becomes three concentric rings with two horizontal bands tattooed just below them. "
 "3) shorten the necklace so the round bronze medallion sits higher at the base of her neck, and add one small simple dark red-brown knot tattoo on her sternum, visible on the bare skin above the bodice. "
 "4) make her slightly grimier: a few soft grey soot smudges on her forearms, hands and shoulder and on the leather bodice, a greasy sweaty sheen on her skin, and a thin grey haze of smoke in the air near the ceiling. No ink splatter, no black clouds. Her face stays perfectly clean. "
 "Her hair stays the same vivid purple.")
if __name__=="__main__":
    ref=edit.upload(f"{S}/hraf/m_4302_w04.png"); names=[]
    for sd in (31,32,33):
        n=f"fix_{sd}"; names.append(n)
        t=edit.run(edit.build(ref,FIX,832,1216,sd,prefix="hf"),f"{S}/hraf/{n}.png")
        open(hraf.LOG,"a").write(json.dumps({"name":n,"method":"qwen-image-edit-2509 + lightning 8 steps","reference":"m_4302_w04 (C_lora_04)","prompt":FIX,"seed":sd,"w":832,"h":1216})+"\n"); print(n,t,flush=True)
    hraf.sheet(["m_4302_w04"]+names,"sh_fix",w=416,h=608,cols=4)
