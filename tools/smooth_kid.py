# Iron out crumpled clothes on a finished character (adult garments squeezed onto a kid), like smoothing them
# by hand in Blender in T-pose. One program at a time (CC5 + Blender together blue-screened this PC):
#   CC5 exports cloth + body in T-pose -> CC5 closed -> Blender smooths/fits each piece -> CC5 puts them back.
#   python tools\smooth_kid.py <job name> [iterations]
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

job = sys.argv[1]
it = next((a for a in sys.argv[2:] if a.isdigit()), "4")
d = os.path.join(kit.JOBS, job)
work = os.path.join(d, "smooth")
py = sys.executable


def run(*a, **kw):
    r = subprocess.run([py] + list(a), cwd=kit.REPO, capture_output=True, text=True, **kw)
    print(r.stdout.strip()[-400:], flush=True)
    return r


if "--again" not in sys.argv:  # --again: redo Blender from the c<n>.obj already exported (the untouched cloth)
    run("tools/start_cc5.py")
    run("tools/cc5.py", "run", "cc5/smooth_cloth.py", "job=" + d, "step=export", timeout=1800)
subprocess.run(["taskkill", "/IM", "CharacterCreator.exe", "/F"], capture_output=True)
print("CC5 closed", flush=True)
upper = open(os.path.join(d, "upper.txt"), encoding="utf-8").read().split() if os.path.exists(os.path.join(d, "upper.txt")) else []
names = dict(l.split(" ", 1) for l in open(os.path.join(work, "names.txt"), encoding="utf-8").read().splitlines())
cloth = [f for f in os.listdir(work) if f.startswith("c") and f.endswith(".obj") and not f.endswith("_s.obj")]
done = []
for f in sorted(cloth, key=lambda f: names.get(f[:-4], "") in upper):  # bottoms first: the shirt lies over them
    if True:
        shirt = names.get(f[:-4], "") in upper  # shirts are laid onto the body; bottoms keep their drape
        r = subprocess.run([kit.BLENDER, "-b", "--python", os.path.join(kit.REPO, "blender", "smooth_obj.py"), "--",
                            os.path.join(work, f), os.path.join(work, f[:-4] + "_s.obj"), it,
                            os.path.join(work, "body.obj")] + (["tight"] + ["over=" + o for o in done] if shirt else []),
                           capture_output=True, text=True, timeout=3600)
        if not shirt:
            done.append(os.path.join(work, f[:-4] + "_s.obj"))
        print(f, [l for l in r.stdout.splitlines() if l.startswith(("SMOOTHED", "FIT"))] or r.stderr[-300:], flush=True)
run("tools/start_cc5.py")
run("tools/cc5.py", "run", "cc5/smooth_cloth.py", "job=" + d, "step=apply", timeout=1800)
print("DONE", flush=True)
