"""Make a cleaner garment reference image with local Qwen-Image-Edit 2511 (Tidmunz ComfyUI, GGUF + 4-step Lightning).
Starts that ComfyUI on port 8193 if it is not running. New files only.
  python qwen_edit.py --image src.png --out out.png --prompt "..." [--long 2048] [--seed 1]"""
import argparse, json, shutil, subprocess, time, urllib.request
from pathlib import Path
from PIL import Image

ROOT = Path(r"E:\TidmunzLocalAI\ComfyUI_windows_portable")
BASE = "http://127.0.0.1:8193"


def req(path, data=None, timeout=60):
    r = urllib.request.Request(BASE + path, data=None if data is None else json.dumps(data).encode(),
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as f: return json.load(f)


def ensure_server():
    try: return req("/object_info/UnetLoaderGGUF")
    except Exception: pass
    log = open(ROOT.parent / "garment_qwen_server.log", "w")
    subprocess.Popen([str(ROOT / "python_embeded" / "python.exe"), "-s", "ComfyUI\\main.py", "--listen", "127.0.0.1",
                      "--port", "8193", "--lowvram", "--reserve-vram", "2", "--disable-auto-launch"],
                     cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, creationflags=0x08000000)
    for _ in range(180):
        try: return req("/object_info/UnetLoaderGGUF")
        except Exception: time.sleep(2)
    raise RuntimeError("Qwen ComfyUI did not start, see garment_qwen_server.log")


def node(t, **kw): return {"class_type": t, "inputs": kw}


ap = argparse.ArgumentParser()
ap.add_argument("--image", required=True); ap.add_argument("--out", required=True); ap.add_argument("--prompt", required=True)
ap.add_argument("--long", type=int, default=2048); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--steps", type=int, default=4)
a = ap.parse_args()
info = ensure_server()
im = Image.open(a.image).convert("RGB"); s = a.long / max(im.size)
w, h = (int(round(im.size[0] * s / 16)) * 16, int(round(im.size[1] * s / 16)) * 16)
name = "garment_qwen_in.png"; im.resize((w, h), Image.LANCZOS).save(ROOT / "ComfyUI" / "input" / name)
n = {"1": node("UnetLoaderGGUF", unet_name="qwen-image-edit-2511-Q4_K_M.gguf"),
     "2": node("CLIPLoader", clip_name="qwen_2.5_vl_7b_fp8_scaled.safetensors", type="qwen_image", device="default"),
     "3": node("VAELoader", vae_name="qwen_image_vae.safetensors"),
     "4": node("LoadImage", image=name),
     "7": node("LoraLoaderModelOnly", model=["1", 0], lora_name="Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors", strength_model=1.0),
     "8": node("ModelSamplingAuraFlow", model=["7", 0], shift=3.1),
     "9": node("VAEEncode", pixels=["4", 0], vae=["3", 0]),
     "10": node("TextEncodeQwenImageEditPlus", clip=["2", 0], vae=["3", 0], image1=["4", 0], prompt=a.prompt),
     "11": node("ConditioningZeroOut", conditioning=["10", 0]),
     "14": node("KSampler", model=["8", 0], positive=["12", 0], negative=["13", 0], latent_image=["9", 0], seed=a.seed,
                steps=a.steps, cfg=1.0, sampler_name="euler", scheduler="simple", denoise=1.0),
     "15": node("VAEDecode", samples=["14", 0], vae=["3", 0]),
     "16": node("SaveImage", images=["15", 0], filename_prefix="garment_qwen")}
info = req("/object_info/FluxKontextMultiReferenceLatentMethod")
key = next(k for k in info["FluxKontextMultiReferenceLatentMethod"]["input"]["required"] if k != "conditioning")
n["12"] = node("FluxKontextMultiReferenceLatentMethod", conditioning=["10", 0], **{key: "index_timestep_zero"})
n["13"] = node("FluxKontextMultiReferenceLatentMethod", conditioning=["11", 0], **{key: "index_timestep_zero"})
t = time.time(); pid = req("/prompt", {"prompt": n})["prompt_id"]
while True:
    h_ = req(f"/history/{pid}")
    if pid in h_:
        e = h_[pid]
        if e["status"].get("status_str") == "error": raise RuntimeError(json.dumps(e["status"])[:1500])
        if e["status"].get("completed"): break
    time.sleep(2)
for o in e["outputs"].values():
    for it in o.get("images", []):
        shutil.copyfile(ROOT / "ComfyUI" / "output" / it.get("subfolder", "") / it["filename"], a.out)
print("IMG", a.out, f"{w}x{h}", round(time.time() - t), "s")
