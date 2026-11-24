# Add a "type" (ประเภทย่อย) to every catalog row from its description + file name (rules only, no model).
#   python tools\catalog_classify.py      (safe to re-run; rewrites only the "type" field of runs/wardrobe_scan/catalog/part_*.json)
import glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "runs", "wardrobe_scan", "catalog")

# (type, regex over name_th + file name) — first match wins inside each part
RULES = {
    "top": [("เสื้อกล้าม/เกาะอก/ครอป", r"กล้าม|เกาะอก|ครอป|crop|tank|bra|สายเดี่ยว|สายบ่า"),
            ("เสื้อสเวตเตอร์/ฮู้ด/คอเต่า", r"สเวตเตอร์|sweater|ฮู้ด|hood|ไหมพรม|คอเต่า|turtle|pullover"),
            ("เสื้อเชิ้ต/มีปก", r"เชิ้ต|shirt(?!s)|ปกแบะ|มีปก|กระดุมหน้า|polo|โปโล|blouse|เบลาส์"),
            ("เสื้อยืด", r"เสื้อยืด|tee|t-shirt|tshirt|แขนสั้น"),
            ("เสื้อแขนยาวทั่วไป", r"แขนยาว|แขนสามส่วน"),
            ("เสื้ออื่นๆ", r".")],
    "outer": [("เสื้อกั๊ก", r"กั๊ก|vest"),
              ("สูท/เบลเซอร์", r"สูท|suit|blazer|เบลเซอร์"),
              ("โค้ต/แจ็กเก็ต", r"โค้ต|coat|แจ็กเก็ต|jacket|parka|bomber"),
              ("เสื้อคลุม/ผ้าคลุม", r"คลุม|cape|cloak|robe|poncho|ผ้าพาด|คาร์ดิแกน"),
              ("เสื้อคลุมอื่นๆ", r".")],
    "bottom": [("กระโปรง", r"กระโปรง|skirt"),
               ("ผ้านุ่ง/โสร่ง/โจงกระเบน", r"ผ้านุ่ง|ผ้าถุง|โสร่ง|โจง|sarong|ผ้าพัน"),
               ("กางเกงขาสั้น", r"ขาสั้น|shorts?\b|สามส่วน|บ็อกเซอร์"),
               ("กางเกงเลกกิง/รัดรูป", r"เลกกิง|legging|รัดรูป|skinny"),
               ("กางเกงยีนส์", r"ยีนส์|เดนิม|jean"),
               ("กางเกงคาร์โก้", r"คาร์โก้|cargo"),
               ("กางเกงขายาว", r"กางเกง|pants?|trouser|ขายาว"),
               ("ท่อนล่างอื่นๆ", r".")],
    "full": [("เดรส", r"เดรส|dress|gown|กระโปรงยาว"),
             ("บอดี้สูท/จั๊มสูท", r"บอดี้สูท|body|จั๊มสูท|jumpsuit|overall|ชุดว่ายน้ำ|bikini|swim"),
             ("ชุดคลุมยาว/ชุดพิธี", r"คลุม|robe|ชุดพิธี|อิหรอม|ihram|ผ้าขาว"),
             ("ชุดสูท/ชุดสองชิ้น", r"สูท|suit|สองชิ้น|set\b"),
             ("ชุดนอน/ชุดชั้นใน", r"ชุดนอน|pajama|nightgown|slip|ชุดชั้นใน|panties"),
             ("ชุดชิ้นเดียวอื่นๆ", r".")],
    "role": [("ชุดตำรวจ/ทหาร/เครื่องแบบ", r"ตำรวจ|police|swat|ทหาร|military|army|เครื่องแบบ|uniform"),
             ("ชุดนักเรียน/นักศึกษา", r"นักเรียน|school|นักศึกษา"),
             ("ชุดแพทย์/พยาบาล", r"พยาบาล|nurse|scrub|หมอ|doctor|surgeon"),
             ("ชุดกู้ชีพ/ไลฟ์การ์ด", r"กู้ชีพ|lifeguard|กู้ภัย"),
             ("ชุดบทบาทอื่นๆ", r".")],
    "accessory": [("หมวก", r"หมวก|hat|cap\b"), ("แว่นตา", r"แว่น|glass"), ("ผ้าพัน/ผ้าพาด", r"ผ้าพัน|ผ้าพาด|scarf|สไบ"),
                  ("เข็มขัด/กระเป๋า", r"เข็มขัด|belt|bag|กระเป๋า"), ("ของเสริมอื่นๆ", r".")],
}
CATEGORY = {"top": "เสื้อ", "outer": "เสื้อคลุม/โค้ต", "bottom": "กางเกง/กระโปรง/ผ้านุ่ง", "full": "ชุดชิ้นเดียว", "role": "ชุดบทบาท",
            "accessory": "ของเสริม", "other": "อื่นๆ"}


def classify(r):
    part = r.get("part", "other")
    text = (r.get("name_th", "") + " " + r.get("orig", "")).lower()
    for t, pat in RULES.get(part, [("อื่นๆ", r".")]):
        if re.search(pat, text):
            return t
    return "อื่นๆ"


n = 0
for f in sorted(glob.glob(os.path.join(CAT, "part_*.json"))):
    rows = json.load(open(f, encoding="utf-8"))
    for r in rows:
        r["type"] = classify(r); r["category"] = CATEGORY.get(r.get("part"), "อื่นๆ"); n += 1
    json.dump(rows, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("classified", n)
