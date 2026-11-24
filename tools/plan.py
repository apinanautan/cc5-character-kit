# Prepare CC5 jobs from a story file: job folder, face, outfit (+fabric), hair, job.json; then queue them for cc5\build.py.
#   python tools\plan.py <story> [job ...]          e.g.  python tools\plan.py krong krong_urai_40
# story = stories\<story>.json. A job needs face.png first (tools\gen_faces.py, or "head_from" another job).
# Jobs with "head_from" reuse that job's finished head: they are built with load_project on a copy of its .ccProject.
import json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit
from tools.cc5_wardrobe_lock import locked_look, build_load_order
from fabric_onto_garment import make

story = kit.load_story(sys.argv[1])  # name in stories\ or a full .json path
only = set(sys.argv[2:])
write_batch = "--no-batch" not in only
only.discard("--no-batch")
wardrobe = {i["id"]: i["path"] for i in json.load(open(kit.data_file("wardrobe_verified.json"), encoding="utf-8"))["items"]}
pool = json.load(open(kit.data_file("cc5_hair_pool.json"), encoding="utf-8"))
ready = []
for job, c in story["characters"].items():
    if only and job not in only:
        continue
    locked, planned_outfit, planned_hair = locked_look(story, job, c)
    d = os.path.join(kit.JOBS, job)
    os.makedirs(d, exist_ok=True)
    src = c.get("head_from")
    if not src and not os.path.exists(os.path.join(d, "face.png")):
        print("no face yet:", job, "-> python tools\\gen_faces.py", sys.argv[1], job)
        continue
    name = c.get("name") or job
    items, fabrics, sources = [], {}, {}   # sources: staged copy -> library original (build.py deletes the copy)
    ordered = build_load_order(locked, planned_outfit)
    for n, (_, (spec, fab)) in enumerate(ordered):
        path = kit.resolve_item(spec, wardrobe)
        dst = "item%d%s" % (n, os.path.splitext(path)[1])
        shutil.copy(path, os.path.join(d, dst))
        items.append(dst)
        sources[dst] = path
        if fab:
            fabrics[dst] = make(path, os.path.join(kit.FABRICS, fab + ".png"))
    data = {"name": name, "face": "face.png", "body": c.get("body", "neutral"), "items": items, "fabrics": fabrics,
            "out_dir": os.path.join(story["out_dir"], c.get("folder", "")), "morphs": c.get("morphs", {}),
            "layer": c.get("layer", ""), "skin_arm": c.get("skin_arm", "")}
    if c.get("body_preset"):
        from pathlib import Path
        preset = Path(c["body_preset"])
        if preset.suffix.lower() != ".ccavatarpreset" or "Body Morph" not in preset.parts or not preset.is_file():
            raise RuntimeError("A verified CC5 Body Morph preset is required")
        data["body_preset"] = str(preset)
    data["wardrobe_source"] = "story-specific locked wardrobe_design.json"
    data["wardrobe_selection"] = locked["selection_status"]
    data["wardrobe_justification"] = [x[0]["brief_reason"] for x in ordered]
    data["original_asset_paths"] = [x[0]["resolved_source_path"] for x in ordered]
    data["wardrobe_item_order"] = [x[0]["slot"] for x in ordered]
    data["visual_qa"] = "PENDING"
    hair = planned_hair
    if hair:  # named hair from the pool (substring of its path)
        hit = [hair] if os.path.isabs(hair) and os.path.exists(hair) else [h["path"] for h in pool["hairs"] if hair.lower() in h["path"].lower()]
        if not hit:
            raise SystemExit("hair %r not in cc5_hair_pool.json" % hair)
        shutil.copy(hit[0], os.path.join(d, "hair.rlHair"))
        sources["hair.rlHair"] = hit[0]
        data["items"] = ["hair.rlHair"] + items
        data["hair_source"] = hit[0]
        data["hair_rgb"] = c.get("hair_rgb") or pool["colors"].get(c.get("age_group", "adult"), [18, 16, 15])
    if src:  # same person: start from the other job's finished character
        other = os.path.join(kit.JOBS, src)
        oname = story["characters"][src].get("name") or src
        shutil.copy(os.path.join(other, oname + ".ccProject"), os.path.join(d, name + ".ccProject"))
        data["load_project"] = True
    data["sources"] = sources
    json.dump(data, open(os.path.join(d, "job.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if hair is None and c.get("age_group") != "baby" and not src:
        raise RuntimeError("Missing locked hairstyle for "+job+"; random fallback is forbidden")
    for f in ("result.txt", "upper.txt", "layer_fix.txt"):
        if os.path.exists(os.path.join(d, f)):
            os.remove(os.path.join(d, f))
    os.makedirs(data["out_dir"], exist_ok=True)
    ready.append(d)
if write_batch:
    kit.set_batch(ready)
    print(len(ready), "jobs ready ->", kit.BATCH)
else:
    print(len(ready), "jobs ready (no batch file change)")
