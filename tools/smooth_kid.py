# Iron out crumpled clothes on a finished character (adult garments squeezed onto a kid), like smoothing them
# by hand in Blender in T-pose. One program at a time (CC5 + Blender together blue-screened this PC):
#   CC5 exports cloth + body in T-pose -> CC5 closed -> Blender smooths/fits each piece -> CC5 puts them back.
#   python tools\smooth_kid.py <job name> [iterations]
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

job = sys.argv[1]
it = sys.argv[2] if len(sys.argv) > 2 else "6"
d = os.path.join(kit.JOBS, job)
work = os.path.join(d, "smooth")
py = sys.executable


def run(*a, **kw):
    r = subprocess.run([py] + list(a), cwd=kit.REPO, capture_output=True, text=True, **kw)
    print(r.stdout.strip()[-400:], flush=True)
    return r


run("tools/start_cc5.py")
run("tools/cc5.py", "run", "cc5/smooth_cloth.py", "job=" + d, "step=export", timeout=1800)
subprocess.run(["taskkill", "/IM", "CharacterCreator.exe", "/F"], capture_output=True)
print("CC5 closed", flush=True)
for f in sorted(os.listdir(work)):
    if f.startswith("c") and f.endswith(".obj") and not f.endswith("_s.obj"):
        r = subprocess.run([kit.BLENDER, "-b", "--python", os.path.join(kit.REPO, "blender", "smooth_obj.py"), "--",
                            os.path.join(work, f), os.path.join(work, f[:-4] + "_s.obj"), it,
                            os.path.join(work, "body.obj")], capture_output=True, text=True, timeout=1800)
        print(f, [l for l in r.stdout.splitlines() if l.startswith(("SMOOTHED", "FIT"))] or r.stderr[-300:], flush=True)
run("tools/start_cc5.py")
run("tools/cc5.py", "run", "cc5/smooth_cloth.py", "job=" + d, "step=apply", timeout=1800)
print("DONE", flush=True)
