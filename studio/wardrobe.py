# Pick outfit, hair and new fabric designs for each character, never repeating inside a story and
# avoiding what earlier stories used (data/history.json).
import json, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

POOL = os.path.join(kit.REPO, "data", "outfit_pool.json")
HAIR = os.path.join(kit.REPO, "data", "app_hair_pool.json")
HISTORY = os.path.join(kit.REPO, "data", "history.json")

# Fabric designs (Thai rural, today): pattern x colour. Never plaid on skirts/sarongs, nothing flashy.
PATTERNS = {
    "top_f": ["ผ้าฝ้ายพิมพ์ลายดอกไม้เล็ก", "ผ้าพิมพ์ลายจุดเล็ก", "ผ้าพิมพ์ลายใบไม้เล็ก", "ผ้าฝ้ายพื้นเรียบ",
              "ผ้าลายทางเล็กแนวตั้ง", "ผ้าพิมพ์ลายดอกไม้ใหญ่แบบเสื้อแม่บ้าน", "ผ้าพิมพ์ลายเรขาคณิตเล็ก",
              "ผ้าพิมพ์ลายดอกพิกุลเล็ก", "ผ้าฝ้ายพิมพ์ลายเถาวัลย์เล็ก"],
    "top_m": ["ผ้าฝ้ายพื้นเรียบ", "ผ้ายืดคอตตอนสีพื้นซีด", "ผ้าลายทางเล็กแนวตั้ง", "ผ้าฝ้ายทอมือเนื้อหยาบพื้นเรียบ",
              "ผ้ายืดลายทางขวางเล็ก", "ผ้าฝ้ายฟอกซีดมีรอยซักบ่อย"],
    "top_child": ["ผ้ายืดสีพื้น", "ผ้ายืดลายทางขวาง", "ผ้าพิมพ์ลายดอกไม้เล็ก", "ผ้าพิมพ์ลายจุด", "ผ้ายืดสองสีตัดต่อ"],
    "sarong": ["ผ้าถุงปาเต๊ะลายดอก", "ผ้าถุงปาเต๊ะลายเถาวัลย์", "ผ้าถุงลายไทยโบราณ", "ผ้าซิ่นมัดหมี่",
               "ผ้าซิ่นทอมือลายขวาง", "ผ้าถุงปาเต๊ะลายนกและดอกไม้", "ผ้าถุงลายดอกพิกุล"],
    "trousers": ["ผ้าฝ้ายพื้นเรียบ", "ผ้าลินินเนื้อหยาบพื้นเรียบ", "ผ้ายีนส์ฟอกซีด", "ผ้าฝ้ายลายทางเล็กมาก",
                 "ผ้าหม้อห้อมย้อมคราม", "ผ้าโพลีเอสเตอร์เนื้อเรียบแบบกางเกงแม่ค้า"],
    "shorts": ["ผ้าฝ้ายพื้นเรียบ", "ผ้ายีนส์ฟอกซีด", "ผ้าฝ้ายลายทางเล็ก"],
}
COLORS = ["สีน้ำตาลอ่อน", "สีครีม", "สีฟ้าหม่น", "สีเขียวขี้ม้า", "สีกรมท่า", "สีเทาเข้ม", "สีแดงอิฐ", "สีชมพูกะปิ",
          "สีเหลืองมัสตาร์ดหม่น", "สีม่วงหม่น", "สีเขียวหัวเป็ดหม่น", "สีขาวนวล", "สีส้มอิฐ", "สีน้ำเงินคราม",
          "สีเทาอมเขียว", "สีกากี", "สีเลือดหมู", "สีฟ้าอมเทา"]
CHILD_COLORS = ["สีเหลืองอ่อน", "สีฟ้าสดแบบซักบ่อย", "สีชมพูอ่อน", "สีเขียวใบไม้", "สีส้มอ่อน", "สีแดงหม่น", "สีขาว"]


def _load(path, default):
    try:
        return json.load(open(path, encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def history():
    return _load(HISTORY, {"stories": {}})


def used_before(skip_story):
    h = history()["stories"]
    out = {"hairs": [], "tops": [], "fabrics": []}
    for name, v in h.items():
        if name != skip_story:
            for k in out:
                out[k] += v.get(k, [])
    return out


def remember(story_slug, chars):
    h = history()
    v = {"hairs": [], "tops": [], "fabrics": []}
    for c in chars.values():
        if c.get("hair"):
            v["hairs"].append(c["hair"])
        if len(c.get("outfit", [])) > 1:
            v["tops"].append(c["outfit"][1][0])
        v["fabrics"] += [f[4:] for _, f in c.get("outfit", []) if f and f.startswith("gen:")]
        v["fabrics"] += c.get("fabric_designs", [])
    h["stories"][story_slug] = v
    json.dump(h, open(HISTORY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def _fits(item, sex, group):
    return not item.get("bad") and item["sex"] in ("any", sex) and group in item["ages"]


def _clash(pool, a, b):
    return any({a, b} == set(p) for p in pool.get("clash", []))


def _least_used(options, used, key=lambda x: x):
    """Random among the least used options (used = list with repeats)."""
    if not options:
        return None
    score = {id(o): used.count(key(o)) for o in options}
    best = min(score.values())
    return random.choice([o for o in options if score[id(o)] == best])


def _design(kind, sex, group, taken, before, avoid_colors=()):
    fam = "sarong" if kind == "sarong" else "shorts" if kind == "shorts" else "trousers" if kind == "trousers" else (
        "top_child" if group == "child" else "top_f" if sex == "f" else "top_m")
    colors = CHILD_COLORS + COLORS[:6] if group == "child" else COLORS
    if group == "old":
        colors = [c for c in colors if c not in ("สีชมพูกะปิ",)]
    colors = [c for c in colors if c not in avoid_colors] or colors
    opts = [p if ("คราม" in p or "ยีนส์" in p) else p + " " + c for p in PATTERNS[fam] for c in colors]
    fresh = [o for o in opts if o not in taken] or opts
    return _least_used(fresh, before)


def pick_outfit(sex, group, story_used, before, notes=""):
    """-> outfit list [[spec, fabric|None], ...], layer, designs."""
    pool = _load(POOL, {})
    sex = sex if sex in ("m", "f") else "m"
    if group == "baby":
        full = [i for i in pool["full"] if _fits(i, sex, group)]
        return [[random.choice(full)["spec"], None]], "", []
    bottoms = [b for b in pool["bottoms"] if _fits(b, sex, group)]
    tops = [t for t in pool["tops"] if _fits(t, sex, group)]
    if "ท้อง" in notes:  # loose long top over trousers/sarong
        tops = [t for t in tops if t["spec"] in ("04f1fc", "MO:Painter\\Shirt.ccCloth", "63b0a4")] or tops
    # women: about half in trousers, half in sarong (when both fit the age)
    kinds = sorted({b["kind"] for b in bottoms})
    kind = random.choice(kinds) if kinds else None
    bottoms = [b for b in bottoms if b["kind"] == kind] or bottoms
    bottom = _least_used(bottoms, story_used["bottoms"] + before["tops"], key=lambda b: b["spec"])
    tops = [t for t in tops if not _clash(pool, t["spec"], bottom["spec"])]
    top = _least_used(tops, story_used["tops"] * 3 + before["tops"], key=lambda t: t["spec"])
    shoes = _least_used([s for s in pool["shoes"] if _fits(s, sex, group)], story_used["shoes"], key=lambda s: s["spec"])
    designs, outfit = [], []
    for item, kind_ in ((bottom, bottom["kind"]), (top, "top")):
        fab = None
        if item.get("fabric"):
            d = _design(kind_, sex, group, story_used["fabrics"] + designs, before["fabrics"],
                        [c for c in COLORS + CHILD_COLORS if any(c in x for x in designs)])
            designs.append(d)
            fab = "gen:" + d
        outfit.append([item["spec"], fab])
    if shoes:
        outfit.append([shoes["spec"], None])
    story_used["bottoms"].append(bottom["spec"])
    story_used["tops"].append(top["spec"])
    story_used["shoes"].append(shoes["spec"] if shoes else "")
    story_used["fabrics"] += designs
    return outfit, bottom.get("layer", "out"), designs


def pick_hair(sex, group, story_used, before):
    """-> (hair path, rgb) or (None, None) for babies."""
    if group == "baby":
        return None, None
    p = _load(HAIR, {"hairs": [], "colors": {}})
    sex = sex if sex in ("m", "f") else "m"
    g = "%s_%s" % ("male" if sex == "m" else "female", group)
    if group == "middle":
        g = "male_old" if sex == "m" else "female_adult"
    if group == "old" and sex == "f":
        g = "female_old"
    opts = [h for h in p["hairs"] if g in h["groups"] and not h.get("bad")]
    opts = [h for h in opts if h["path"] not in story_used["hairs"]] or opts
    h = _least_used(opts, before["hairs"], key=lambda h: h["path"])
    story_used["hairs"].append(h["path"])
    color = p["colors"].get({"child": "child", "adult": "adult", "middle": "middle", "old": "old"}[group], [18, 16, 15])
    return h["path"], color


def new_story_used():
    return {"hairs": [], "tops": [], "bottoms": [], "shoes": [], "fabrics": []}
