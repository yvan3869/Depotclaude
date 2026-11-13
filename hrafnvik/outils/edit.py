"""Qwen-Image-Edit 2509 via ComfyUI API: edit(ref_name_on_server, prompt, out_path, w, h, seed)"""
import json,subprocess,time,os,glob
S=os.path.dirname(os.path.abspath(__file__))
B="https://"+open(os.path.join(S,"pod.txt")).read().strip()+"-8188.proxy.runpod.net"
def curl(*a): return subprocess.run(["curl","-sS","-m","120",*a],capture_output=True,text=True).stdout
def upload(path):
    return json.loads(curl("-X","POST",B+"/upload/image","-F",f"image=@{path}","-F","overwrite=true"))["name"]
def build(ref,prompt,w,h,seed,prefix="ref",steps=8):
    return {"1":{"class_type":"UNETLoader","inputs":{"unet_name":"qwen_image_edit_2509_fp8_e4m3fn.safetensors","weight_dtype":"default"}},
    "2":{"class_type":"LoraLoaderModelOnly","inputs":{"model":["1",0],"lora_name":"Qwen-Image-Edit-2509-Lightning-8steps-V1.0-bf16.safetensors","strength_model":1.0}},
    "3":{"class_type":"ModelSamplingAuraFlow","inputs":{"model":["2",0],"shift":3.0}},
    "4":{"class_type":"CFGNorm","inputs":{"model":["3",0],"strength":1.0}},
    "5":{"class_type":"CLIPLoader","inputs":{"clip_name":"qwen_2.5_vl_7b_fp8_scaled.safetensors","type":"qwen_image","device":"default"}},
    "6":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
    "7":{"class_type":"LoadImage","inputs":{"image":ref}},
    "8":{"class_type":"TextEncodeQwenImageEditPlus","inputs":{"clip":["5",0],"vae":["6",0],"image1":["7",0],"prompt":prompt}},
    "9":{"class_type":"TextEncodeQwenImageEditPlus","inputs":{"clip":["5",0],"vae":["6",0],"image1":["7",0],"prompt":""}},
    "10":{"class_type":"EmptySD3LatentImage","inputs":{"width":w,"height":h,"batch_size":1}},
    "11":{"class_type":"KSampler","inputs":{"model":["4",0],"seed":seed,"steps":steps,"cfg":1.0,"sampler_name":"euler","scheduler":"simple","positive":["8",0],"negative":["9",0],"latent_image":["10",0],"denoise":1.0}},
    "12":{"class_type":"VAEDecode","inputs":{"samples":["11",0],"vae":["6",0]}},
    "13":{"class_type":"SaveImage","inputs":{"images":["12",0],"filename_prefix":prefix}}}
def run(g,out,timeout=600):
    r=curl("-X","POST",B+"/prompt","-H","content-type: application/json","-d",json.dumps({"prompt":g}))
    try: pid=json.loads(r)["prompt_id"]
    except Exception: print("ERR",r[:1200]); return None
    t=time.time()
    while time.time()-t<timeout:
        try: h=json.loads(curl(B+"/history/"+pid) or "{}")
        except Exception: h={}
        if pid in h:
            for m in h[pid]["status"].get("messages",[]):
                if m[0]=="execution_error": print(json.dumps(m[1])[:1200])
            for o in h[pid].get("outputs",{}).values():
                for im in o.get("images",[]):
                    subprocess.run(["curl","-sS","-m","90","-o",out,f"{B}/view?filename={im['filename']}&subfolder={im['subfolder']}&type={im['type']}"])
            return round(time.time()-t)
        time.sleep(3)
ID=("Keep exactly the same woman: same face, same facial structure, same green eyes, same freckles, same adult age of 27. ")
if __name__=="__main__":
    ref=upload(glob.glob(S+"/casting/cast_29_*.png")[0]); print("ref",ref)
    tests=[("t1_nomakeup",ID+"Remove all makeup: bare natural skin with visible pores and freckles, no lipstick, no eyeliner, slightly messy wavy auburn hair with copper highlights. Front portrait, mischievous half smile, candid smartphone photo, soft daylight.",864,1152),
           ("t2_threequarter",ID+"Turn her head to a three-quarter left view, looking at the camera with a teasing look and one eyebrow raised. Wavy auburn hair. Candid smartphone photo, natural light, plain wall.",864,1152),
           ("t3_fullbody",ID+"Full body photo of her standing in a bright pilates studio with white walls and plants, wearing a sage green sports bra and matching leggings, athletic toned build with a full bust, auburn hair in a high ponytail, relaxed confident posture, smartphone photo.",832,1216)]
    for n,p,w,h in tests:
        print(n,run(build(ref,p,w,h,7,prefix="t_"+n),os.path.join(S,"ref",n+".png")),"s",flush=True)
