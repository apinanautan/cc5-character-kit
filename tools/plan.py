# Prepare CC5 jobs from a story file: job folder, face, outfit (+fabric), hair, job.json; then queue them for cc5\build.py.
#   python tools\plan.py <story> [job ...]          e.g.  python tools\plan.py krong krong_urai_40
# story = stories\<story>.json. A job needs face.png first (tools\gen_faces.py, or "head_from" another job).
# Jobs with "head_from" reuse that job's finished head: they are built with load_project on a copy of its .ccProject.
import json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit
from fabric_onto_garment import make

story = kit.load_story(sys.argv[1])  # name in stories\ or a full .json path
only = set(sys.argv[2:])
wardrobe = {i["id"]: i["path"] for i in json.load(open(kit.data_file("wardrobe_verified.json"), encoding="utf-8"))["items"]}
pool = json.load(open(kit.data_file("cc5_hair_pool.json"), encoding="utf-8"))
ready = []
for job, c in story["characters"].items():
    if only and job not in only:
        continue
    d = os.path.join(kit.JOBS, job)
    os.makedirs(d, exist_ok=True)
    src = c.get("head_from")
    if not src and not os.path.exists(os.path.join(d, "face.png")):
        print("no face yet:", job, "-> python tools\\gen_faces.py", sys.argv[1], job)
        continue
    name = c.get("name") or job
    items, fabrics = [], {}
    for n, (spec, fab) in enumerate(c["outfit"]):
        path = kit.resolve_item(spec, wardrobe)
        dst = "item%d%s" % (n, os.path.splitext(path)[1])
        shutil.copy(path, os.path.join(d, dst))
        items.append(dst)
        if fab:
            fabrics[dst] = make(path, os.path.join(kit.FABRICS, fab + ".png"))
    data = {"name": name, "face": "face.png", "body": c.get("body", "neutral"), "items": items, "fabrics": fabrics,
            "out_dir": os.path.join(story["out_dir"], c.get("folder", "")), "morphs": c.get("morphs", {}),
            "layer": c.get("layer", ""), "skin_arm": c.get("skin_arm", "")}
    hair = c.get("hair")
    if hair:  # named hair from the pool (substring of its path)
        hit = [hair] if os.path.isabs(hair) and os.path.exists(hair) else [h["path"] for h in pool["hairs"] if hair.lower() in h["path"].lower()]
        if not hit:
            raise SystemExit("hair %r not in cc5_hair_pool.json" % hair)
        shutil.copy(hit[0], os.path.join(d, "hair.rlHair"))
        data["items"] = ["hair.rlHair"] + items
        data["hair_source"] = hit[0]
        data["hair_rgb"] = c.get("hair_rgb") or pool["colors"].get(c.get("age_group", "adult"), [18, 16, 15])
    if src:  # same person: start from the other job's finished character
        other = os.path.join(kit.JOBS, src)
        oname = story["characters"][src].get("name") or src
        shutil.copy(os.path.join(other, oname + ".ccProject"), os.path.join(d, name + ".ccProject"))
        data["load_project"] = True
    json.dump(data, open(os.path.join(d, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if hair is None and c.get("age_group") != "baby" and not src:  # no hair given -> random pick (needs Tidmunz Studio)
        subprocess.run([sys.executable, os.path.join(kit.PROGRAM, "snapgen_modules", "cc5", "cc5_pick_hair.py"),
                        d, c["sex"], c.get("age_group", "adult")], check=True)
    for f in ("result.txt", "upper.txt", "layer_fix.txt"):
        if os.path.exists(os.path.join(d, f)):
            os.remove(os.path.join(d, f))
    os.makedirs(data["out_dir"], exist_ok=True)
    ready.append(d)
kit.set_batch(ready)
print(len(ready), "jobs ready ->", kit.BATCH)
