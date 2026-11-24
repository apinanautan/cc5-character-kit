# Write down how far every render/catalog job got, from the files on disk, so it can be resumed after any stop.
#   python tools\job_state.py        -> runs/wardrobe_scan/state.json  +  runs/wardrobe_scan/RESUME.md (human readable, with the resume command)
# Safe to run at any time (read-only on the data); render_list.py calls it when it ends. Jobs resume by themselves:
# render_list.py skips every batch whose last picture already exists.
import glob, json, os, re, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "runs", "wardrobe_scan")

JOBS = [  # name, candidate list, batch-folder prefix, resume command
    ("ชุดผู้ใหญ่จากโฟลเดอร์ 'เสื้อผ้า' (index 245+)", "cand_adult_cloth.json", "adult_batch", "python tools\\render_adult_rest.py 245 353", 245),
    ("เสื้อผ้า CC5 ที่ติดมากับโปรแกรม (Reallusion Templates)", "cand_cc5_cloth.json", "cc5_batch", "python tools\\render_list.py cand_cc5_cloth.json cc5_batch", 0),
    ("ของเสริมใน Custom", "cand_custom_acc.json", "custacc_batch", "python tools\render_queue.py", 0),
    ("ทรงผมใน Custom", "cand_custom_hair.json", "custhair_batch", "python tools\render_queue.py", 0),
    ("พร็อพใน Custom", "cand_custom_props.json", "custprop_batch", "python tools\render_queue.py", 0),
    ("เสื้อผ้าใน Reallusion Custom (ของที่ผู้ใช้ทำเอง)", "cand_custom_cloth.json", "custom_batch", "python tools\\render_list.py cand_custom_cloth.json custom_batch", 0),
]


def rendered(prefix, lo):
    idx = set()
    for p in glob.glob(os.path.join(S, prefix + "_*", "*.png")):
        m = re.match(r"(\d+)\.png$", os.path.basename(p))
        if m and int(m.group(1)) >= lo and re.search(prefix + r"_\d+_\d+", p):
            idx.add(int(m.group(1)))
    return idx


def catalogued():
    ids = set()
    for f in glob.glob(os.path.join(S, "catalog", "part_*.json")):
        try:
            ids |= {int(r["id"]) for r in json.load(open(f, encoding="utf-8")) if str(r.get("id", "")).isdigit()}
        except Exception:
            pass
    return ids


state = {"updated": time.strftime("%Y-%m-%d %H:%M:%S"), "jobs": []}
md = ["# RESUME — where each job stopped (auto-written by tools\\job_state.py, %s)\n" % state["updated"]]
for name, lst, prefix, cmd, lo in JOBS:
    try:
        total = len(json.load(open(os.path.join(S, lst), encoding="utf-8")))
    except Exception:
        total = 0
    done = rendered(prefix, lo)
    first_missing = next((i for i in range(lo, total) if i not in done), None)
    j = {"name": name, "list": lst, "prefix": prefix, "total": total, "rendered": len(done), "next_index": first_missing,
         "highest_rendered": max(done) if done else None, "resume": cmd}
    state["jobs"].append(j)
    md.append("## %s\n- ทำแล้ว (เรนเดอร์) %d จาก %d (index %d ขึ้นไป)\n- ทำถึง index %s | ต่อที่ index %s\n- วิธีทำต่อ: `%s` (ข้ามล็อตที่ทำแล้วเอง)\n" %
              (name, len(done), total - lo, lo, j["highest_rendered"], j["next_index"], cmd))
cat = catalogued()
state["catalogued_ids_adult_0_244"] = len(cat)
md.append("## แคตตาล็อก (ข้อมูล+ประเภท) ของชุดผู้ใหญ่ index 0–244\n- ทำแล้ว %d แถว (catalog/part_*.json)\n- ที่เรนเดอร์แล้วแต่ยังไม่ทำแคตตาล็อก: ดู index ที่เรนเดอร์แล้วนอกช่วง 0–244 ข้างบน → ใช้ `python tools\\catalog_prep.py prep` แล้วสั่งตัวช่วยอ่านรูปมีป้ายทีละใบ\n" % len(cat))
md.append("## ยังไม่ได้เริ่ม\n- รองเท้า / หมวก / ของเสริม / ทรงผม / ถุงมือ (ทุกโฟลเดอร์), Reallusion Custom ที่ไม่ใช่เสื้อผ้า (ของเสริม 214, รองเท้า 41, ผม 25), !Converted STUFFS (413), ตัวละครสำเร็จ 79, ชุดเด็ก 12\n")
json.dump(state, open(os.path.join(S, "state.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(S, "RESUME.md"), "w", encoding="utf-8").write("\n".join(md))
print(open(os.path.join(S, "RESUME.md"), encoding="utf-8").read())
