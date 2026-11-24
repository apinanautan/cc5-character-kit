#!/usr/bin/env python3
"""Read-only search of external G: hair gallery for GPT character art direction.

The output is a shortlist for visual assessment, NOT an automatic asset picker.
Does not load or copy models, invoke CC5, or modify a story.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "hair_catalog_external_g.json"
GALLERY = ROOT / "runs" / "hair_catalog_g_20261114" / "gallery.html"
PREVIEW = ROOT / "runs" / "hair_catalog_g_20261114"

def find(query="", shape="", gender="", pack="", item_id="", limit=20, include_unsafe=False):
    catalog = json.loads(INDEX.read_text(encoding="utf-8-sig"))
    results = []
    tokens = query.casefold().split()
    for row in catalog["items"]:
        if item_id and row["id"] != item_id: continue
        if shape and shape.casefold() not in row["shape_guess"].casefold(): continue
        if gender and gender.casefold() not in row["gender_guess"].casefold(): continue
        if pack and pack.casefold() not in row["pack"].casefold(): continue
        if not include_unsafe and ("ตรวจสิทธิ์ก่อนใช้" in row["rights_review"] or row["asset_kind"] != "ทรงผมหลัก (ยังไม่ตรวจ)"):
            continue
        if not item_id and row["thumbnail_status"] != "HAS_THUMBNAIL":continue
        searchable = " ".join(str(row.get(k,"")) for k in ("name","relative_path","shape_guess","description_th","pack"))
        text=searchable.casefold()
        if any(term not in text for term in tokens): continue
        exact = row["name"].casefold()
        # Score only relevance to human-supplied design, not a universal fashion preference.
        score = sum(6 if t in exact else 3 if t in row["shape_guess"].casefold() else 1 for t in tokens)
        score += 1 if row["thumbnail_native_px"] not in ("125x125","160x160",None) else 0
        results.append((score,row))
    results.sort(key=lambda pair:(-pair[0],pair[1]["name"].casefold(),pair[1]["id"]))
    return [x for _,x in results[:limit]]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("query", nargs="?", default="", help="Search terms; all must match")
    p.add_argument("--shape",default="",help="Thai shape category e.g. บ๊อบ, แสกข้าง, มวย")
    p.add_argument("--gender",default="",help="Gender text; inferred from asset name only")
    p.add_argument("--pack",default="",help="Filter pack name")
    p.add_argument("--id",default="",help="Get an exact asset ID")
    p.add_argument("--limit",type=int,default=20)
    p.add_argument("--include-unsafe",action="store_true",help="Show rights-review / non-hair candidates for audit only")
    p.add_argument("--json",action="store_true",help="Machine-readable results")
    args = p.parse_args()
    if not INDEX.is_file():
        p.error("Catalog missing: build G-drive manifest and thumbnails first")
    if not 1 <= args.limit <= 100:p.error("--limit must be 1..100")
    selected = find(args.query,args.shape,args.gender,args.pack,args.id,args.limit,args.include_unsafe)
    output=[]
    for row in selected:
        output.append({k:row[k] for k in ("id","name","pack","shape_guess","description_th",
             "length_guess","gender_guess","era_review","rights_review",
             "asset_kind","thumbnail_native_px","thumbnail_status",
             "visual_qa","cc5_load_qa","eligible_for_auto_selection","source_path")})
        output[-1]["preview_path"]=str(PREVIEW/row["preview_file"])
        output[-1]["crop_path"]=str(PREVIEW/row["crop_file"])
        output[-1]["has_images"]=(PREVIEW/row["preview_file"]).is_file() and (PREVIEW/row["crop_file"]).is_file()
    if args.json:print(json.dumps({"count":len(output),"gallery":str(GALLERY),"results":output},ensure_ascii=False,indent=2))
    else:
        print("SEARCH_HAIR_CATALOG",len(output),"GALLERY",GALLERY)
        print("PREVIEW=WINDOWS_SHELL, SHAPE_DESCRIPTION=NAME_INFERENCE, VISUAL_QA=PENDING")
        for x in output:
            print(x["id"],x["name"],"|",x["shape_guess"],"|",x["gender_guess"],
                  "|",x["thumbnail_native_px"],"|",x["pack"])
            print("  THUMB",x["preview_path"])
        if not output:print("NO_MATCH — broaden design terms or review the full gallery")
    return 0

if __name__ == "__main__":sys.exit(main())
