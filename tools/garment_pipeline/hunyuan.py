"""Image -> geometry with native Hunyuan3D 2.1 (StableGen ComfyUI). Geometry only, for comparison with TRELLIS.
  python hunyuan.py --run <run dir> --image <png> [--octree 512] [--seed 0]"""
import argparse, shutil, time
from pathlib import Path
import comfy as C

def graph(img, seed, octree, prefix, ckpt="hunyuan_3d_v2.1.safetensors", steps=30, cfg=5.0, res=4096):
    n = C.node
    return {
        "1": n("LoadImage", image=img),
        "5": n("LoadBackgroundRemovalModel", bg_removal_name="birefnet.safetensors"),
        "6": n("RemoveBackground", bg_removal_model=["5", 0], image=["1", 0]),
        "7": n("ImageCropToMask", images=["1", 0], masks=["6", 0], width=1024, height=1024, pad_factor=1.0,
               grow_mask=0, background="#FFFFFF"),
        "2": n("ImageOnlyCheckpointLoader", ckpt_name=ckpt),
        "3": n("CLIPVisionEncode", clip_vision=["2", 1], image=["7", 0], crop="none"),
        "4": n("Hunyuan3Dv2Conditioning", clip_vision_output=["3", 0]),
        "8": n("ModelSamplingAuraFlow", model=["2", 0], shift=1.0),
        "9": n("EmptyLatentHunyuan3Dv2", resolution=res, batch_size=1),
        "10": n("KSampler", model=["8", 0], positive=["4", 0], negative=["4", 1], latent_image=["9", 0], seed=seed,
                steps=steps, cfg=cfg, sampler_name="euler", scheduler="normal", denoise=1.0),
        "11": n("VAEDecodeHunyuan3D", samples=["10", 0], vae=["2", 2], num_chunks=8000, octree_resolution=octree),
        "12": n("VoxelToMesh", voxel=["11", 0], algorithm="surface net", threshold=0.6),
        "13": n("SaveGLB", mesh=["12", 0], filename_prefix=prefix),
    }

ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--image", required=True)
ap.add_argument("--octree", type=int, default=512)
ap.add_argument("--ckpt", default="hunyuan_3d_v2.1.safetensors"); ap.add_argument("--steps", type=int, default=30)
ap.add_argument("--cfg", type=float, default=5.0); ap.add_argument("--res", type=int, default=4096); ap.add_argument("--tag", default=""); ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args(); run = Path(a.run)
C.wait_ready(C.TRELLIS_URL)
img = C.stage_input(a.image, C.TRELLIS_ROOT, "garment_pipeline_input.png")
t = time.time()
e = C.run(C.TRELLIS_URL, graph(img, a.seed, a.octree, f"hy3d_{run.name}_{int(t)}", a.ckpt, a.steps, a.cfg, a.res), label="hunyuan3d")
for f in C.outputs(e, C.TRELLIS_ROOT):
    if f.suffix == ".glb":
        out = run / f"hy3d_raw{a.tag}_o{a.octree}_s{a.seed}.glb"; shutil.copyfile(f, out); print("GLB", out, round(time.time() - t), "s")
