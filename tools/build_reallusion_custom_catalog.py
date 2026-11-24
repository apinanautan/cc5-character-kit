"""Build an offline, searchable, paged large-thumbnail index of CC5 Custom items.
Run once any time; --watch waits for the renderer to reach verified completion.
Never reads CC5/iClone scenes, modifies source assets or sends notifications.
"""
import html,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'runs'/'wardrobe_scan'
CAT=BASE/'catalog'/'reallusion_custom_catalog.html'
PROGRESS=BASE/'catalog_3_progress.json'
SPECS=[
  ('cloth','เสื้อผ้า Custom','cand_custom_cloth.json','custom_batch'),
  ('acc','ของเสริม Custom','cand_custom_acc.json','custacc_batch'),
  ('prop','พร็อพ Custom','cand_custom_props.json','custprop_batch')
]
def collect():
  rows=[];counts={}
  for kind,title,filename,prefix in SPECS:
    manifest=json.loads((BASE/filename).read_text(encoding='utf-8'))
    pictures={}
    for image in BASE.glob(prefix+'_*/[0-9]*.png'):
      try: n=int(image.stem)
      except ValueError: continue
      if image.stat().st_size<1000:continue
      if n not in pictures or image.stat().st_mtime>pictures[n].stat().st_mtime:
        pictures[n]=image
    counts[kind]={'name':title,'total':len(manifest),'done':sum(i in pictures for i in range(len(manifest))),'skipped':sum(bool(x.get('skip')) for x in manifest)}
    for index,item in enumerate(manifest):
      image=pictures.get(index)
      rows.append(dict(group=kind,id=index,name=item.get('name') or Path(item.get('path','')).stem,
        sub=item.get('part') or '',rel=item.get('rel') or '',skip=bool(item.get('skip')),
        src=os.path.relpath(image,CAT.parent).replace('\\','/') if image else None))
  return rows,counts
def build():
  items,counts=collect()
  state='unknown'
  if PROGRESS.is_file():
    try:state=json.loads(PROGRESS.read_text(encoding='utf-8')).get('state','unknown')
    except Exception:pass
  payload=json.dumps(items,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
  totals=json.dumps(counts,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
  tpl="""<!DOCTYPE html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>แคตตาล็อก Reallusion Custom — CC5</title>
<style>
:root{color-scheme:dark;--bg:#121820;--tile:#222b36;--line:#415064;--tx:#f5f5f5;--mut:#b8c4d1;--accent:#7dd3fc}
*{box-sizing:border-box}body{margin:0;background:var(--bg);font:15px/1.45 Tahoma,Segoe UI,sans-serif;color:var(--tx)}
header{position:sticky;top:0;z-index:9;background:#141c25ef;padding:16px 22px;border-bottom:1px solid var(--line);backdrop-filter:blur(12px)}
h1{font-size:23px;margin:0 0 9px}.small{color:var(--mut);font-size:13px}
#controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:10px}
select,input,button{padding:10px 12px;border-radius:9px;border:1px solid var(--line);background:#293647;color:white;font:inherit}
input{flex:1;min-width:185px}button{cursor:pointer}button:disabled{opacity:.4}button:hover{border-color:var(--accent)}
main{padding:19px 22px}#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:17px}
.card{border:1px solid var(--line);background:var(--tile);border-radius:12px;overflow:hidden}
.thumb{display:flex;align-items:center;justify-content:center;background:#0e141c;height:325px;overflow:hidden}
.thumb img{max-width:100%;max-height:100%;object-fit:contain;cursor:zoom-in}
.card .description{padding:12px 14px}.name{font-weight:700;white-space:nowrap;text-overflow:ellipsis;overflow:hidden}
.meta{color:var(--mut);font-size:12px;margin-top:6px;overflow-wrap:anywhere}
.absent{color:#ffb4a2;padding:14px;text-align:center}.skip{color:#f9df97}
#pager{display:flex;gap:15px;justify-content:center;align-items:center;padding:20px}
#overlay{display:none;position:fixed;inset:0;background:#000e;z-index:20;align-items:center;justify-content:center}
#overlay img{max-width:97vw;max-height:95vh;object-fit:contain}
</style></head><body>
<header><h1>แคตตาล็อก Reallusion Custom — CC5</h1>
<div id="summary" class="small"></div>
<div id="controls"><select id="group"><option value="">ทุกหมวด</option><option value="cloth">เสื้อผ้า Custom</option><option value="acc">ของเสริม Custom</option><option value="prop">พร็อพ Custom</option></select>
<input id="search" placeholder="ค้นหาชื่อ / โฟลเดอร์ / รหัสรายการ">
<select id="only"><option value="">ทุกสถานะ</option><option value="ok">มีภาพแล้ว</option><option value="missing">ยังไม่มีภาพ</option></select>
<span id="counter" class="small"></span></div></header>
<main><section id="grid"></section><nav id="pager">
<button id="previous">ก่อนหน้า</button><span id="page_status"></span><button id="next">ถัดไป</button></nav></main>
<div id="overlay" role="dialog" aria-label="Preview" onclick="this.style.display='none'"><img id="big_image"></div>
<script>
const ITEMS=__ITEMS__;
const COUNTS=__COUNTS__;
const STATE=__STATE__;
const TAKE=48;let page=0;
const group=document.querySelector('#group'),search=document.querySelector('#search'),only=document.querySelector('#only');
const escapeHTML=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const names={cloth:'เสื้อผ้า',acc:'ของเสริม',prop:'พร็อพ'};
document.querySelector('#summary').textContent=Object.values(COUNTS).map(x=>x.name+': '+x.done+'/'+x.total+(x.skipped?' (ข้าม '+x.skipped+')':'')).join('  •  ')+'   |   สถานะ: '+STATE;
function render(){
 const q=search.value.trim().toLocaleLowerCase();
 const filtered=ITEMS.filter(r=>(!group.value||group.value===r.group)&&(!only.value||(only.value==='ok'?!!r.src:!r.src))&&(!q||[r.name,r.sub,r.rel,String(r.id)].join(' ').toLocaleLowerCase().includes(q)));
 const totalPages=Math.max(1,Math.ceil(filtered.length/TAKE));page=Math.min(page,totalPages-1);
 const list=filtered.slice(page*TAKE,(page+1)*TAKE);
 document.querySelector('#grid').innerHTML=list.map(r=>{
  let img=r.src?'<img loading="lazy" src="'+encodeURI(r.src)+'" data-src="'+encodeURI(r.src)+'" alt="'+escapeHTML(r.name)+'">':'<span class="absent '+(r.skip?'skip':'')+'">'+(r.skip?'ข้ามตามรายการต้นทาง':'ยังไม่มีภาพ')+'</span>';
  return '<article class="card"><div class="thumb">'+img+'</div><div class="description"><div class="name">#'+String(r.id).padStart(3,'0')+' '+escapeHTML(r.name)+'</div><div class="meta">'+names[r.group]+' · '+escapeHTML(r.sub)+' · '+escapeHTML(r.rel)+'</div></div></article>';
 }).join('');
 document.querySelectorAll('.thumb img').forEach(el=>el.addEventListener('click',()=>{document.querySelector('#big_image').src=el.dataset.src;document.querySelector('#overlay').style.display='flex'}));
 document.querySelector('#page_status').textContent='หน้า '+(page+1)+' / '+totalPages;
 document.querySelector('#previous').disabled=page===0;
 document.querySelector('#next').disabled=page>=totalPages-1;
 document.querySelector('#counter').textContent=filtered.length+' รายการ';
}
for(const el of [group,only])el.addEventListener('change',()=>{page=0;render()});
search.addEventListener('input',()=>{page=0;render()});
document.querySelector('#previous').addEventListener('click',()=>{if(page){page--;render();window.scrollTo(0,0)}});
document.querySelector('#next').addEventListener('click',()=>{page++;render();window.scrollTo(0,0)});
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelector('#overlay').style.display='none'});
render();
</script></body></html>"""
  output=tpl.replace('__ITEMS__',payload).replace('__COUNTS__',totals).replace('__STATE__',json.dumps(state))
  CAT.parent.mkdir(parents=True,exist_ok=True)
  temp=CAT.with_name(CAT.name+'.tmp')
  temp.write_text(output,encoding='utf-8')
  os.replace(temp,CAT)
  return counts,state
def main():
  mode=sys.argv[1] if len(sys.argv)>1 else '--once'
  if mode not in ('--once','--watch'):raise SystemExit('usage --once | --watch')
  counts,state=build()
  print('HTML_BUILT',CAT,counts,'state',state,flush=True)
  if mode=='--watch':
    while True:
      try:
        j=json.loads(PROGRESS.read_text(encoding='utf-8'))
        if j.get('state') in ('completed','completed_with_failures'):
          counts,state=build()
          print('HTML_FINAL',CAT,counts,'state',state,flush=True)
          break
      except Exception as exc:print('WAIT_RETRY',str(exc)[:120],flush=True)
      time.sleep(40)
if __name__=='__main__':main()