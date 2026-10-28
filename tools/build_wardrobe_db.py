# Build data/wardrobe_db.json (ONE wardrobe database) + docs/WARDROBE.md (readable list, no pictures needed).
#   python tools\build_wardrobe_db.py
# Sources: data/base_pool.json (garments), uniform sets, data/fabrics (+ gen/ AI fabrics and their prompts),
# stories/*.json (where each garment / fabric was used). Re-run any time; the program also appends new AI fabrics.
import glob, hashlib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit
from tools.base_chars import BASES, DIR as BASE_DIR

R = kit.REPO
pool = json.load(open(os.path.join(R, "data", "base_pool.json"), encoding="utf-8"))

# detailed shape descriptions (what the garment looks like, independent of its fabric)
SHAPE = {
    "Basic T-shirts": "เสื้อยืดคอกลม แขนสั้นถึงกลางต้นแขน ตัวตรงหลวมเล็กน้อย ยาวคลุมสะโพก ผ้ายืดคอตตอน (แม่แบบ CC5)",
    "V Neck Scrub Shirt_Base": "เสื้อคอวี แขนสั้น ตัวตรงหลวม ไม่มีกระดุม ทรงเสื้อสครับ/เสื้ออยู่บ้าน (Plain Base)",
    "Sleeves Tops_Base": "เสื้อผู้หญิงคอกลมกว้าง แขนสามส่วนเข้ารูป ชายเสื้อปล่อย (Plain Base)",
    "Close_collar_short_sleeves_shirt_Base": "เสื้อเชิ้ตคอปก แขนสั้น ติดกระดุมหน้า (Plain Base) — ไม่ใช้ เพราะมีกระดุม",
    "Slim Jeans": "กางเกงยีนส์ขายาวทรงกระบอกเล็ก สีน้ำเงินฟอก มีลายยีนส์ในตัว (แม่แบบ CC5) — ไม่เปลี่ยนลาย",
    "Slim fit pants": "กางเกงขายาวทรงเข้ารูป ผ้าเรียบ เอวปกติ (แม่แบบ CC5)",
    "Slacks_Base": "กางเกงสแล็คขายาว ทรงตรง มีจีบหน้า เอวคาด (Plain Base)",
    "Cargo Pants_Base": "กางเกงคาร์โก้ขายาว มีกระเป๋าข้างขา ทรงหลวม (Plain Base)",
    "Scrub Pants_Base": "กางเกงขายาวหลวม เอวยางยืด ปลายขาตรง ใส่สบาย คล้ายกางเกงเล/กางเกงอยู่บ้าน (Plain Base)",
    "Knee length skirt": "กระโปรงบานยาวคลุมเข่า ทรงเอ เอวพอดี (แม่แบบ CC5) — ใช้เป็นผ้าถุง/กระโปรงชาวบ้าน",
    "Pencil skirt_Base": "กระโปรงทรงสอบยาวเหนือเข่า เข้ารูป (Plain Base) — ใช้เป็นผ้าถุงสั้น/กระโปรงทำงาน",
    "Canvas Shoes": "รองเท้าผ้าใบหุ้มส้นสีขาวครีม ผูกเชือก (แม่แบบ CC5)",
    "Sport sneakers": "รองเท้าสนีกเกอร์สีขาว (แม่แบบ CC5)",
    "Flip Flops": "รองเท้าแตะหูหนีบ (คลัง Male Outfits/Oahu)",
    "Sandals 02": "รองเท้าแตะรัดส้น (คลัง Male Outfits/Oahu)",
    "Shoes 01": "รองเท้ารัดส้นผู้หญิง (คลัง Dash)",
    "Shoes": "รองเท้าผ้าใบ/หนังลำลอง (คลัง Casual)",
}


def key(spec):
    return os.path.splitext(os.path.basename(spec.replace("\\", "/")))[0]


def source(spec):
    p = kit.resolve_item(spec) if not os.path.isabs(spec) else spec
    s = p.lower()
    return ("แม่แบบ CC5" if "reallusion templates" in s else "Plain Base" if "plain base" in s
            else "ชุด AI ที่ทำเอง" if "_ai" in s or "school_" in os.path.basename(s) else "คลังเสื้อผ้าเดิม")


# where each garment / fabric was used
used_g, used_f = {}, {}
for f in glob.glob(os.path.join(R, "stories", "*.json")):
    s = json.load(open(f, encoding="utf-8-sig"))
    for c in s.get("characters", {}).values():
        who = "%s / %s" % (s.get("title", ""), c.get("name", ""))
        for spec, fab in c.get("outfit", []):
            used_g.setdefault(spec, []).append(who)
            if fab and not fab.startswith("gen:"):
                used_f.setdefault(fab, []).append(who)
        for d in c.get("fabric_designs", []):
            used_f.setdefault("gen/" + hashlib.md5(d.encode("utf-8")).hexdigest()[:10], []).append(who)

garments = []
for kind_name, items in (("top", pool["tops"]), ("bottom", pool["bottoms"]), ("full", pool["full"]), ("shoes", pool["shoes"])):
    for it in items:
        k = key(it["spec"])
        garments.append({
            "id": k, "spec": it["spec"], "type": kind_name, "name": it["name"],
            "shape": SHAPE.get(k, it.get("note", "")), "source": source(it["spec"]),
            "sex": it["sex"], "ages": it["ages"], "retexture": bool(it.get("fabric")),
            "kind": it.get("kind", ""), "layer": it.get("layer", ""),
            "status": "bad" if it.get("bad") else "ok", "used_in": used_g.get(it["spec"], [])})

for it in pool.get("old_thai", []):  # old-Thai pieces (โจงกระเบน ...), tested in CC5, keep their own texture
    garments.append({"id": key(it["spec"]), "spec": it["spec"], "type": it["type"], "name": it["name"],
                     "shape": it["name"] + (" — " + it["note"] if it.get("note") else ""), "source": "คลังเสื้อผ้าเดิม (แนวโบราณ)",
                     "sex": it["sex"], "ages": ["adult", "middle", "old"], "retexture": False, "kind": "old_thai",
                     "layer": "", "status": "bad" if it.get("bad") else "ok", "used_in": used_g.get(it["spec"], [])})

uniforms = [
    {"id": "school_f_secondary", "name": "ชุดนักเรียนหญิงมัธยม (ชุด AI)", "fixed": True,
     "pieces": pool["school"].get("girl_set", []),
     "detail": "เสื้อขาวคอซอง (ปกทหารเรือ) ผูกโบว์กรมท่า แขนพองจีบปลาย + กระโปรงจีบรอบตัวสีกรมท่ายาวคลุมเข่า + ถุงเท้าขาว + รองเท้าหนังดำ",
     "for": "หญิงอายุ 13-18", "used_in": ["จุดหักเหของชีวิต / สุดา วัย 15 ชุดนักเรียน", "จุดหักเหของชีวิต / สุภา ชุดนักเรียน"]},
    {"id": "school_m_secondary", "name": "ชุดนักเรียนชายมัธยม", "fixed": True,
     "pieces": [pool["school"].get("shirt_m", ""), pool["school"].get("trousers_m", ""), pool["school"].get("shoes_m", "")],
     "detail": "เสื้อเชิ้ตขาวแขนสั้น (ผ้าขาวเรียบ) + กางเกงขายาวกรมท่า + รองเท้าหนังดำ",
     "for": "ชายอายุ 13-18", "used_in": ["จุดหักเหของชีวิต / สมโชค ชุดนักเรียน"]},
]

# whole characters kept as bases (uniforms, workers): take the whole avatar, swap the head
bases = [{"file": os.path.join(BASE_DIR, f), "group": g, "for": a, "detail": d,
          "ok": os.path.exists(os.path.join(BASE_DIR, f))} for f, g, a, d, _ in BASES]

# fabrics: hand-made library + AI-made (description from the prompt saved next to it, or from the story)
desc_of = {}
for f in glob.glob(os.path.join(R, "stories", "*.json")):
    for c in json.load(open(f, encoding="utf-8-sig")).get("characters", {}).values():
        for d in c.get("fabric_designs", []):
            desc_of["gen/" + hashlib.md5(d.encode("utf-8")).hexdigest()[:10]] = d
fabrics = []
for p in sorted(glob.glob(os.path.join(kit.FABRICS, "*.png")) + glob.glob(os.path.join(kit.FABRICS, "gen", "*.png"))):
    rel = os.path.relpath(p, kit.FABRICS).replace("\\", "/")[:-4]
    if rel.startswith("_") or rel.endswith("_raw"):
        continue
    txt = os.path.join(os.path.dirname(p), os.path.basename(rel) + "_raw.txt")
    side = p[:-4] + ".txt"  # written by studio/fabric_ai.py for every new AI fabric
    d = open(side, encoding="utf-8").read().strip() if os.path.exists(side) else desc_of.get(rel)
    if not d and os.path.exists(txt):
        m = re.search(r"Requested surface: ([^.]*?)(?: แบบเสื้อผ้าคนไทย|\.)", open(txt, encoding="utf-8", errors="ignore").read())
        d = m.group(1).strip() if m else None
    if not d:
        d = {"school_white": "ผ้าขาวเรียบ ชุดนักเรียนใหม่", "school_white_old": "ผ้าขาวหม่นออกเหลือง ชุดนักเรียนเก่า"}.get(rel, rel.replace("_", " "))
    use = "ผ้าถุง/กระโปรง" if any(w in d for w in ("ผ้าถุง", "ซิ่น", "pha_thung", "pha_sin")) else \
          "กางเกง" if any(w in d for w in ("ยีนส์", "กางเกง", "ลินิน", "โพลีเอสเตอร์")) else "เสื้อ/ทั่วไป"
    fabrics.append({"id": rel, "file": "data/fabrics/" + rel + ".png", "desc": d, "use": use,
                    "source": "AI" if rel.startswith("gen/") else "คลังผ้าเดิม",
                    "avoid": "plaid" in rel, "used_in": used_f.get(rel, [])})

db = {"note": "ฐานข้อมูลเสื้อผ้า+ลายผ้า (สร้างโดย tools/build_wardrobe_db.py). garments = ทรงที่เปลี่ยนลายได้; "
              "uniforms = ชุดตายตัว (ชุดนักเรียน ฯลฯ) ใช้ทั้งชุดไม่เปลี่ยนลาย; fabrics = ลายผ้าที่มีแล้ว ใช้ซ้ำก่อนสร้างใหม่",
      "garments": garments, "uniforms": uniforms, "base_characters": bases, "fabrics": fabrics,
      # compatibility with studio/wardrobe.py (same shape as base_pool.json)
      "tops": pool["tops"], "bottoms": pool["bottoms"], "full": pool["full"], "shoes": pool["shoes"],
      "clash": pool.get("clash", []), "school": pool["school"]}
json.dump(db, open(os.path.join(R, "data", "wardrobe_db.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# readable list
L = ["# คลังเสื้อผ้า (สร้างอัตโนมัติจาก data/wardrobe_db.json — อย่าแก้ไฟล์นี้ตรงๆ)", "",
     "## 1. ชุดตายตัว (ใช้ทั้งชุด ไม่เปลี่ยนลาย)", "", "| ชุด | รายละเอียด | ใช้กับ | เคยใช้ |", "|---|---|---|---|"]
for u in uniforms:
    L.append("| %s | %s | %s | %s |" % (u["name"], u["detail"], u["for"], ", ".join(u["used_in"]) or "-"))
L += ["", "### ตัวละครเบสทั้งตัว (`%s`)" % BASE_DIR, "", "| ไฟล์ | กลุ่ม | เพศ/วัย | ชุด |", "|---|---|---|---|"]
L += ["| %s | %s | %s | %s |" % (os.path.basename(b["file"]), b["group"], b["for"], b["detail"]) for b in bases]
L += ["", "## 2. ทรงเสื้อผ้า (เปลี่ยนลายผ้าได้ = ไม่ซ้ำ)", "",
      "| ประเภท | ชื่อ | รูปทรง | ที่มา | เพศ/วัย | เปลี่ยนลาย | สถานะ | ใช้ไปแล้ว |", "|---|---|---|---|---|---|---|---|"]
T = {"top": "เสื้อ", "bottom": "ล่าง", "full": "ชุดเต็มตัว", "shoes": "รองเท้า"}
sx = {"m": "ชาย", "f": "หญิง", "any": "ทุกเพศ"}
for g in garments:
    L.append("| %s | %s | %s | %s | %s %s | %s | %s | %d ครั้ง |" % (
        T[g["type"]], g["name"], g["shape"] or "-", g["source"], sx.get(g["sex"], g["sex"]), "/".join(g["ages"]),
        "ได้" if g["retexture"] else "ไม่", "ห้ามใช้" if g["status"] == "bad" else "ใช้ได้", len(g["used_in"])))
L += ["", "## 3. ลายผ้าที่มีแล้ว (%d ลาย — ใช้ซ้ำก่อนให้ AI สร้างใหม่)" % len(fabrics), "",
      "| ไฟล์ | ลาย | เหมาะกับ | ที่มา | ใช้ไปแล้ว |", "|---|---|---|---|---|"]
for f in sorted(fabrics, key=lambda x: (x["use"], x["desc"])):
    L.append("| `%s` | %s%s | %s | %s | %d |" % (f["id"], f["desc"], " ⚠️ไม่ใช้ (ลายสก็อต)" if f["avoid"] else "",
                                              f["use"], f["source"], len(f["used_in"])))
open(os.path.join(R, "docs", "WARDROBE.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("garments %d, uniforms %d, fabrics %d" % (len(garments), len(uniforms), len(fabrics)))
