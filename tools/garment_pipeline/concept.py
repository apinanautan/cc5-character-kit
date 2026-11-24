"""Stage 1: garment concept image, made ON the real character's T-pose silhouette.

  python concept.py --run <run dir> --design "<garment description>" [--seed N] [--image <your own garment image>]

1) ref_body_front.png (Blender render of the exported CC5 body) -> Qwen-Image-Edit: dress the mannequin
   in the design (so proportions, sleeve angle and hem height match this exact body),
2) -> Qwen-Image-Edit: remove the body, keep the garment only (ghost-mannequin product shot) with the
   neck, sleeve and hem openings visible -> concept_garment.png, the input for image-to-3D.
With --image, step 1 uses that picture as the design reference instead of text alone.
"""
import argparse, json
from pathlib import Path
from PIL import Image
import comfy as C

DRESS = ("Dress this grey mannequin in the following garment: {design}. "
         "Keep the exact same T-pose, arms straight out horizontally, same camera, same body proportions, same framing "
         "and the same plain grey background. The garment is worn naturally and fits this body, real fabric with "
         "small natural folds. Only the garment is added; no other clothing, no accessories, no props.")
GHOST = ("Remove the mannequin body completely: no head, no neck, no arms, no hands, no skin, no legs. "
         "Keep ONLY the garment, unchanged in shape, size, position, color and pattern, as an invisible-mannequin "
         "(ghost mannequin) product photo: the garment keeps its worn 3D volume with the sleeves straight out "
         "horizontally, the inside of the back collar visible through the neck opening, sleeve cuffs and the "
         "bottom hem open and hollow. Plain flat light grey background, soft even studio light, no shadow, "
         "nothing else in the picture.")
REF_DESIGN = ("Dress this grey mannequin in the garment shown in the second picture, copying its design, color, "
              "pattern, collar, sleeves and length exactly. Keep the exact same T-pose, arms straight out horizontally, "
              "same camera, proportions, framing and plain grey background. Only that garment is added.")


def edit(images, prompt, seed, out, w=1024, h=1024):
    names = [C.stage_input(p, C.QWEN_ROOT, f"garment_in_{i}.png") for i, p in enumerate(images)]
    info = C.wait_ready(C.QWEN_URL)
    n = C.node
    g = {"1": n("UnetLoaderGGUF", unet_name="qwen-image-edit-2511-Q4_K_M.gguf"),
         "2": n("CLIPLoader", clip_name="qwen_2.5_vl_7b_fp8_scaled.safetensors", type="qwen_image", device="default"),
         "3": n("VAELoader", vae_name="qwen_image_vae.safetensors"),
         "7": n("LoraLoaderModelOnly", model=["1", 0], lora_name="Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors",
                strength_model=1.0),
         "8": n("ModelSamplingAuraFlow", model=["7", 0], shift=3.1),
         "9": n("EmptySD3LatentImage", width=w, height=h, batch_size=1),
         "14": n("KSampler", model=["8", 0], positive=["12", 0], negative=["13", 0], latent_image=["9", 0], seed=seed,
                 steps=4, cfg=1.0, sampler_name="euler", scheduler="simple", denoise=1.0),
         "15": n("VAEDecode", samples=["14", 0], vae=["3", 0]),
         "16": n("SaveImage", images=["15", 0], filename_prefix="garment_concept")}
    enc = {"clip": ["2", 0], "vae": ["3", 0], "prompt": prompt}
    for i, name in enumerate(names):
        g[f"4{i}"] = n("LoadImage", image=name)
        enc[f"image{i + 1}"] = [f"4{i}", 0]
    g["10"] = n("TextEncodeQwenImageEditPlus", **enc)
    g["11"] = n("ConditioningZeroOut", conditioning=["10", 0])
    spec = info["FluxKontextMultiReferenceLatentMethod"]["input"]["required"]
    key = next(k for k in spec if k != "conditioning")
    g["12"] = n("FluxKontextMultiReferenceLatentMethod", conditioning=["10", 0], **{key: "index_timestep_zero"})
    g["13"] = n("FluxKontextMultiReferenceLatentMethod", conditioning=["11", 0], **{key: "index_timestep_zero"})
    e = C.run(C.QWEN_URL, g, label=Path(out).stem)
    src = C.outputs(e, C.QWEN_ROOT)[0]
    Image.open(src).convert("RGB").save(out)
    return out


def extract_garment(ref, dressed, out, thr=28):
    """Garment-only image without a second AI pass: pixels that changed between the bare mannequin render and
    the dressed render (same camera) are the garment; skin, head, legs and background stay identical -> removed."""
    import numpy as np
    from scipy import ndimage as ndi
    a = np.asarray(Image.open(ref).convert("RGB").resize((1024, 1024)), np.float32)
    b = np.asarray(Image.open(dressed).convert("RGB").resize((1024, 1024)), np.float32)
    d = np.abs(ndi.uniform_filter(a, (5, 5, 1)) - ndi.uniform_filter(b, (5, 5, 1))).max(2)
    r = (ndi.uniform_filter(b, (5, 5, 1)) + 1) / (ndi.uniform_filter(a, (5, 5, 1)) + 1)
    shadow = (r.std(2) < 0.035) & (r.mean(2) < 0.97)      # same colour as the mannequin/backdrop, only darker
    m = (d > thr) & ~shadow
    m = ndi.binary_opening(m, iterations=2)
    m = ndi.binary_closing(m, iterations=4)
    lab, n = ndi.label(m)
    if n == 0: raise RuntimeError("no garment found")
    sizes = ndi.sum(m, lab, range(1, n + 1))
    m = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 0.05 * sizes.max()])
    holes = ndi.binary_fill_holes(m) & ~m                     # fill only small pinholes, keep real openings
    hl, hn = ndi.label(holes)
    if hn:
        hs = ndi.sum(holes, hl, range(1, hn + 1))
        m |= np.isin(hl, [i + 1 for i, s in enumerate(hs) if s < 400])
    bg = np.full_like(b, 200.0)
    rgba = np.dstack([np.where(m[..., None], b, bg), m * 255.0]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(out)
    Image.fromarray((m * 255).astype(np.uint8)).save(str(out).replace(".png", "_mask.png"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True); ap.add_argument("--design", default="")
    ap.add_argument("--seed", type=int, default=1201); ap.add_argument("--image")
    ap.add_argument("--step", choices=["all", "dress", "extract", "ghost"], default="all")
    a = ap.parse_args()
    run = Path(a.run)
    ref = run / "ref_body_front.png"
    dressed, ghost = run / f"concept_dressed_s{a.seed}.png", run / f"concept_garment_s{a.seed}.png"
    if a.step in ("all", "dress"):
        if a.image:
            edit([ref, a.image], REF_DESIGN + (" " + a.design if a.design else ""), a.seed, dressed)
        else:
            edit([ref], DRESS.format(design=a.design), a.seed, dressed)
    if a.step in ("all", "extract"):   # deterministic cut-out (the AI 'ghost' edit turned the shirt around)
        extract_garment(ref, dressed, ghost)
    if a.step == "ghost":
        edit([dressed], GHOST, a.seed + 1, ghost)
    json.dump({"design": a.design, "image": a.image, "seed": a.seed, "dressed": str(dressed), "garment": str(ghost)},
              open(run / f"concept_s{a.seed}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("CONCEPT", ghost)


if __name__ == "__main__":
    main()
