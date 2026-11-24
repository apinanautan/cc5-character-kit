# Look things up in the wardrobe catalog WITHOUT opening any picture (one short line per item).
#   python tools\wardrobe_find.py --part top --sex m --verdict ok,fixable --era urban_modern --q เชิ้ต --limit 15
#   python tools\wardrobe_find.py --show 231        (full row: library path, description, reasons, image file)
#   python tools\wardrobe_find.py --stats           (counts by part / verdict / era)
# Data: runs/wardrobe_scan/catalog/part_*.json  (+ images/<id>.jpg, labeled/<id>.jpg)
import argparse, collections, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "runs", "wardrobe_scan", "catalog")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load():
    rows = {}
    for f in sorted(glob.glob(os.path.join(CAT, "part_*.json"))):
        for r in json.load(open(f, encoding="utf-8")):
            rows[r["id"]] = r
    return [rows[k] for k in sorted(rows)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part"); ap.add_argument("--type", help="ประเภทย่อย เช่น เสื้อเชิ้ต/มีปก, เดรส, กางเกงขายาว (ค้นบางส่วนของคำได้)"); ap.add_argument("--sex"); ap.add_argument("--age"); ap.add_argument("--era")
    ap.add_argument("--verdict", help="ok,fixable,no (comma list)"); ap.add_argument("--q", help="keyword in name/file/good_for")
    ap.add_argument("--limit", type=int, default=20); ap.add_argument("--show"); ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    rows = load()
    if a.show:
        for r in rows:
            if r["id"] == a.show.zfill(3):
                for k, v in r.items():
                    print("%s: %s" % (k, v))
                print("image file:", os.path.join(CAT, r.get("image", "")))
        return
    if a.stats:
        print("type", dict(collections.Counter(r.get("type") for r in rows)))
        for key in ("part", "verdict"):
            print(key, dict(collections.Counter(r.get(key) for r in rows)))
        print("era", dict(collections.Counter(e for r in rows for e in r.get("eras", []))))
        print("total", len(rows)); return
    vs = a.verdict.split(",") if a.verdict else None
    out = []
    for r in rows:
        if a.part and r.get("part") != a.part: continue
        if a.type and a.type not in r.get("type", ""): continue
        if a.sex and r.get("sex") not in (a.sex, "any"): continue
        if a.age and a.age not in r.get("ages", []): continue
        if a.era and a.era not in r.get("eras", []): continue
        if vs and r.get("verdict") not in vs: continue
        if a.q and a.q.lower() not in (r.get("name_th", "") + r.get("orig", "") + r.get("good_for", "") + r.get("reason_th", "")).lower(): continue
        out.append(r)
    for r in out[:a.limit]:
        print("%s | %s | %s | %s | %s | %s" % (r["id"], r["verdict"], r.get("type", r.get("part")), r.get("sex"), r.get("name_th", "")[:60], r.get("orig", "")[:30]))
    print("-- %d matches (showing %d)" % (len(out), min(len(out), a.limit)))


main()
