# Build runs/wardrobe_scan/catalog/catalog.html: one self-contained gallery page (filters + search), images relative.
#   python tools\catalog_html.py
import glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "runs", "wardrobe_scan", "catalog")
rows = {}
for f in sorted(glob.glob(os.path.join(CAT, "part_*.json"))):
    for r in json.load(open(f, encoding="utf-8")):
        rows[r["id"]] = r
items = [rows[k] for k in sorted(rows)]
for r in items:
    r["img"] = ("images/%s.jpg" % r["id"]) if os.path.exists(os.path.join(CAT, "images", r["id"] + ".jpg")) else ("labeled/%s.jpg" % r["id"])
data = json.dumps(items, ensure_ascii=False)
html = """<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>แคตตาล็อกเสื้อผ้า CC5</title>
<style>
:root{--bg:#16181c;--card:#20232a;--tx:#e8e8e8;--mut:#9aa0a6;--ok:#2fb344;--fix:#e3a008;--no:#d64545}
@media (prefers-color-scheme: light){:root{--bg:#f4f5f7;--card:#fff;--tx:#1b1d21;--mut:#60646b}}
body{margin:0;background:var(--bg);color:var(--tx);font:14px/1.4 "Segoe UI",Tahoma,sans-serif}
header{position:sticky;top:0;background:var(--bg);padding:10px 16px;border-bottom:1px solid #8884;z-index:5;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
select,input{background:var(--card);color:var(--tx);border:1px solid #8886;border-radius:6px;padding:6px 8px;font:inherit}
#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;padding:16px}
.c{background:var(--card);border-radius:10px;overflow:hidden;border:2px solid transparent}
.c.ok{border-color:var(--ok)}.c.fixable{border-color:var(--fix)}.c.no{border-color:var(--no);opacity:.8}
.c img{width:100%;height:260px;object-fit:contain;background:#0006;display:block;cursor:zoom-in}
.c div{padding:8px 10px}.n{font-weight:600}.m{color:var(--mut);font-size:12px;margin-top:2px}
.b{display:inline-block;border-radius:4px;padding:0 6px;font-size:11px;margin-right:4px;background:#8884}
#cnt{color:var(--mut)}#big{display:none;position:fixed;inset:0;background:#000d;z-index:9;align-items:center;justify-content:center}#big img{max-height:96vh;max-width:96vw}
</style></head><body>
<header><b>แคตตาล็อกเสื้อผ้า CC5</b>
<select id="part"><option value="">ทุกหมวด</option></select>
<select id="type"><option value="">ทุกประเภท</option></select>
<select id="verdict"><option value="">ทุกผล</option><option value="ok">ใช้ได้เลย</option><option value="fixable">ใช้ได้ถ้าแก้/เฉพาะแนว</option><option value="no">ใช้ไม่ได้</option></select>
<select id="era"><option value="">ทุกแนวเรื่อง</option></select>
<select id="sex"><option value="">ทุกเพศ</option><option value="m">ชาย</option><option value="f">หญิง</option></select>
<input id="q" placeholder="ค้นหา เช่น เชิ้ต กางเกง ขาว"><span id="cnt"></span></header>
<div id="grid"></div><div id="big" onclick="this.style.display='none'"><img id="bi"></div>
<script>
const D=__DATA__;
const VT={ok:"ใช้ได้เลย",fixable:"แก้ได้/เฉพาะแนว",no:"ใช้ไม่ได้"};
const PT={top:"เสื้อ",bottom:"กางเกง/กระโปรง",full:"ชุดชิ้นเดียว",outer:"เสื้อคลุม",accessory:"ของเสริม",role:"ชุดบทบาท",other:"อื่นๆ"};
const ET={folk_old:"ชาวบ้านโบราณ",rural_modern:"ชนบทร่วมสมัย",urban_modern:"คนเมืองปัจจุบัน",role_uniform:"เครื่องแบบ",costume:"แต่งกายพิเศษ"};
const uniq=a=>[...new Set(a)];
for(const t of uniq(D.map(r=>r.type||"")).sort())if(t)type.add(new Option(t,t));
for(const p of uniq(D.map(r=>r.part)))part.add(new Option(PT[p]||p,p));
for(const e of uniq(D.flatMap(r=>r.eras||[])))era.add(new Option(ET[e]||e,e));
function esc(s){return String(s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
function draw(){
 const q=document.getElementById("q").value.toLowerCase();
 const L=D.filter(r=>(!part.value||r.part==part.value)&&(!type.value||r.type==type.value)&&(!verdict.value||r.verdict==verdict.value)&&(!era.value||(r.eras||[]).includes(era.value))&&(!sex.value||r.sex==sex.value||r.sex=="any")&&(!q||(r.name_th+r.orig+(r.good_for||"")+(r.reason_th||"")).toLowerCase().includes(q)));
 cnt.textContent=L.length+" / "+D.length+" ชิ้น";
 grid.innerHTML=L.map(r=>`<div class="c ${r.verdict}"><img loading="lazy" src="${r.img}" onclick="bi.src=this.src;big.style.display='flex'"><div><div class="n">#${r.id} ${esc(r.name_th)}</div>
 <div class="m"><span class="b">${VT[r.verdict]}</span><span class="b">${r.type||PT[r.part]||r.part}</span><span class="b">${r.sex}</span></div>
 <div class="m">${esc(r.reason_th)}</div><div class="m">${(r.eras||[]).map(e=>ET[e]||e).join(" · ")}</div><div class="m">${esc(r.orig)}</div></div></div>`).join("");
}
[part,type,verdict,era,sex,document.getElementById("q")].forEach(e=>e.addEventListener("input",draw));draw();
</script></body></html>""".replace("__DATA__", data)
open(os.path.join(CAT, "catalog.html"), "w", encoding="utf-8").write(html)
print("wrote catalog.html with", len(items), "items")
