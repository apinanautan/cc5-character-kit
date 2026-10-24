# One command: put AI garments (data/garments_3d/<garment>/model.glb) on a character, with renders to check.
#   python tools\try_garment.py <job> <garment>[:top|bottom] [<garment>:bottom ...]
#   e.g. python tools\try_garment.py story_1024_1113_01 thai_school_blouse_t:top thai_school_skirt:bottom
# 1) CC5: export the character's naked body in T-pose  2) Blender: fit each garment to that body
# 3) CC5: T-pose, load them with Transfer Skin Weight, render T-pose + A-pose, save <job>\try_<garments>.ccProject
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

job, specs = sys.argv[1], sys.argv[2:]
d = os.path.join(kit.JOBS, job)
body = os.path.join(d, "body_tpose.obj")
py, cc5 = sys.executable, os.path.join(kit.REPO, "tools", "cc5.py")


def step(label, cmd, timeout=1800):
    print("==", label, flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    out = (r.stdout + r.stderr).strip()
    print("\n".join(l for l in out.splitlines() if l.startswith(("FIT", "WROTE", "OK", "ERROR", "load", "removed",
                                                                    "saved", "exported", "Traceback", "FAIL")))[-1500:], flush=True)
    if r.returncode:
        sys.exit("FAILED at " + label + "\n" + out[-800:])


subprocess.run([py, os.path.join(kit.REPO, "tools", "start_cc5.py")])
step("body T-pose", [py, cc5, "run", "cc5/export_body_tpose.py", "job=" + job, "out=" + body])
# keep RAM low (this PC blue-screens under heavy memory load): close CC5 while Blender works, reopen after
subprocess.run(["taskkill", "/IM", "CharacterCreator.exe", "/F"], capture_output=True)
fitted, kinds = [], []
for spec in specs:
    name, _, kind = spec.partition(":")
    kind = kind or "top"
    g = os.path.join(kit.REPO, "data", "garments_3d", name)
    f = os.path.join(g, "fitted_%s.obj" % job)
    step("fit " + name, [kit.BLENDER, "-b", "--python", os.path.join(kit.REPO, "blender", "fit_garment.py"), "--",
                         os.path.join(g, "model.glb"), body, f, kind])
    fitted.append(f); kinds.append(kind)
subprocess.run([py, os.path.join(kit.REPO, "tools", "start_cc5.py")])
remove = "all" if {"top", "bottom"} <= set(kinds) else "top" if "top" in kinds else "none"
save = "try_" + "_".join(s.partition(":")[0] for s in specs)
step("wear in CC5", [py, cc5, "run", "cc5/wear_garment.py", "job=" + job, "obj=" + ";".join(fitted),
                     "remove=" + remove, "save=" + save])
print("renders:", os.path.join(d, "garment_T.png"), os.path.join(d, "garment_A.png"))
