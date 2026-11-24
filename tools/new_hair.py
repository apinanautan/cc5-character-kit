# Give a job's character a different hair from the Custom hair list and save the project (the old project is copied first).
#   python tools\new_hair.py <job> <hair index in runs/wardrobe_scan/cand_custom_hair.json> [project file name (default: <job name>.ccProject)]
# Opens the job project in CC5, swaps+dyes the hair (cc5\swap_hair.py), saves, and writes <job>\hair_front.png / hair_face.png to look at.
import json, os, shutil, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
job, idx = sys.argv[1], int(sys.argv[2])
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs", job)
name = json.load(open(os.path.join(J, "job.json"), encoding="utf-8-sig"))["name"]
proj = os.path.join(J, sys.argv[3] if len(sys.argv) > 3 else name + ".ccProject")
bak = os.path.join(J, "before_newhair_" + os.path.basename(proj))
if not os.path.exists(bak):
    shutil.copy2(proj, bak)
hair = json.load(open(os.path.join(ROOT, "runs", "wardrobe_scan", "cand_custom_hair.json"), encoding="utf-8"))[idx]["path"]


def run(*a):
    r = subprocess.run([sys.executable, "tools/cc5.py", "run", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return (r.stdout.strip().splitlines() or ["?"])[-1]


print(run("cc5/probes/open_path.py", "path=" + proj))
print(run("cc5/swap_hair.py", "hair=" + hair, "out=" + os.path.join(J, "hair"), "save=" + proj))
