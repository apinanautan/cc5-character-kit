# One command: AI garment (data/garments_3d/<garment>/model.glb) onto a character, with renders to check.
#   python tools\try_garment.py <job> <garment> [top|bottom]
# 1) CC5: export the character's naked body in T-pose  2) Blender: fit the garment to that body
# 3) CC5: T-pose, load it with Transfer Skin Weight, render T-pose + A-pose, save as <job>\<garment>.ccProject
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

job, garment = sys.argv[1], sys.argv[2]
kind = sys.argv[3] if len(sys.argv) > 3 else "top"
d = os.path.join(kit.JOBS, job)
g = os.path.join(kit.REPO, "data", "garments_3d", garment)
body = os.path.join(d, "body_tpose.obj")
fitted = os.path.join(g, "fitted_%s.obj" % job)
py, cc5 = sys.executable, os.path.join(kit.REPO, "tools", "cc5.py")


def step(label, cmd, timeout=1800):
    print("==", label, flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    out = (r.stdout + r.stderr).strip()
    print("\n".join(l for l in out.splitlines() if not l.startswith("Blender quit")) [-1500:], flush=True)
    if r.returncode:
        sys.exit("FAILED at " + label)


subprocess.run([py, os.path.join(kit.REPO, "tools", "start_cc5.py")])
step("body T-pose", [py, cc5, "run", "cc5/export_body_tpose.py", "job=" + job, "out=" + body])
step("fit in Blender", [kit.BLENDER, "-b", "--python", os.path.join(kit.REPO, "blender", "fit_garment.py"), "--",
                        os.path.join(g, "model.glb"), body, fitted, kind])
step("wear in CC5", [py, cc5, "run", "cc5/wear_garment.py", "job=" + job, "obj=" + fitted,
                     "remove=top" if kind == "top" else "remove=none", "save=" + garment])
print("renders:", os.path.join(d, "garment_T.png"), os.path.join(d, "garment_A.png"),
      fitted[:-4] + "_front.png", fitted[:-4] + "_side.png")
