# Merge catalog.json + CC5 test results (wardrobe_verify_raw.jsonl) + hand notes (cc5_wardrobe.json)
# into snapgen_data/wardrobe_verified.json.  Presets are kept from the existing file if present.
import json, os

LOCAL = os.environ["LOCALAPPDATA"]
DATA = os.path.join(LOCAL, "Tidmunz Studio", "snapgen_data")
cat = json.load(open(os.path.join(LOCAL, "Tidmunz Studio", "cc5_catalog", "catalog.json"), encoding="utf-8"))["items"]
hand = {os.path.normcase(i["path"]): i for i in json.load(open(os.path.join(DATA, "cc5_wardrobe.json"), encoding="utf-8"))["items"]}
raw = {}
p = os.path.join(DATA, "wardrobe_verify_raw.jsonl")
if os.path.exists(p):
    for line in open(p, encoding="utf-8"):
        r = json.loads(line); raw[r["id"]] = r
outp = os.path.join(DATA, "wardrobe_verified.json")
old = json.load(open(outp, encoding="utf-8")) if os.path.exists(outp) else {}


def slot(v, r):
    if v["kind"] in ("hair", "shoes"):
        return v["kind"]
    k = set(r.get("knocked_off", []))
    if k == {"upper", "lower"}: return "full"
    if k == {"upper"}: return "upper"
    if k == {"lower"}: return "lower"
    z0, z1 = r.get("z", [None, None])
    if z0 is None: return "unknown"
    if z1 < 0.12: return "shoes"
    if z0 > 0.45: return "upper"
    if z1 < 0.62: return "lower"
    return "full_layer"  # covers both but CC5 keeps other pieces (dress/coat on top)


PAIRS = {"upper": ["lower", "shoes", "hair"], "lower": ["upper", "shoes", "hair"],
         "full": ["shoes", "hair"], "full_layer": ["shoes", "hair"], "shoes": ["upper", "lower", "full"],
         "hair": ["upper", "lower", "full", "shoes"]}
items = []
for v in cat.values():
    if v.get("kind") not in ("cloth", "shoes", "hair"):
        continue
    r = raw.get(v["id"], {})
    h = hand.get(os.path.normcase(v["path"]), {})
    status = h.get("status") or {"ok": "loads", "nothing_added": "broken", "missing_file": "broken", "error": "broken"}.get(r.get("load"), "untested")
    s = slot(v, r) if r.get("load") == "ok" else (h.get("part") or "unknown")
    items.append({
        "id": v["id"], "path": v["path"], "file": v["file"],
        "name": h.get("name") or v.get("name_th"),
        "slot": s, "wear_with": PAIRS.get(s, []),
        "gender_guess": v.get("gender"), "age_guess": v.get("age"), "style": v.get("style"), "folk_fit": v.get("folk_fit"),
        "status": status,  # ok (seen on a character) / loads (CC5 test) / broken / rejected / untested
        "cc5_test": {k: r[k] for k in ("load", "knocked_off", "z") if k in r},
        "note": h.get("note") or "",
        "used_by": h.get("used_by", []),
    })
out = {"rules": ["slot มาจากการโหลดจริงใน CC5 (ชนกับเสื้อ/กางเกงอ้างอิงตัวไหน) ไม่ใช่จากรูป",
                 "full = ชุดชิ้นเดียว ใส่คู่กับเสื้อ/กางเกงไม่ได้ (ทับกัน)",
                 "status: ok=ใส่ตัวละครจริงแล้วผ่าน, loads=โหลดขึ้นแต่ยังไม่ดูด้วยตา, broken/rejected=ห้ามใช้",
                 "gender_guess/age_guess มาจากการเดาจากรูป ยังไม่ยืนยัน"],
       "items": sorted(items, key=lambda x: (x["slot"], x["status"], x["file"])),
       "presets": old.get("presets", [])}
json.dump(out, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print(len(items), Counter((i["slot"], i["status"]) for i in items).most_common())
