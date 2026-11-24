#!/usr/bin/env python3
"""Create G-drive CC5 hair catalog from original asset metadata and Shell thumbnails.
This tool NEVER opens CC5, copies an asset model, or declares visual QA PASS.
"""
import argparse
import collections
import datetime
import hashlib
import json
import re
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

ROOT=Path(__file__).resolve().parent.parent
OUTPUT=ROOT/"runs"/"hair_catalog_g_20261114"
INDEX=ROOT/"data"/"hair_catalog_external_g.json"
HAIR_EXT={".ccHair".lower(),".rlHair".lower(),".iHair".lower()}
SIGNALS=[
 (("ponytail","pony tail","low pony"),"หางม้า","ทรงรวบหางม้า","รวบ"),
 (("bun","updo","up-do","chignon","topknot"),"มวย/เกล้า","ทรงมวยหรือเกล้าผม","เกล้า"),
 (("braid","plait"),"เปีย","ถักเปียหรือถักเป็นช่อ","ถัก"),
 (("pixie",),"พิกซี","ทรงผมสั้นมาก","สั้น"),
 (("afro",),"แอฟโฟร","ผมหยิกหนาฟู","หยิก"),
 (("bob","a-line"),"บ๊อบ","ทรงบ๊อบรอบหน้าและต้นคอ","สั้น/ประบ่า"),
 (("undercut","buzz","fade","crew cut"),"สั้นไถข้าง","ทรงสั้นไถข้างหรือเกรียน","สั้น"),
 (("slick","swept back","comb back"),"เสยกลับ","เสยผมไปด้านหลัง","สั้น/กลาง"),
 (("side part","side parted","side-part","sidepart"),"แสกข้าง","แสกผมด้านข้าง","สั้น/กลาง"),
 (("center part","middle part","curtain","centre part"),"แสกกลาง","ผมแสกกลาง","กลาง"),
 (("dread","locs"),"เดรดล็อก","ผมแยกเป็นช่อเดรด","ยาว"),
 (("curly","curl"),"ลอนหยิก","ผมหยิกหรือลอนชัด","ไม่ระบุ"),
 (("wavy","wave"),"ลอนคลาย","ผมลอนคลื่น","ไม่ระบุ"),
 (("layered","layer"),"ซอยไล่ระดับ","ผมซอยไล่ระดับ","ไม่ระบุ"),
 (("long",),"ผมยาว","ทรงผมยาว","ยาว"),
 (("short","crop","taper"),"ผมสั้น","ทรงผมสั้น","สั้น")
]
def describe(rel):
    n=rel.stem
    key=n.lower().replace("_"," ").replace("-"," ")
    full=rel.as_posix().lower()
    shape="ยังไม่ระบุ"
    comment="ชื่อไฟล์ยังบอกทรงไม่ชัด ต้องดูภาพพรีวิวและตรวจจริง"
    length="ยังไม่ทราบ"
    for terms,kind,detail,size in SIGNALS:
        if any(term in key for term in terms):
            shape,comment,length=kind,detail,size
            comment="คาดว่า"+comment+"จากชื่อไฟล์ ต้องดูภาพก่อนใช้"
            break
    if re.search(r"(^|[/ _-])(female|women|woman|femail|girls)([/ _-]|$)",full) or re.search(r"hair[_-]?p\d+[_-]?f\d+",full):
        gender="หญิง (คาดจากชื่อ)"
    elif re.search(r"(^|[/ _-])(male|men|man|boys)([/ _-]|$)",full) or re.search(r"hair[_-]?p\d+[_-]?m\d+",full):
        gender="ชาย (คาดจากชื่อ)"
    else:gender="ไม่ระบุ"
    era="ต้องตรวจความเหมาะสมกับยุค"
    if any(x in full for x in ("victorian","medieval","ancient","royal","historical","vintage","classic beauties")):
        era="อาจเป็นทรงย้อนยุค ต้องตรวจภาพและฉาก"
    asset_type="อาจเป็นหนวดหรือคิ้ว" if re.search(r"(beard|brows|eyebrow|facial hairs)",full) else "ทรงผมหลัก (ยังไม่ตรวจ)"
    rights="รอตรวจสิทธิ์ก่อนใช้" if re.search(r"(cracked|crkd)",full) else "ยังไม่ตรวจสิทธิ์"
    return {"name":n,"shape_guess":shape,"description_th":comment,
            "length_guess":length,"gender_guess":gender,"era_review":era,
            "asset_kind":asset_type,"rights_review":rights,
            "visual_qa":"PENDING","cc5_load_qa":"NOT_TESTED",
            "eligible_for_auto_selection":False}
def prepare(source):
    if not source.is_dir():raise FileNotFoundError(source)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    assets=[]
    for file in source.rglob("*"):
        if not file.is_file() or file.suffix.lower() not in HAIR_EXT:continue
        rel=file.relative_to(source)
        stable="G"+hashlib.sha1(rel.as_posix().casefold().encode("utf-8")).hexdigest()[:11]
        stat=file.stat()
        assets.append({"id":stable,"source_path":str(file),"relative_path":rel.as_posix(),
         "pack":rel.parts[0],"file_ext":file.suffix,"file_size_bytes":stat.st_size,
         "modified_local":datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
         "preview_file":"thumbs/"+stable+".jpg","crop_file":"crops/"+stable+".jpg",
         "thumbnail_source":"Windows Shell original asset thumbnail; not CC5 render",
         "thumbnail_native_px":None,"thumbnail_status":"PENDING",**describe(rel)})
    assets.sort(key=lambda x:(x["pack"].casefold(),x["relative_path"].casefold()))
    data={"schema_version":1,"source_root":str(source),"created_local":datetime.datetime.now().isoformat(timespec="seconds"),
          "policy":"Catalog only, original models never copied, all quality checks pending",
          "items":assets}
    (OUTPUT/"manifest.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print("MANIFEST",OUTPUT/"manifest.json","ASSETS",len(assets))
    print("BY_EXT",dict(collections.Counter(x["file_ext"].lower() for x in assets)))
    return data
def build_gallery(data,summary):
    template=r"""<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CC5 · G-drive Hair Catalog</title>
<style>
*{box-sizing:border-box}body{font-family:"Segoe UI",Tahoma,Arial,sans-serif;background:#0f151d;color:#e7f0f8;margin:0}
header{position:sticky;top:0;background:#111a24f7;border-bottom:1px solid #314153;padding:15px 24px;z-index:2}
h1{font-size:22px;margin:0 0 6px}p{color:#a9bcce;font-size:13px;line-height:1.55;margin:5px 0}
.controls{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}input,select{font-size:14px;background:#1a2837;color:white;border:1px solid #425269;padding:10px 12px;border-radius:8px;min-width:155px}
input{flex:1;min-width:210px}.counter{margin:14px 24px;color:#b7c8d9;font-size:13px}
.grid{padding:0 22px 52px;display:grid;grid-template-columns:repeat(auto-fill,minmax(255px,1fr));gap:15px}
.item{display:block;background:#1b2735;border:1px solid #364a60;border-radius:12px;color:inherit;text-align:left;padding:0;cursor:pointer;overflow:hidden}
.item:hover{outline:2px solid #8bb7ee}
.item img{display:block;aspect-ratio:1;object-fit:cover;width:100%;background:#cdd2d8}
.item .blank{aspect-ratio:1;display:grid;place-items:center;color:#c0c7cd;background:#343d47}
.info{padding:12px;display:grid;gap:5px}.name{font-weight:700;font-size:14px;overflow-wrap:anywhere}
.meta{color:#b5c5d4;font-size:12px;line-height:1.45}
.badge{background:#2a3c50;color:#d6e6f6;border-radius:5px;font-size:11px;padding:4px 7px;display:inline-block}
.modal{display:none;position:fixed;inset:0;background:#02080edc;z-index:5;overflow:auto;padding:18px}
.window{max-width:1030px;margin:3vh auto;background:#1b2837;border-radius:14px;border:1px solid #55708b;padding:20px;position:relative}
.close{position:absolute;right:16px;top:12px;background:#334b64;color:white;border:0;border-radius:7px;padding:8px 13px;cursor:pointer}
.photos{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0}
.photos img{width:100%;max-height:500px;object-fit:contain;border-radius:9px;background:#d5dbe0}
.caption{color:#9fb4c9;font-size:12px;margin:6px 0}
.field{margin:7px 0;color:#dce8f4;font-size:13px;line-height:1.6}
.path{word-break:break-all;white-space:pre-wrap;background:#0d1925;border:1px solid #304053;border-radius:7px;padding:12px}
button.copy{border:0;background:#46688a;color:#fff;border-radius:6px;padding:9px 14px;cursor:pointer}
@media(max-width:650px){header{padding:12px}.grid{padding:0 9px 30px;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:9px}.photos{grid-template-columns:1fr}}
</style></head><body>
<header><h1>แคตตาล็อกทรงผม G: สำหรับ CC5</h1>
<p>ภาพ Thumbnail จากไฟล์ต้นฉบับโดยตรง ไม่โหลดทรงผมลงบนหัวตัวละคร ไม่คัดลอกโมเดล ภาพเต็มและครอปเป็นภาพขยายจากต้นฉบับซึ่งบางรายการมีความละเอียดเพียง 125×125 พิกเซล</p>
<p>ข้อมูลรูปทรงจากชื่อเป็นเพียงคำใบ้ ทุกไฟล์ยังต้องตรวจยุค เท็กซ์เจอร์ รูปทรง และการใช้ใน CC5 ก่อนอนุมัติ</p>
<div class="controls">
<input id="q" placeholder="ค้นชื่อทรงผม / กลุ่มแพ็ก / ลักษณะ..." oninput="render()">
<select id="shape" onchange="render()"><option value="">รูปทรงทั้งหมด</option></select>
<select id="gender" onchange="render()"><option value="">เพศทั้งหมด</option></select>
<select id="photo" onchange="render()"><option value="">ภาพทั้งหมด</option><option value="HAS_THUMBNAIL">มี Thumbnail</option><option value="NO_THUMBNAIL">ไม่มี Thumbnail</option></select>
</div></header><div class="counter" id="count"></div><main class="grid" id="grid"></main>
<div id="modal" class="modal" onclick="if(event.target===this)closeDetail()">
<div class="window"><button class="close" onclick="closeDetail()">ปิด ×</button>
<h2 id="title"></h2><div class="photos" id="photos"></div><div id="fields"></div><p>พาธต้นฉบับ (ไม่ถูกคัดลอก):</p><div id="path" class="path"></div>
<button class="copy" onclick="copyPath()">คัดลอกพาธ</button></div></div>
<script>
const ITEMS=__DATA__;
const STATS=__STATS__;
let selected=null;
function el(tag,text,klass){let x=document.createElement(tag);if(text!==null&&text!==undefined)x.textContent=String(text);if(klass)x.className=klass;return x;}
function addOptions(id,vals){let x=document.getElementById(id);[...new Set(vals)].sort((a,b)=>a.localeCompare(b,"th")).forEach(v=>{let o=el("option",v);o.value=v;x.appendChild(o);});}
addOptions("shape",ITEMS.map(x=>x.shape_guess));addOptions("gender",ITEMS.map(x=>x.gender_guess));
function render(){
 let q=document.getElementById("q").value.toLowerCase().trim();
 let s=document.getElementById("shape").value,g=document.getElementById("gender").value,p=document.getElementById("photo").value;
 let rows=ITEMS.filter(x=>(!s||x.shape_guess===s)&&(!g||x.gender_guess===g)&&(!p||x.thumbnail_status===p)&&(!q||(x.name+" "+x.pack+" "+x.description_th+" "+x.relative_path).toLowerCase().includes(q)));
 document.getElementById("count").textContent=rows.length+" / "+ITEMS.length+" ไฟล์ · มี Thumbnail "+STATS.has_thumbnail+" · ยังไม่มี "+STATS.no_thumbnail+" · Visual QA ยังไม่ผ่าน";
 let container=document.getElementById("grid");container.replaceChildren();let frag=document.createDocumentFragment();
 rows.forEach(x=>{let b=el("button",null,"item");b.type="button";b.onclick=()=>showDetail(x);
 if(x.thumbnail_status==="HAS_THUMBNAIL"){let i=el("img");i.src=x.preview_file;i.loading="lazy";i.alt=x.name;b.appendChild(i);}
 else b.appendChild(el("div","ไม่มีภาพตัวอย่าง","blank"));
 let d=el("div",null,"info");d.appendChild(el("div",x.name,"name"));d.appendChild(el("div",x.shape_guess+" · "+x.gender_guess,"meta"));
 d.appendChild(el("div",x.pack,"meta"));d.appendChild(el("div",(x.thumbnail_status==="HAS_THUMBNAIL"?"มีภาพต้นฉบับ":"รอภาพ")+" · รอตรวจ QA","badge"));
 b.appendChild(d);frag.appendChild(b);});container.appendChild(frag);
}
function showDetail(x){selected=x;document.getElementById("title").textContent=x.name;
 let photos=document.getElementById("photos");photos.replaceChildren();
 if(x.thumbnail_status==="HAS_THUMBNAIL"){
   [[x.preview_file,"ภาพเต็ม (ขยายจากต้นฉบับ "+(x.thumbnail_native_px||"?")+")"],[x.crop_file,"ภาพครอปช่วงเส้นผม"]].forEach(pair=>{
    let div=el("div");div.appendChild(el("div",pair[1],"caption"));let img=el("img");img.src=pair[0];div.appendChild(img);photos.appendChild(div);
   });
 }else photos.appendChild(el("p","ไม่มีภาพจริงจากไฟล์นี้ ไม่ควรตัดสินจากชื่ออย่างเดียว"));
 let d=document.getElementById("fields");d.replaceChildren();
 [x.description_th,"กลุ่มทรง: "+x.shape_guess+" | ความยาว: "+x.length_guess,"เพศ: "+x.gender_guess+" | ยุค: "+x.era_review,
 "แพ็ก: "+x.pack+" | ชนิดไฟล์: "+x.file_ext+" | ขนาด "+(x.file_size_bytes/1048576).toFixed(1)+" MB",
 "สิทธิ์ใช้งาน: "+x.rights_review,"คุณภาพ: ยังไม่ผ่าน Visual QA | ยังไม่ลองโหลดใน CC5"].forEach(t=>d.appendChild(el("div",t,"field")));
 document.getElementById("path").textContent=x.source_path;
 document.getElementById("modal").style.display="block";
}
function closeDetail(){document.getElementById("modal").style.display="none";}
function copyPath(){if(!selected)return;if(navigator.clipboard){navigator.clipboard.writeText(selected.source_path).catch(()=>prompt("คัดลอกพาธ",selected.source_path));}else prompt("คัดลอกพาธ",selected.source_path);}
document.addEventListener("keydown",e=>{if(e.key==="Escape")closeDetail()});render();
</script></body></html>"""
    return template.replace("__DATA__",json.dumps(data,ensure_ascii=False,separators=(",",":")).replace("</","<\\/")).replace("__STATS__",json.dumps(summary,ensure_ascii=False))
def make_sheets(items):
    folder=OUTPUT/"sheets";folder.mkdir(exist_ok=True)
    for page,start in enumerate(range(0,len(items),12),1):
        paper=Image.new("RGB",(4*280,3*325),(239,242,245));draw=ImageDraw.Draw(paper)
        for i,x in enumerate(items[start:start+12]):
            tx=i%4*280;ty=i//4*325;source=OUTPUT/x["preview_file"]
            if source.exists():
                with Image.open(source) as photo:
                    im=ImageOps.contain(photo.convert("RGB"),(262,267))
                    paper.paste(im,(tx+(280-im.width)//2,ty+3))
            else:
                draw.rectangle((tx+9,ty+5,tx+271,ty+270),fill=(217,221,226))
                draw.text((tx+25,ty+115),"NO THUMBNAIL",fill=(71,74,77))
            draw.text((tx+8,ty+277),x["name"][:34],fill=(19,25,32))
            draw.text((tx+8,ty+297),x["shape_guess"][:28],fill=(45,53,61))
        paper.save(folder/("sheet_%03d.jpg"%page),"JPEG",quality=81,optimize=True)
    return (len(items)+11)//12
def finalize():
    p=OUTPUT/"manifest.json"
    data=json.loads(p.read_text(encoding="utf-8"))
    by_id={}
    log=OUTPUT/"thumbnail_extract.ndjson"
    if log.exists():
        for line in log.read_text(encoding="utf-8-sig").splitlines():
            try:
                x=json.loads(line);by_id[x["id"]]=x
            except (ValueError,KeyError):pass
    rows=data["items"];counts=collections.Counter()
    for x in rows:
        thumb=OUTPUT/x["preview_file"];crop=OUTPUT/x["crop_file"]
        ok=thumb.is_file() and thumb.stat().st_size>800 and crop.is_file() and crop.stat().st_size>800
        x["thumbnail_status"]="HAS_THUMBNAIL" if ok else "NO_THUMBNAIL"
        status=by_id.get(x["id"],{}).get("status","")
        x["thumbnail_native_px"]=status[3:] if status.startswith("OK:") else None
        x["preview_error"]=None if ok else status or "not extracted"
        counts[x["thumbnail_status"]]+=1
    summary={"total":len(rows),"has_thumbnail":counts["HAS_THUMBNAIL"],"no_thumbnail":counts["NO_THUMBNAIL"],
             "packs":len(set(x["pack"] for x in rows)),
             "file_types":dict(collections.Counter(x["file_ext"].lower() for x in rows)),
             "visual_qa":"ALL_PENDING","auto_selection_enabled":False,
             "generated_local":datetime.datetime.now().isoformat(timespec="seconds")}
    canonical={"schema_version":1,"source_root":data["source_root"],"summary":summary,
               "policy":"External catalog only: do not auto-select or copy models before era, quality, and load QA",
               "items":rows}
    INDEX.write_text(json.dumps(canonical,ensure_ascii=False,indent=2),encoding="utf-8")
    (OUTPUT/"gallery.html").write_text(build_gallery(rows,summary),encoding="utf-8")
    sheet_count=make_sheets(rows)
    readme=("# G-drive CC5 Hair Catalog\n\n"
            + "- Total hair asset files: "+str(len(rows))+"\n"
            + "- Shell thumbnails: "+str(summary["has_thumbnail"])+"/"+str(len(rows))+"\n"
            + "- No thumbnail: "+str(summary["no_thumbnail"])+"\n"
            + "- Preview source: existing Windows Shell / Reallusion content thumbnails, no CC5 scene or model loading\n"
            + "- Large gallery and cropped previews: "+str(OUTPUT/"gallery.html")+"\n"
            + "- Overview contact sheets: "+str(OUTPUT/"sheets")+" ("+str(sheet_count)+" pages)\n"
            + "- Central machine-readable index: "+str(INDEX)+"\n"
            + "- Descriptions inferred from filenames are provisional. Visual and CC5 load QA have NOT been done.\n"
            + "- Do not count material variants as unique verified styles. Rights notes need review.\n")
    (OUTPUT/"README.md").write_text(readme,encoding="utf-8")
    print("FINALIZED",len(rows),"THUMBNAILS",summary["has_thumbnail"],"MISSING",summary["no_thumbnail"],"SHEETS",sheet_count)
    print("GALLERY",OUTPUT/"gallery.html")
    print("DATA",INDEX)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("prepare","finalize"))
    p.add_argument("--source",type=Path)
    a=p.parse_args()
    if a.action=="prepare":
        if not a.source:p.error("--source is required")
        prepare(a.source)
    else:finalize()
if __name__=="__main__":main()
