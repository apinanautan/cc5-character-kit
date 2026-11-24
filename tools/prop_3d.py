# Try making a NEW garment as a 3D model: AI image of the garment (ghost mannequin) -> Hunyuan 3D (Tidmunz Studio's
# client, Tencent cloud, 20 credits/day) -> OBJ/GLB in data/garments_3d/<name>/.
#   "%LOCALAPPDATA%\Tidmunz Studio\.venv312\Scripts\python.exe" tools\garment_3d.py <name> "<garment description>"
#   python tools\garment_3d.py thai_school_blouse "เสื้อนักเรียนหญิงไทย..." [--image existing.png] [--tpose]
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

P = kit.PROGRAM
sys.path[:0] = [P, os.path.join(P, "snapgen_modules")]

name, desc = sys.argv[1], sys.argv[2]
out = os.path.join(kit.REPO, "data", "props_3d", name)
os.makedirs(out, exist_ok=True)
img = sys.argv[sys.argv.index("--image") + 1] if "--image" in sys.argv else None
if not img:
    generate_image = kit.image_gen()
    prompt = (f"Product photo of ONE object only: {desc}. Three-quarter view from slightly above, whole object visible, centered, plain pure white background, soft even studio light, no person, no hands, no text, no logo, realistic materials.")
    img = generate_image(prompt, output_dir=out, name_hint=name + "_ref", aspect_ratio="1:1")
    from PIL import Image  # Hunyuan upload times out on big PNGs: send a 1024 jpg
    small = os.path.splitext(img)[0] + "_small.jpg"
    im = Image.open(img).convert("RGB"); im.thumbnail((1024, 1024)); im.save(small, quality=90)
    img = small
print("IMAGE", img, flush=True)

from snapgen_modules.hunyuan3d import Hunyuan3DClient
cli = Hunyuan3DClient(cookie_file=os.path.join(P, "snapgen_data", "hunyuan_cookies.txt"))
task = cli.image_to_3d(img, face_count=int(os.environ.get("FACES", "30000")))
print("TASK", task, flush=True)
import time
t0, status = time.time(), None
while time.time() - t0 < 1200:  # the Hunyuan site is slow from here: retry status calls instead of failing
    try:
        st = cli.get_task_status(task)
        if "success" in json.dumps(st).lower() and "url" in json.dumps(st).lower():
            status = st
            break
        if '"fail' in json.dumps(st).lower():
            sys.exit("Hunyuan failed: " + json.dumps(st)[:300])
    except Exception as e:
        print("retry", str(e)[:80], flush=True)
    time.sleep(15)
files = cli.download_result(status, out, formats=["obj", "glb"])
json.dump({"desc": desc, "image": img, "task": task, "files": {k: str(v) for k, v in files.items()}},
          open(os.path.join(out, "info.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("FILES", files, flush=True)
