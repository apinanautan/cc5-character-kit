"""ONE COMMAND: garment image -> fitted, skin-weighted garment on a CC5 character. No AI hand-fixing needed.

  python make_garment.py --image <garment.png> --run <new run dir> --body <body_tpose.obj>  [--name my_blouse]
  python make_garment.py --image <garment.png> --run <new run dir> --character <char.ccProject> --takeoff <cloth name>

Steps (every step writes new files only, and stops with a clear reason if its automatic check fails):
  0  body       (only with --character) CC5 opens the character, takes off the old top, T-pose, exports body OBJ
  1  hunyuan    Hunyuan3D 2.1 geometry from the image (ComfyUI)                -> hy3d_raw.glb
  2  clean      Blender: fine voxel remesh (closes holes) + decimate to --faces -> clean.glb   CHECK: no holes
  3  place      collar to neck, sleeves on the T-pose arms                       -> placed.obj
  4  tightfit   move/rotate/scale (9 numbers) so the cloth hugs the skin        -> tight.obj
  5  push       Blender 'ball in a tube': shrunk body grows back inside cloth   -> pushed.obj  CHECK: 0% inside
  5b smooth    keep original surface, apply the push smoothed (no sim crinkles) -> final.obj
  6  qc         Blender renders on the body (front/side/back + close-ups)       -> qc_*.png
  7  cc5        CC5: stage, Transfer Skin Weight, pose tests, save character     -> <name>_on_character.ccProject
Use --stop_before cc5 to look at qc_*.png first (CC5 is touched only in steps 0 and 7).
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.3\blender.exe"
STEPS = ["body", "hunyuan", "clean", "place", "tightfit", "push", "qc", "cc5"]


def sh(cmd, step):
    t = time.time(); print(f"\n=== {step} ===", flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = r.stdout + r.stderr
    if r.returncode != 0:
        sys.exit(f"[{step}] FAILED (exit {r.returncode}):\n" + out[-3000:])
    print(f"[{step}] ok {round(time.time() - t)} s"); return out


def blender(script, *args, step):
    return sh([BLENDER, "-b", "--factory-startup", "-P", HERE / "blender" / script, "--", *args], step)


def check(ok, step, why):
    if not ok: sys.exit(f"[{step}] CHECK FAILED: {why}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True); ap.add_argument("--run", required=True)
    ap.add_argument("--body"); ap.add_argument("--character"); ap.add_argument("--takeoff", default="")
    ap.add_argument("--name", default="ai_garment"); ap.add_argument("--faces", type=int, default=100000)
    ap.add_argument("--color", default="0.16,0.36,0.38"); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--stop_before", choices=STEPS, default=None)
    a = ap.parse_args()
    run = Path(a.run).resolve(); run.mkdir(parents=True, exist_ok=True)
    todo = STEPS[:STEPS.index(a.stop_before)] if a.stop_before else STEPS
    f = lambda n: run / n
    body = Path(a.body).resolve() if a.body else f("body_tpose.obj")

    if "body" in todo and a.character:
        sys.path.insert(0, str(HERE)); import cc5call
        r = cc5call.call(str(HERE / "cc5" / "prep_body.py"), dict(source=a.character, out=str(run), upper=a.takeoff,
                         preserve=str(f("scene_before_garment.ccProject"))), timeout=1800)
        check(r["status"] == "ok" and body.exists(), "body", r.get("log", ""))
    check(body.exists(), "body", f"no body OBJ {body} (give --body or --character)")

    if "hunyuan" in todo and not f("hy3d_raw.glb").exists():
        # visualbruno Hunyuan 2.1 node: 512 octree / 30 steps is about 2 min; detail comes back through the normal bake
        out = sh([PY, "hunyuan_vb.py", "--run", run, "--image", a.image, "--seed", a.seed, "--octree", 512,
                  "--steps", 30, "--tag", ""], "hunyuan")
        src = sorted(run.glob(f"hy3d_raw*_o*_s{a.seed}.glb"))[-1]; src.replace(f("hy3d_raw.glb"))

    if "clean" in todo:
        # voxel 0.4% of size closes TRELLIS/Hunyuan holes; poly target is quads -> about half the triangles
        out = blender("quad_remesh2.py", f("hy3d_raw.glb"), f("clean.glb"), 0.004, a.faces // 2, str(f("qc_clean_")) , 0, step="clean")
        line = [l for l in out.splitlines() if l.startswith("decimated")][0]; print(line)
        check("'boundary', 0," in line and "'nonmanifold', 0)" in line, "clean", "mesh still has holes: " + line)

    if "place" in todo:
        sh([PY, "place.py", "--run", run, "--mesh", "clean.glb", "--body", body, "--out", "placed"], "place")
    if "tightfit" in todo:
        sh([PY, "tightfit.py", "--run", run, "--placed", "placed.obj", "--body", body, "--out", "tight"], "tightfit")
        rep = json.load(open(f("tight_report.json")))["after"]; print(rep)
        check(rep["skin_to_cloth_median_cm"] < 2.5, "tightfit", f"cloth too far from the skin {rep}")
    if "push" in todo:
        blender("inflate_push.py", body, f("tight.obj"), f("pushed.obj"), str(f("qc_push_")), step="push")
        rep = json.load(open(f("pushed_report.json"))); print(rep)
        check(rep["inside_after"] < 0.01, "push", f"cloth still inside the body {rep}")
        check(rep["move_max_cm"] < 5.0, "push", f"cloth moved too far, design may be lost {rep}")
        # keep the clean original surface, apply only the smoothed push (the sim itself adds small crinkles)
        sh([PY, "smooth_push.py", "--run", run, "--tight", "tight.obj", "--pushed", "pushed.obj", "--body", body,
            "--out", "final"], "smooth push")
        rep = json.load(open(f("final_report.json"))); print(rep)
        check(rep["inside_final"][0] < 0.01, "smooth push", f"cloth back inside the body after smoothing {rep}")
    if "qc" in todo:
        blender("qc_on_body.py", body, f("final.obj"), str(f("qc_")), step="qc")
        print("look at:", *sorted(run.glob("qc_*.png")), sep="\n  ")
    if "cc5" in todo:
        sys.path.insert(0, str(HERE)); import cc5call
        print("\n=== cc5 ===", flush=True)
        r = cc5call.call(str(HERE / "cc5" / "wear_placed.py"), dict(obj=str(f("final.obj")), out=str(run), name=a.name,
                         color=a.color, remove=a.name), timeout=3600)
        print(r["status"], r.get("log", "")); check(r["status"] == "ok", "cc5", r.get("log", ""))
    print("\nDONE ->", run)


if __name__ == "__main__":
    main()
