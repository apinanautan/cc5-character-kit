"""Make visual, non-random CC5 outfit catalog for user's current story. Read-only source meshes."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import os,json,re,collections,shutil,html
ROOT=Path(__file__).resolve().parents[1]
SCAN=ROOT/'runs'/'wardrobe_scan'
DEST=ROOT/'runs'/'chai_chana_khon_mai_yom_phae_sister2_scoop_v11'/'wardrobe_catalog'
GOOGLE=Path.home()/'Desktop'/'ชัยชนะของคนไม่ยอมแพ้'/'ไฟล์ทำงานภายใน_ไม่อัปขึ้นDrive'/'แค็ตตาล็อกชุด_เลือกจากรูป'
assert os.environ.get('COMPUTERNAME','').upper()=='DESKTOP-F1PJT4S'
assert GOOGLE.parent.is_dir()
assert not DEST.exists(),'Catalog already exists, do not overwrite'
catfiles={c:json.loads((SCAN/f'cand_{c}_cloth.json').read_text(encoding='utf-8-sig')) for c in ('adult','custom','cc5')}
banned_terms=r'underwear|lingerie|bikini|swim|pajama|pyjama|sleepwear|nightwear|nightgown|medieval|cosplay|fantasy|armor|armour|sci.?fi|cyber|soldier|tactical|police|uniform|doctor|surgeon|nurse|school|military|robe|gown|dress|skirt|corset|bra\b|โจง|สไบ|กระโปรง|ผ้าถุง|ชุดนอน|นักเรียน|พยาบาล|สูทแฟนซี'
known_broken={'MonteCarlo_Shirt.ccCloth','sco.ccCloth','reddy.ccCloth','Sweater.ccCloth'}
fontfile=Path(r'C:\Windows\Fonts\tahoma.ttf')
ft=ImageFont.truetype(str(fontfile),15) if fontfile.is_file() else ImageFont.load_default()
hft=ImageFont.truetype(str(fontfile),22) if fontfile.is_file() else ft
rows=[];images={};counts=collections.Counter()
for tag,data in [('A',catfiles['adult']),('C',catfiles['custom']),('N',catfiles['cc5'])]:
 source={'A':'adult','C':'custom','N':'cc5'}[tag]
 previews={}
 for f in SCAN.glob(source+'_batch_*/*.png'):
  if not f.stem.isdigit():continue
  idx=int(f.stem)
  if idx not in previews or f.stat().st_mtime>previews[idx].stat().st_mtime:previews[idx]=f
 for i,x in enumerate(data):
  path=Path(x['path'])
  rel=x.get('rel','');name=x.get('name',path.stem)
  text=(str(rel)+' '+name).lower()
  first=rel.replace('/','\\').split('\\')[0].lower()
  if tag=='A':
   part=x.get('part')
  else:
   if '\\shirts\\' in text or '\\tops\\' in text or first=='shirts':part='top'
   elif '\\pants\\' in text or '\\trousers\\' in text or first=='pants':part='bottom'
   else:part='unknown'
   if part=='unknown':
    if re.search(r'(shirt|blouse|polo|sweater|tee|(^|[ _])top($|[ ._])|เสื้อ)',name.lower()):part='top'
    elif re.search(r'(trouser|pant|jean|slack|shorts?|กางเกง)',name.lower()):part='bottom'
  if part not in ('top','bottom'):continue
  why=[]
  if re.search(banned_terms,text,re.I):why.append('ผิดยุค/ชุดนอน/ชุดอื่น')
  if path.name in known_broken:why.append('เคยใส่แล้ว Mesh เสียหรือเสื้อผ้าหาย')
  if not path.is_file():why.append('ไฟล์ต้นทางไม่พบ')
  pv=previews.get(i)
  if pv is None:why.append('ไม่มีรูปตัวอย่างจริง')
  category=('เสื้อ' if part=='top' else 'กางเกง')
  code=f'{tag}{i:03d}'
  row={'id':code,'source_group':source,'source_index':i,'category':category,'name':name,
       'part':part,'file':str(path),'original_rel':rel,'sex_hint':x.get('gender'),
       'preview':bool(pv),'excluded':bool(why),
       'why_excluded':why,'selection':'NOT_APPROVED','cc5_fit':'NOT_TESTED'}
  rows.append(row);counts[(category,'excluded' if why else 'candidate')]+=1
  if pv and not why:images[code]=pv
assert len(rows)>200 and len(images)>100,(len(rows),len(images))
DEST.mkdir(parents=True);(DEST/'images').mkdir()
for row in rows:
 id=row['id']
 if id not in images:continue
 f=images[id]
 with Image.open(f) as im:
  im=im.convert('RGB');im.thumbnail((220,280),Image.Resampling.LANCZOS)
  thumb=Image.new('RGB',(230,286),(34,42,50))
  thumb.paste(im,((230-im.width)//2,(286-im.height)//2))
  thumb.save(DEST/'images'/(id+'.jpg'),'JPEG',quality=64,optimize=True)
pages=[]
for category in ['เสื้อ','กางเกง']:
 entries=[x for x in rows if x['id'] in images and x['category']==category]
 (DEST/category).mkdir()
 for p in range(0,len(entries),20):
  subset=entries[p:p+20]
  W,H=236,326
  board=Image.new('RGB',(W*5,64+H*4),(244,245,246))
  draw=ImageDraw.Draw(board);draw.rectangle((0,0,W*5,64),fill=(29,43,56))
  draw.text((20,14),f'แค็ตตาล็อก{category}  |  แผ่น {p//20+1}  |  ภาพจริง ไม่สุ่ม',font=hft,fill='white')
  for k,row in enumerate(subset):
   x=k%5*W;y=64+k//5*H
   tile=Image.open(DEST/'images'/(row['id']+'.jpg'))
   board.paste(tile,(x+3,y+3))
   draw.rectangle((x,y+286,x+W-1,y+H),fill=(35,45,56))
   label=row['id']+'  '+row['name']
   if len(label)>31:label=label[:30]+'…'
   draw.text((x+5,y+291),label,font=ft,fill='white')
   draw.rectangle((x,y,x+W-1,y+H-1),outline=(160,166,172))
  name=f'{category}_{p//20+1:02d}.jpg'
  board.save(DEST/category/name,'JPEG',quality=79,optimize=True)
  pages.append({'category':category,'filename':f'{category}/{name}','ids':[x['id'] for x in subset]})
(DEST/'รายการชุดพร้อมไฟล์จริง.json').write_text(json.dumps({'story':'ชัยชนะของคนไม่ยอมแพ้','count_total_filtered':len(rows),'candidate_preview_count':len(images),'rules':'manual visual shortlisting then CC5 fit; no random; no automatic PASS','items':rows,'pages':pages},ensure_ascii=False,indent=2),encoding='utf-8')
with (DEST/'README_วิธีเลือก.txt').open('w',encoding='utf-8') as f:
 f.write('แค็ตตาล็อกเสื้อผ้าที่มีภาพจริงของ CC5\n')
 f.write('A=คลังทั่วไป C=Custom N=CC5 built-in; เลข ID ใช้ค้นชื่อไฟล์จริงใน JSON\n')
 f.write('ห้ามสุ่ม หรือเลือกเพียงชื่อไฟล์ ต้องเปิดภาพและทดสอบใส่ตัวละครจริง\n')
 f.write('ชุดนอน ชุดผิดยุค ชุดแฟนตาซี ชุดที่เคยพัง และไม่มีภาพ ถูกกันออกจากแผงเลือก\n')
 f.write(f'รายการเสื้อกางเกง {len(rows)} / มีภาพและยังไม่พบข้อห้าม {len(images)} / แผงภาพ {len(pages)}\n')
webpage='''<!doctype html><html lang="th"><meta charset="utf-8"><title>CC5 เลือกชุดจากภาพ</title><style>body{font:15px Tahoma;background:#151e2b;color:white;margin:0}header{position:sticky;top:0;padding:12px;background:#101723}input,select{padding:9px}#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;padding:12px}.card{background:#29394a;padding:7px;border-radius:8px}img{width:100%;height:220px;object-fit:contain}.small{font-size:12px;color:#becbd6;overflow-wrap:anywhere}</style><header><b>CC5 • เลือกเสื้อกางเกงจากภาพจริง ไม่สุ่ม</b> <input id="q" placeholder="ค้นชื่อ / รหัส A-C-N" oninput="show()"> <select id="kind" onchange="show()"><option value="">ทุกประเภท</option><option>เสื้อ</option><option>กางเกง</option></select><span id="count"></span></header><div id="grid"></div><script>let data=__DATA__;function show(){let a=data.filter(x=>(!kind.value||x.category===kind.value)&&(!q.value||(x.id+' '+x.name).toLowerCase().includes(q.value.toLowerCase())));count.innerText=' '+a.length+' รายการ';grid.innerHTML=a.map(x=>'<div class="card"><a target="_blank" href="images/'+x.id+'.jpg"><img loading="lazy" src="images/'+x.id+'.jpg"></a><b>'+x.id+' '+x.name.replace(/[<>&]/g,'')+'</b><div class="small">'+x.source_group+' • '+x.category+'<br>ต้องทดสอบ Mesh ใน CC5 ก่อน</div></div>').join('')}show()</script></html>'''
published=[{'id':r['id'],'name':r['name'],'category':r['category'],'source_group':r['source_group']} for r in rows if r['id'] in images]
(DEST/'เปิดแค็ตตาล็อก.html').write_text(webpage.replace('__DATA__',json.dumps(published,ensure_ascii=False)),encoding='utf-8')
# Mirror compact picture catalog (not any original clothing meshes) to story folder in Drive, preserve no overwrite.
GOOGLE.mkdir()
for p in DEST.rglob('*'):
 if not p.is_file():continue
 dst=GOOGLE/p.relative_to(DEST)
 dst.parent.mkdir(exist_ok=True,parents=True)
 assert not dst.exists()
 shutil.copy2(p,dst)
 assert dst.stat().st_size==p.stat().st_size
print('CATALOG_BUILT', 'rows',len(rows),'pictured_candidates',len(images),'pages',len(pages),
      'drive',str(GOOGLE),'source_3d_copies',0,flush=True)
