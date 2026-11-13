"""Wan 2.2 T2V still generation via ComfyUI API. gen.py NAME MODE STEPS CFG W H SEED [sampler] [scheduler]
MODE: hl_fast (high+low +lightning) | l_fast (low only +lightning) | hl (no lora) | l (low only, no lora)"""
import json,subprocess,sys,time,os
S=os.path.dirname(os.path.abspath(__file__))
B="https://"+open(os.path.join(S,"pod.txt")).read().strip()+"-8188.proxy.runpod.net"
POS=("candid smartphone photo of an adult woman in her late twenties, 27 years old, mature facial features, wavy shoulder-length auburn hair with copper highlights, "
     "green almond-shaped eyes, full eyebrows, freckles across the nose, small beauty mark under the right eye, slight asymmetric smile, "
     "front-facing head and shoulders portrait, cream knit sweater, plain white wall, soft window light, sharp focus, detailed natural skin texture, visible pores")
NEG="blurry, soft focus, plastic skin, airbrushed, cgi, 3d render, doll, teenager, young girl, childlike, deformed, text, watermark, grid pattern, moire"
def curl(*a): return subprocess.run(["curl","-sS","-m","90",*a],capture_output=True,text=True).stdout
def build(mode,steps,cfg,w,h,seed,sampler,sched,pos=POS,neg=NEG,prefix="q"):
    fast=mode.endswith("_fast"); two=mode.startswith("hl")
    g={"5":{"class_type":"CLIPLoader","inputs":{"clip_name":"umt5_xxl_fp8_e4m3fn_scaled.safetensors","type":"wan","device":"default"}},
       "6":{"class_type":"CLIPTextEncode","inputs":{"clip":["5",0],"text":pos}},"7":{"class_type":"CLIPTextEncode","inputs":{"clip":["5",0],"text":neg}},
       "8":{"class_type":"VAELoader","inputs":{"vae_name":"wan_2.1_vae.safetensors"}},
       "9":{"class_type":"EmptyHunyuanLatentVideo","inputs":{"width":w,"height":h,"length":1,"batch_size":1}}}
    def chain(tag,noise):
        g[tag+"u"]={"class_type":"UNETLoader","inputs":{"unet_name":f"wan2.2_t2v_{noise}_noise_14B_fp8_scaled.safetensors","weight_dtype":"default"}}
        src=tag+"u"
        if fast:
            g[tag+"l"]={"class_type":"LoraLoaderModelOnly","inputs":{"model":[src,0],"lora_name":f"wan2.2_t2v_lightx2v_4steps_lora_v1.1_{noise}_noise.safetensors","strength_model":1.0}}; src=tag+"l"
        g[tag+"s"]={"class_type":"ModelSamplingSD3","inputs":{"model":[src,0],"shift":5.0 if fast else 8.0}}
        return tag+"s"
    def ks(model,latent,add,s,e,ret): return {"class_type":"KSamplerAdvanced","inputs":{"model":[model,0],"add_noise":add,"noise_seed":seed,"steps":steps,"cfg":cfg,
        "sampler_name":sampler,"scheduler":sched,"positive":["6",0],"negative":["7",0],"latent_image":latent,"start_at_step":s,"end_at_step":e,"return_with_leftover_noise":ret}}
    lo=chain("b","low")
    if two:
        hi=chain("a","high"); half=steps//2
        g["10"]=ks(hi,["9",0],"enable",0,half,"enable"); g["11"]=ks(lo,["10",0],"disable",half,steps,"disable")
    else:
        g["11"]=ks(lo,["9",0],"enable",0,steps,"disable")
    g["12"]={"class_type":"VAEDecode","inputs":{"samples":["11",0],"vae":["8",0]}}
    g["15"]={"class_type":"SaveImage","inputs":{"images":["12",0],"filename_prefix":prefix}}
    return g
def run(g,out,timeout=900):
    r=curl("-X","POST",B+"/prompt","-H","content-type: application/json","-d",json.dumps({"prompt":g}))
    try: pid=json.loads(r)["prompt_id"]
    except Exception: print("ERR",r[:800]); return None
    t=time.time()
    while time.time()-t<timeout:
        try: h=json.loads(curl(B+"/history/"+pid) or "{}")
        except Exception: h={}
        if pid in h:
            st=h[pid]["status"]
            for m in st.get("messages",[]):
                if m[0]=="execution_error": print(json.dumps(m[1])[:800])
            for o in h[pid].get("outputs",{}).values():
                for im in o.get("images",[]):
                    subprocess.run(["curl","-sS","-m","90","-o",out,f"{B}/view?filename={im['filename']}&subfolder={im['subfolder']}&type={im['type']}"])
            return round(time.time()-t)
        time.sleep(3)
    return None
if __name__=="__main__":
    a=sys.argv; name,mode,steps,cfg,w,h,seed=a[1],a[2],int(a[3]),float(a[4]),int(a[5]),int(a[6]),int(a[7])
    sampler=a[8] if len(a)>8 else "euler"; sched=a[9] if len(a)>9 else "simple"
    print(name,mode,steps,cfg,f"{w}x{h}",sampler,sched,"->",run(build(mode,steps,cfg,w,h,seed,sampler,sched,prefix="q_"+name),os.path.join(S,"q",name+".png")),"s",flush=True)
