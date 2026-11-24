"""Compare 20 items/sheet vs 10 items/sheet using SAME CC5 asset preview renders.
Inputs stay in place; keep sheets & metadata with the active story.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os,json,shutil,hashlib,math
ROOT=Path(__file__).resolve().parents[1]
SCAN=ROOT/'runs/wardrobe_scan'
CAT=ROOT/'runs/chai_chana_khon_mai_yom_phae_sister2_scoop_v11/wardrobe_catalog'
OUT=CAT/'แบบทดสอบ_10_vs_20'
DRIVE=Path.home()/'Desktop'/'ชัยชนะของคนไม่ยอมแพ้'/'ไฟล์ทำงานภายใน_ไม่อัปขึ้นDrive'/'แค็ตตาล็อกชุด_เลือกจากรูป'/'แบบทดสอบ_10_vs_20'
assert os.environ.get('COMPUTERNAME','').upper()=='DESKTOP-F1PJT4S'
assert DRIVE.parent.is_dir() and CAT.is_dir()
catalog=json.loads((CAT/'รายการชุดพร้อมไฟล์จริง.json').read_text(encoding='utf-8-sig'))
rows={r['id']:r for r in catalog['items']}
# Mix actual garments across existing categorized source sets; ID stable.
IDs=['A123','A124','A129','A140','A144','A157','A163','A169','A180','A183',
     'C230','C234','C235','C240','C245','C247','C254','C257','C260','C262']
all_rows=[]
for id in IDs:
 assert id in rows,id
 entry=rows[id]
 assert entry.get('preview') and not entry.get('excluded'),(id,entry.get('why_excluded'))
 group={'A':'adult','C':'custom','N':'cc5'}[id[0]]
 seq=int(id[1:])
 paths=list(SCAN.glob(f'{group}_batch_*/{seq:03d}.png'))
 assert paths,id
 src=max(paths,key=lambda p:p.stat().st_mtime)
 assert src.is_file()
 all_rows.append((entry,src))
OUT.mkdir(exist_ok=True);DRIVE.mkdir(exist_ok=True)
fontfile=Path('C:/Windows/Fonts/tahoma.ttf')
def font(sz):
 return ImageFont.truetype(str(fontfile),sz) if fontfile.is_file() else ImageFont.load_default()
def sheet(batch,per_sheet,num):
 cols=2 if per_sheet==10 else 4
 card_w=540 if per_sheet==10 else 270
 card_h=462 if per_sheet==10 else 350
 img_h=353 if per_sheet==10 else 256
 header=95;foot=60
 rows_count=math.ceil(len(batch)/cols)
 out=Image.new('RGB',(cols*card_w,header+rows_count*card_h+foot),(242,244,247))
 d=ImageDraw.Draw(out)
 d.rectangle((0,0,out.width,header),fill=(26,41,55))
 d.text((20,10),f'CC5 • ทดลอง {per_sheet} รูป/แผ่น | แบบ {num}',font=font(29),fill='white')
 d.text((20,52),'ภาพจากคลังจริง — อ่านชื่อและรหัส ก่อนเลือกให้ตัวละคร (ยังไม่ผ่าน CC5 Fit)',font=font(18),fill=(216,225,231))
 for i,(entry,src) in enumerate(batch):
  x=i%cols*card_w;y=header+i//cols*card_h
  d.rectangle((x+3,y+3,x+card_w-4,y+card_h-3),fill=(255,255,255),outline=(180,192,202),width=2)
  with Image.open(src) as im:
   im=im.convert('RGB')
   pmaxw=card_w-18
   im.thumbnail((pmaxw,img_h),Image.Resampling.LANCZOS)
   out.paste(im,(x+(card_w-im.width)//2,y+10+(img_h-im.height)//2))
  ty=y+img_h+17
  d.text((x+12,ty),entry['id']+'   '+entry['name'][:28],font=font(23 if per_sheet==10 else 16),fill=(31,40,49))
  d.text((x+12,ty+(36 if per_sheet==10 else 25)),f"แหล่ง: {entry['source_group']} | {entry['category']}",font=font(17 if per_sheet==10 else 13),fill=(70,80,94))
  if per_sheet==10:d.text((x+12,ty+66),'สภาพ: ยังไม่ทดสอบกับตัวละคร',font=font(16),fill=(133,80,40))
 d.rectangle((0,out.height-foot,out.width,out.height),fill=(222,229,234))
 d.text((15,out.height-foot+14),f'รวม {len(batch)} ไอเทม • ชุดตัวอย่างเดียวกัน • ไม่มีการสุ่ม • เก็บภาพต้นทางไว้ในโปรเจกต์',font=font(18),fill=(32,45,59))
 f=OUT/(('10_ชุด_%02d.jpg'%num) if per_sheet==10 else ('20_ชุด_%02d.jpg'%num))
 out.save(f,'JPEG',quality=82,optimize=True)
 target=DRIVE/f.name
 if target.is_file():
  assert hashlib.sha256(target.read_bytes()).digest()==hashlib.sha256(f.read_bytes()).digest()
 else:
  shutil.copy2(f,target)
 return {'image':str(f),'drive_image':str(target),'px':list(out.size),'items':[e['id'] for e,p in batch]}
test=[sheet(all_rows,20,1),sheet(all_rows[:10],10,1),sheet(all_rows[10:],10,2)]
doc={
 'story':'ชัยชนะของคนไม่ยอมแพ้',
 'source_catalog':str(CAT/'รายการชุดพร้อมไฟล์จริง.json'),
 'comparison':'Same 20 existing true CC5 preview renders; 20-sheet = 4 columns, 10-sheet = 2 columns. No new model rendering or random asset selection.',
 'recommendation':'10 per sheet for phone legibility, larger item and label, faster visual judgment; keep 20 only for quick desktop overview.',
 'test_images':test,'items':[dict(x) for x,p in all_rows]}
(OUT/'layout_comparison.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
target=DRIVE/'layout_comparison.json'
if not target.exists():shutil.copy2(OUT/'layout_comparison.json',target)
print('COMPARE_READY',[(Path(x['image']).name,Path(x['image']).stat().st_size,x['px']) for x in test])
print('LOCAL',OUT)
print('DRIVE',DRIVE)
