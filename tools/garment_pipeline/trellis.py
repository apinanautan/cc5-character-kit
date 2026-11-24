"""Stage 2: image -> raw 3D geometry with native TRELLIS.2 (StableGen ComfyUI). Geometry only, no UV/texture.

  python trellis.py --run <run dir> --image <concept_garment.png> [--res 1024] [--seed 0]

Writes <run>/raw_<res>.glb (untouched TRELLIS mesh). Decimation is done later with full control (decimate.py);
no voxel remesh here, because a closed 'solid' remesh seals the neck / sleeve / hem openings.
"""
import argparse, json, shutil, time
from pathlib import Path
import comfy as C


def graph(img, res, seed, prefix, tokens, faces=0):
    n = C.node
    return {
        "1": n("LoadImage", image=img),
        "2": n("UNETLoader", unet_name="trellis_2_bf16.safetensors", weight_dtype="default"),
        "3": n("VAELoader", vae_name="trellis_2_shape_vae_bf16.safetensors"),
        "4": n("CLIPVisionLoader", clip_name="dino_v3_vit_l.safetensors"),
        "5": n("LoadBackgroundRemovalModel", bg_removal_name="birefnet.safetensors"),
        "6": n("RemoveBackground", bg_removal_model=["5", 0], image=["1", 0]),
        "7": n("ImageCropToMask", images=["1", 0], masks=["6", 0], width=1024, height=1024, pad_factor=1.0,
               grow_mask=0, background="#000000"),
        "8": n("Trellis2Conditioning", clip_vision_model=["4", 0], image=["7", 0]),
        "9": n("CFGOverride", model=["2", 0], cfg=1.0, start_percent=0.667, end_percent=1.0),
        "10": n("RescaleCFG", multiplier=0.7, model=["9", 0]),
        "11": n("ModelSamplingSD3", shift=5.0, model=["10", 0]),
        "12": n("EmptyTrellis2LatentStructure", batch_size=1),
        "13": n("KSampler", model=["11", 0], positive=["8", 0], negative=["8", 1], latent_image=["12", 0], seed=seed,
                steps=12, cfg=7.5, sampler_name="euler", scheduler="normal", denoise=1.0),
        "14": n("VaeDecodeStructureTrellis2", samples=["13", 0], vae=["3", 0], resolution="32"),
        "15": n("CFGOverride", model=["2", 0], cfg=1.0, start_percent=0.769, end_percent=1.0),
        "16": n("RescaleCFG", multiplier=0.5, model=["15", 0]),
        "17": n("Trellis2ShapeStage", positive=["8", 0], negative=["8", 1], voxel=["14", 0]),
        "18": n("KSampler", model=["16", 0], positive=["17", 0], negative=["17", 1], latent_image=["17", 2], seed=seed,
                steps=12, cfg=7.5, sampler_name="euler", scheduler="normal", denoise=1.0),
        "19": n("StableGenTrellis2TokenBudget", shape_latent=["18", 0], vae=["3", 0], target_resolution=res,
                max_tokens=tokens),
        "20": n("Trellis2UpsampleStage", positive=["17", 0], negative=["17", 1], shape_latent=["18", 0], vae=["3", 0],
                target_resolution=["19", 0]),
        "21": n("KSampler", model=["16", 0], positive=["20", 0], negative=["20", 1], latent_image=["20", 2], seed=seed,
                steps=12, cfg=7.5, sampler_name="euler", scheduler="simple", denoise=1.0),
        "22": n("VaeDecodeShapeTrellis", samples=["21", 0], vae=["3", 0]),
        "30": n("SaveGLB", mesh=["22", 0], filename_prefix=prefix),
        "31": n("SaveImage", images=["7", 0], filename_prefix=prefix + "_input"),
        **({"40": n("DecimateMesh", mesh=["22", 0], target_face_count=faces, placement_mode="qem",
                    **{"placement_mode.line_quadric_weight": 1.0, "placement_mode.feature_edge_quadric_weight": 10.0,
                       "placement_mode.feature_edge_min_dihedral_deg": 30.0, "placement_mode.clamp_v_to_edge": True}),
            "41": n("SaveGLB", mesh=["40", 0], filename_prefix=prefix + f"_dec{faces}")} if faces else {}),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True); ap.add_argument("--image", required=True)
    ap.add_argument("--res", type=int, default=1024); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tokens", type=int, default=49152)
    ap.add_argument("--faces", type=int, default=0, help="also save a GPU-decimated copy with this many faces")
    a = ap.parse_args()
    run = Path(a.run)
    C.wait_ready(C.TRELLIS_URL)
    img = C.stage_input(a.image, C.TRELLIS_ROOT, "garment_pipeline_input.png")
    prefix = f"garment_{run.name}_{int(time.time())}"
    t0 = time.time()
    e = C.run(C.TRELLIS_URL, graph(img, a.res, a.seed, prefix, a.tokens, a.faces), label="trellis")
    files = C.outputs(e, C.TRELLIS_ROOT)
    for glb in (f for f in files if f.suffix == ".glb"):
        out = run / (f"dec_{a.faces}_s{a.seed}.glb" if "_dec" in glb.name else f"raw_{a.res}_s{a.seed}.glb")
        shutil.copyfile(glb, out); print("GLB", out)
    for f in files:
        if f.suffix == ".png":
            shutil.copyfile(f, run / f"trellis_input_s{a.seed}.png")
    json.dump({"image": a.image, "res": a.res, "seed": a.seed, "glb": str(out), "seconds": round(time.time() - t0)},
              open(run / f"raw_{a.res}_s{a.seed}.json", "w"), indent=1)
    print("RAW", out)


if __name__ == "__main__":
    main()
