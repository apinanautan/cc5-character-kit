# Run inside Character Creator 5 (Script > Load Python) with ONE Neutral avatar in the scene.
# Loads every cloth/shoes/hair from catalog.json one at a time and records what really happens:
#   loaded?, object names, which reference piece it knocked off (= real CC5 slot), height range on body.
# Results append to snapgen_data/wardrobe_verify_raw.jsonl; rerun = continues where it stopped.
import json, os, time, traceback
import RLPy

LOCAL = os.environ["LOCALAPPDATA"]
CATALOG = os.path.join(LOCAL, "Tidmunz Studio", "cc5_catalog", "catalog.json")
DATA = os.path.join(LOCAL, "Tidmunz Studio", "snapgen_data")
OUT = os.path.join(DATA, "wardrobe_verify_raw.jsonl")
BATCH = 1000  # max items per run

# Known-good reference pieces (from cc5_wardrobe.json, status ok)
wardrobe = json.load(open(os.path.join(DATA, "cc5_wardrobe.json"), encoding="utf-8"))
REF = {}
for it in wardrobe["items"]:
    if it.get("status") == "ok" and it["part"] in ("upper", "lower") and it["part"] not in REF:
        REF[it["part"]] = it["path"]

items = json.load(open(CATALOG, encoding="utf-8"))["items"]
done = set()
if os.path.exists(OUT):
    for line in open(OUT, encoding="utf-8"):
        try:
            done.add(json.loads(line)["id"])
        except Exception:
            pass

avatar = RLPy.RScene.GetAvatars()[0]


def objs():
    return list(avatar.GetClothes()) + list(avatar.GetHairs()) + list(avatar.GetAccessories())


def names():
    return [o.GetName() for o in objs()]


def bounds(o):
    mx, c, mn = RLPy.RVector3(), RLPy.RVector3(), RLPy.RVector3()
    o.GetBounds(mx, c, mn)
    return mn.z, mx.z  # CC is Z-up


def load(path):
    RLPy.RScene.SelectObject(avatar)
    return RLPy.RFileIO.LoadFile(path)


def strip():
    for o in objs():
        RLPy.RScene.RemoveObject(o)


strip()
ref_names = {}
for part, p in REF.items():
    before = set(names()); load(p)
    ref_names[part] = list(set(names()) - before)
try:
    a0, a1 = bounds(avatar)
except Exception:
    a0, a1 = 0.0, 180.0
H = (a1 - a0) or 180.0

IDS = os.path.join(DATA, "cc5_jobs", "verify_ids.txt")
only = set(open(IDS, encoding="utf-8").read().split()) if os.path.exists(IDS) else None
todo = [v for v in items.values() if v["id"] not in done and v.get("kind") in ("cloth", "shoes", "hair") and (only is None or v["id"] in only)]
f = open(OUT, "a", encoding="utf-8")
for v in todo[:BATCH]:
    rec = {"id": v["id"], "file": v["file"], "kind": v["kind"]}
    t = time.time()
    try:
        # make sure both reference pieces are on
        cur = set(names())
        for part, p in REF.items():
            if not set(ref_names[part]) & cur:
                load(p)
        before = set(names())
        if not os.path.exists(v["path"]):
            rec["load"] = "missing_file"
        else:
            load(v["path"])
            after = set(names())
            new = sorted(after - before)
            rec["load"] = "ok" if new else "nothing_added"
            rec["new"] = new
            rec["knocked_off"] = [part for part, ns in ref_names.items() if set(ns) & before and not set(ns) & after]
            rng = []
            for o in objs():
                if o.GetName() in new:
                    try:
                        z0, z1 = bounds(o); rng.append(((z0 - a0) / H, (z1 - a0) / H))
                    except Exception:
                        pass
            if rng:
                rec["z"] = [round(min(r[0] for r in rng), 2), round(max(r[1] for r in rng), 2)]
            for o in objs():
                if o.GetName() in new:
                    RLPy.RScene.RemoveObject(o)
    except Exception:
        rec["load"] = "error"; rec["err"] = traceback.format_exc()[-400:]
    rec["sec"] = round(time.time() - t, 1)
    f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
f.close()
