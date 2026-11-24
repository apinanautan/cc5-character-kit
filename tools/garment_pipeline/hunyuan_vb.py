"""Image -> geometry with Hunyuan3D 2.1 via the visualbruno custom node (original Tencent pipeline:
auto recenter with 15% border, 50 steps, FlashVDM decode, marching cubes at iso 0, floater removal).
  python hunyuan_vb.py --run <run dir> --image <png> [--octree 512] [--steps 50] [--algo mc|dmc] [--seed 0] [--tag _vb]"""
import argparse, shutil, time
from pathlib import Path
import comfy as C


def graph(img, a, prefix):
    n = C.node
    return {
        "1": n("LoadImage", image=img),
        "5": n("LoadBackgroundRemovalModel", bg_removal_name="birefnet.safetensors"),
        "6": n("RemoveBackground", bg_removal_model=["5", 0], image=["1", 0]),
        "7": n("InvertMask", mask=["6", 0]),
        "8": n("JoinImageWithAlpha", image=["1", 0], alpha=["7", 0]),         # RGBA -> pipeline recenters by alpha
        "9": n("Hy3D21MeshGenerator", model="hunyuan3D-dit-v2-1-fp16.ckpt", image=["8", 0], steps=a.steps,
               guidance_scale=a.cfg, seed=a.seed, attention_mode="sdpa"),
        "10": n("Hy3D21VAELoader", model_name="Hunyuan3D-vae-v2-1-fp16.ckpt"),
        "11": n("Hy3D21VAEDecode", vae=["10", 0], latents=["9", 0], box_v=1.01, octree_resolution=a.octree,
                num_chunks=a.chunks, mc_level=0.0, mc_algo=a.algo, enable_flash_vdm=True, force_offload=True),
        "12": n("Hy3D21PostprocessMesh", trimesh=["11", 0], remove_floaters=True, remove_degenerate_faces=True,
                reduce_faces=False, max_facenum=200000, smooth_normals=False),
        "13": n("Hy3D21ExportMesh", trimesh=["12", 0], filename_prefix=prefix, file_format="glb"),
    }


ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--image", required=True)
ap.add_argument("--octree", type=int, default=512); ap.add_argument("--steps", type=int, default=50)
ap.add_argument("--cfg", type=float, default=5.0); ap.add_argument("--algo", default="mc")
ap.add_argument("--chunks", type=int, default=20000); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--tag", default="_vb")
a = ap.parse_args(); run = Path(a.run)
C.wait_ready(C.TRELLIS_URL)
img = C.stage_input(a.image, C.TRELLIS_ROOT, "garment_pipeline_input.png")
t = time.time()
e = C.run(C.TRELLIS_URL, graph(img, a, f"hy3d/vb_{run.name}_{int(t)}"), label="hunyuan3d_vb")
for f in C.outputs(e, C.TRELLIS_ROOT):
    if f.suffix == ".glb":
        out = run / f"hy3d_raw{a.tag}_{a.algo}_o{a.octree}_s{a.seed}.glb"; shutil.copyfile(f, out)
        print("GLB", out, round(time.time() - t), "s")
