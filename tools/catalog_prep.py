# Wardrobe catalog helper (no model needed):
#   python tools\catalog_prep.py prep    -> runs/wardrobe_scan/catalog/labeled/<id>.jpg : latest render of each item, cropped to the
#                                          figure, upscaled to ~900 px tall, with "#id  <file name in the library>" burned in on top
#   python tools\catalog_prep.py check   -> compares every catalog/part_*.json row with the library file name; writes catalog/flags.json
# The label on the picture means that even if a tool returns images out of order, the reader still sees which item it is.
import glob, json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN = os.path.join(ROOT, "runs", "wardrobe_scan")
CAT = os.path.join(SCAN, "catalog")
cand = json.load(open(os.path.join(SCAN, "cand_adult_cloth.json"), encoding="utf-8"))


def latest_render(i):
    fs = glob.glob(os.path.join(SCAN, "adult_batch_*", "%03d.png" % i))
    return max(fs, key=os.path.getmtime) if fs else None


def font(sz):
    for f in ("C:/Windows/Fonts/tahoma.ttf", "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def prep():
    out = os.path.join(CAT, "labeled"); os.makedirs(out, exist_ok=True)
    n = 0
    for i, e in enumerate(cand):
        src = latest_render(i)
        if not src:
            continue
        im = Image.open(src).convert("RGB")
        a = np.asarray(im).astype(int)
        bg = np.median(np.concatenate([a[:8, :8].reshape(-1, 3), a[:8, -8:].reshape(-1, 3), a[-8:, :8].reshape(-1, 3), a[-8:, -8:].reshape(-1, 3)]), axis=0)
        m = np.abs(a - bg).sum(2) > 60
        ys, xs = np.where(m)
        if len(ys) > 200:
            x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
            pad = 12
            im = im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))
        h = 900
        im = im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS)
        bar = Image.new("RGB", (max(im.width, 640), 64), (20, 20, 20))
        d = ImageDraw.Draw(bar)
        name = os.path.basename(e.get("rel") or e.get("path"))
        d.text((8, 6), "#%03d" % i, fill=(255, 220, 80), font=font(26))
        d.text((90, 8), name[:60], fill=(255, 255, 255), font=font(22))
        folder = os.path.basename(os.path.dirname(e.get("rel") or e.get("path")))
        d.text((90, 36), folder[:70], fill=(160, 160, 160), font=font(16))
        canvas = Image.new("RGB", (bar.width, 64 + im.height), (20, 20, 20))
        canvas.paste(bar, (0, 0)); canvas.paste(im, ((bar.width - im.width) // 2, 64))
        canvas.save(os.path.join(out, "%03d.jpg" % i), quality=88)
        n += 1
    print("labeled images:", n, "->", out)


KEYS = [  # (part, English name keywords, Thai words that would contradict-or-confirm)
    ("bottom", r"pant|trouser|jean|short|skirt|sarong|legging|slack|chino", r"กางเกง|กระโปรง|ผ้านุ่ง|ผ้าถุง|โสร่ง|โจง"),
    ("outer", r"coat|jacket|cape|cloak|robe|hoodie|parka|blazer|cardigan", r"โค้ต|แจ็กเก็ต|เสื้อคลุม|ผ้าคลุม|คาร์ดิแกน"),
    ("top", r"shirt|tee|t-shirt|blouse|vest|tank|top|polo|sweater|crop", r"เสื้อ"),
    ("full", r"dress|gown|suit|outfit|jumpsuit|overall|uniform|costume", r"ชุด|เดรส"),
    ("accessory", r"hat|cap|glass|scarf|belt|glove|tie|mask|bag", r"หมวก|แว่น|ผ้าพัน|เข็มขัด|ถุงมือ"),
]


def expect(name):
    low = name.lower()
    hits = [p for p, en, th in KEYS if re.search(en, low)]
    return hits


def check():
    flags, rows = [], []
    for f in sorted(glob.glob(os.path.join(CAT, "part_*.json"))):
        rows += json.load(open(f, encoding="utf-8"))
    for r in rows:
        i = int(r["id"]); e = cand[i]
        fname = os.path.basename(e.get("rel") or e.get("path"))
        exp = expect(fname)
        why = []
        part = r.get("part")
        if exp and part not in exp:
            why.append("part=%s แต่ชื่อไฟล์ '%s' บ่งว่า %s" % (part, fname, "/".join(exp)))
        th = r.get("name_th", "")
        # Thai description must not claim a different garment than the file name
        for p, en, tw in KEYS:
            if exp and p in exp and p == "bottom" and re.search(r"เสื้อโค้ต|แจ็กเก็ต|เสื้อ", th) and not re.search(tw, th):
                why.append("ชื่อไฟล์เป็นกางเกง/กระโปรง แต่คำอธิบายพูดถึงเสื้อ")
            if exp and p in exp and p in ("top", "outer") and re.search(r"กางเกง|กระโปรง", th) and not re.search(r"เสื้อ|โค้ต|แจ็กเก็ต", th):
                why.append("ชื่อไฟล์เป็นเสื้อ แต่คำอธิบายพูดถึงกางเกง/กระโปรง")
        if r.get("verdict") == "ok" and not r.get("reason_th"):
            why.append("ok แต่ไม่มีเหตุผล")
        if why:
            flags.append({"id": r["id"], "file": fname, "name_th": th, "why": why})
    json.dump(flags, open(os.path.join(CAT, "flags.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("rows checked:", len(rows), " flagged:", len(flags))
    for x in flags[:25]:
        print(" ", x["id"], x["file"][:40], "|", x["why"][0][:90])


if __name__ == "__main__":
    {"prep": prep, "check": check}[sys.argv[1]]()
