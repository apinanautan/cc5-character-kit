# One garment: Blender clay views -> GPT paints fabric + sewing details -> Blender bakes into the garment's own UV.
#   python paint_garment.py <char.fbx> <mesh name> <out dir> "<garment kind>" "<fabric description>"
# Output: <out dir>\baked.png (load as Diffuse in CC5 with UV tiling 1x1, see cc5_retexture.py)
import os, subprocess, sys
from PIL import Image

BLENDER = r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio")
sys.path[:0] = [P, os.path.join(P, "snapgen_modules")]
from snapgen_image_gen import generate_image

fbx, mesh, out, kind, fabric = sys.argv[1:6]
os.makedirs(out, exist_ok=True)
NAMES = ["front", "back"]


def blender(*args):
    subprocess.run([BLENDER, "-b", "--python", os.path.join(HERE, "blender_proj.py"), "--", *args],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if not os.path.exists(os.path.join(out, "view_1.png")):
    blender("render", fbx, mesh, out)
DETAIL = ("Add realistic garment construction details exactly where they belong on this shape: visible sewn seams "
          "(shoulder seams, side seams, armhole seams), neat topstitched hems at the bottom and sleeve ends, a narrow "
          "binding along the neckline and front opening, slight seam puckering, subtle cotton weave and soft natural "
          "wear. ")
for i, name in enumerate(NAMES):
    dst = os.path.join(out, "painted_%d.png" % i)
    if os.path.exists(dst):
        continue
    refs = [os.path.join(out, "view_%d.png" % i)] + ([os.path.join(out, "painted_0.png")] if i else [])
    prompt = (f"Texture-paint the {kind} in the FIRST image ({name} view, orthographic) as {fabric}. " + DETAIL +
              "Keep EXACTLY the same silhouette, folds, buttons, size, position and camera framing, and the same plain "
              "gray background. Do not move, crop, rotate or zoom; no person, no body, no mannequin, no text. "
              "Keep the original fold shading. Print scale small and consistent everywhere. "
              + ("This is the BACK of the garment: it has NO buttons, NO front opening and NO placket; paint only what the "
                 "FIRST image shows (a center-back or plain back panel). Use the SECOND image only as a swatch for fabric, colors, "
                 "print scale and stitching style; do NOT copy its shape or buttons. " if i else ""))
    p = generate_image(prompt, output_dir=out, name_hint="painted_raw_%d" % i, is_edit=True,
                       ref_images=refs, aspect_ratio="1:1")
    Image.open(p).convert("RGB").resize((1024, 1024)).save(dst)
    print("painted", i, flush=True)
blender("bake", fbx, mesh, out, "2048")
print("BAKED", os.path.join(out, "baked.png"))
