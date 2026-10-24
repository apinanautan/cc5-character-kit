# Try making a NEW garment as a 3D model: AI image of the garment (ghost mannequin) -> Hunyuan 3D (Tidmunz Studio's
# client, Tencent cloud, 20 credits/day) -> OBJ/GLB in data/garments_3d/<name>/.
#   "%LOCALAPPDATA%\Tidmunz Studio\.venv312\Scripts\python.exe" tools\garment_3d.py <name> "<garment description>"
#   python tools\garment_3d.py thai_school_blouse "เสื้อนักเรียนหญิงไทย..." [--image existing.png]
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

P = kit.PROGRAM
sys.path[:0] = [P, os.path.join(P, "snapgen_modules")]

name, desc = sys.argv[1], sys.argv[2]
out = os.path.join(kit.REPO, "data", "garments_3d", name)
os.makedirs(out, exist_ok=True)
img = sys.argv[sys.argv.index("--image") + 1] if "--image" in sys.argv else None
if not img:
    from snapgen_image_gen import generate_image
    prompt = (f"Product photo of ONE garment only: {desc}. Ghost mannequin / invisible mannequin style: the garment keeps "
              "its worn 3D shape but there is NO person, NO mannequin, NO hanger, nothing inside. Front three-quarter view, "
              "whole garment visible, centered, plain pure white background, soft even studio light, no shadow on the "
              "background, no text, no logo, realistic cotton fabric, simple everyday Thai clothing.")
    img = generate_image(prompt, output_dir=out, name_hint=name + "_ref", aspect_ratio="1:1")
print("IMAGE", img, flush=True)

from snapgen_modules.hunyuan3d import Hunyuan3DClient
cli = Hunyuan3DClient(cookie_file=os.path.join(P, "snapgen_data", "hunyuan_cookies.txt"))
task = cli.image_to_3d(img, face_count=int(os.environ.get("FACES", "30000")))
print("TASK", task, flush=True)
status = cli.wait_for_task(task, timeout=900)
files = cli.download_result(status, out, formats=["obj", "glb"])
json.dump({"desc": desc, "image": img, "task": task, "files": {k: str(v) for k, v in files.items()}},
          open(os.path.join(out, "info.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("FILES", files, flush=True)
