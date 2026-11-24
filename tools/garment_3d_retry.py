# Like garment_3d.py --image, but logs the task id at once and retries the download (the Hunyuan CDN often drops it).
#   python tools\garment_3d_retry.py <name> <image.jpg>      or  ... <name> --task <creations id>   (download only, no credit)
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit
P = kit.PROGRAM
sys.path[:0] = [P, os.path.join(P, "snapgen_modules")]
from snapgen_modules.hunyuan3d import Hunyuan3DClient
name = sys.argv[1]
out = os.path.join(kit.REPO, "data", "garments_3d", name)
cli = Hunyuan3DClient(cookie_file=os.path.join(P, "snapgen_data", "hunyuan_cookies.txt"))
if sys.argv[2] == "--task":
    task = sys.argv[3]
else:
    task = cli.image_to_3d(sys.argv[2], face_count=int(os.environ.get("FACES", "40000")))
    open(os.path.join(out, "task.txt"), "w").write(task)
print("TASK", task, flush=True)
t0, status = time.time(), None
while time.time() - t0 < 900:
    try:
        st = cli.get_task_status(task)
        s = json.dumps(st).lower()
        if "success" in s and "url" in s:
            status = st; break
        if '"fail' in s:
            sys.exit("Hunyuan failed: " + s[:300])
    except Exception as e:
        print("retry", str(e)[:80], flush=True)
    time.sleep(15)
for i in range(8):
    try:
        files = cli.download_result(status, out, formats=["obj", "glb"])
        print("FILES", files); break
    except Exception as e:
        print("download retry", i, str(e)[:80], flush=True); time.sleep(10)
