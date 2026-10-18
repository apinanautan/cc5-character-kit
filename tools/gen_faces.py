# Generate AI face photos for a story's characters (one at a time, skips jobs that already have face.png).
#   python tools\gen_faces.py <story> [job ...]
# Needs Tidmunz Studio OPEN (faces go through its Chrome / ChatGPT; closed program = "token_revoked").
# Uses the program's own Story Face prompt builder; story character "face" = fields for it (+ "ref": job to look alike).
import ast, json, os, shutil, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

P = kit.PROGRAM
sys.path[:0] = [P, os.path.join(P, "snapgen_modules")]
src = open(os.path.join(P, "snapgen_gui_v2.py"), encoding="utf-8").read()
fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "_build_story_face_prompt_from_character")
ns = {}
exec(ast.get_source_segment(src, fn), ns)
build = ns["_build_story_face_prompt_from_character"]
from snapgen_image_gen import generate_image

story = kit.load_story(sys.argv[1])
only = set(sys.argv[2:])
face_dir = os.path.join(kit.JOBS, "_faces")
os.makedirs(face_dir, exist_ok=True)
for job, c in story["characters"].items():
    if (only and job not in only) or "face" not in c:
        continue
    d = os.path.join(kit.JOBS, job)
    os.makedirs(d, exist_ok=True)
    if os.path.exists(os.path.join(d, "face.png")):
        continue
    fields = {k: v for k, v in c["face"].items() if k not in ("prompt_name", "ref")}
    try:
        prompt = build(dict(fields, name=c["face"].get("prompt_name", c.get("name", job))))
        refs = None
        ref = c["face"].get("ref")
        if ref and os.path.exists(os.path.join(kit.JOBS, ref, "face.png")):
            refs = [os.path.join(kit.JOBS, ref, "face.png")]
            prompt = "Same person as the reference photo, aged as described. " + prompt
        p = generate_image(prompt, output_dir=face_dir, name_hint=job + "_face", aspect_ratio="3:4",
                           ref_images=refs, use_story_face_history=True)
        shutil.copy(p, os.path.join(d, "face.png"))
        print("OK", job, flush=True)
    except Exception:
        print("FAIL", job, traceback.format_exc()[-300:], flush=True)
