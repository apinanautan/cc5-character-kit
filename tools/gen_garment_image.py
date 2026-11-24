# Make ONLY the 2D garment image through ChatGPT (no Hunyuan / no credits):
#   "%LOCALAPPDATA%\Tidmunz Studio\.venv312\Scripts\python.exe" tools\gen_garment_image.py <name> "<description>" [--tpose]
# Needs the Tidmunz Studio program open (ChatGPT bridge). Result: data\garments_3d\<name>\<name>_ref*.png
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

P = kit.PROGRAM
sys.path[:0] = [P, os.path.join(P, "snapgen_modules")]
name, desc = sys.argv[1], sys.argv[2]
out = os.path.join(kit.REPO, "data", "garments_3d", name)
os.makedirs(out, exist_ok=True)
tpose = ("The garment is shaped for a T-POSE: both sleeves stretched straight out sideways at exactly 90 degrees to the body, "
         "perfectly HORIZONTAL (not drooping, not angled down), the whole garment forms a capital letter T; the underarm "
         "seams are flat and horizontal; clear empty space under the sleeves. ") if "--tpose" in sys.argv else ""
prompt = (f"Product photo of ONE garment only: {desc}. Ghost mannequin / invisible mannequin style: the garment keeps its "
          "worn 3D shape but there is NO person, NO mannequin, NO hanger, nothing inside. " + tpose +
          "Straight front view, whole garment visible, centered, plain pure white background, soft even studio light, "
          "no shadow on the background, no text, no logo.")
img = kit.image_gen()(prompt, output_dir=out, name_hint=name + "_ref", aspect_ratio="16:9" if "--tpose" in sys.argv else "1:1")
print("IMAGE", img)
