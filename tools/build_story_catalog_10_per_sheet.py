"""Read-only source mesh catalogue; 10 large real CC5 preview images per contact sheet.
Story-scoped character suitability tags are human-curated ONLY for actually reviewed imagery.
Others remain REVIEW_REQUIRED; no guessing, random choice, or automatic wardrobe approval.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import os,json,hashlib,shutil,math,re
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runs/chai_chana_khon_mai_yom_phae_sister2_scoop_v11/wardrobe_catalog'
SCAN=ROOT/'runs/wardrobe_scan'
NEW=RUN/'แค็ตตาล็อก_10รูปต่อแผ่น'
DRIVE=Path.home()/'Desktop'/'ชัยชนะของคนไม่ยอมแพ้'/'ไฟล์ทำงานภายใน_ไม่อัปขึ้นDrive'/'แค็ตตาล็อกชุด_เลือกจากรูป'/'แค็ตตาล็อก_10รูปต่อแผ่น'
assert os.environ.get('COMPUTERNAME','').upper()=='DESKTOP-F1PJT4S'
assert (RUN/'รายการชุดพร้อมไฟล์จริง.json').is_file() and DRIVE.parent.is_dir()
rootdata=json.loads((RUN/'รายการชุดพร้อมไฟล์จริง.json').read_text(encoding='utf-8-sig'))
items=rootdata['items']
# Visual notes manually inspected against actual CC5 preview contact sheet. NOT full-character fit approval.
manual={
'A123':('พักก่อน','คอลึกเปิดมาก อาจไม่เหมาะกับชาวบ้านในบทนี้',[],'short_open'),
'A124':('ไม่เลือก','เสื้อคลุมดำเปิดอก ไม่มีเสื้อด้านใน',[],'open_coat'),
'A129':('พิจารณา','เชิ้ตแขนสั้นสีฟ้าจาง เหมาะกับร้านค้าหรือชายวัยหนุ่ม',['ชัยยศ — วัยหนุ่ม','น้องชายชัยยศ — วัยหนุ่ม'],'short_button'),
'A140':('พักก่อน','เสื้อคอกลมทูโทนคล้ายเสื้อสมัยใหม่ ตรวจยุคเพิ่มเติม',[],'crew_long'),
'A144':('พักก่อน','ลายดอกสีสดเด่นมาก ไม่เหมาะฐานะชาวบ้านทั่วไป',[],'bright_floral'),
'A157':('ไม่เลือก','เสื้อเข้ารูปคอสูง รูปทรงไม่เหมาะงานชนบทที่กำหนด',[],'fitted_highneck'),
'A163':('พิจารณา','เสื้อแขนยาวสีฟ้าลักษณะลำลอง เหมาะชายทำงาน',['พ่ออำพร — วัยผู้ใหญ่','คนงานโรงอิฐ B — วัยหนุ่ม'],'work_long'),
'A169':('ไม่เลือก','เชิ้ตสีอ่อนเปิดอกมาก ไม่เหมาะภาพตัวละครที่กำหนด',[],'open_shirt'),
'A180':('พักก่อน','เชิ้ตแขนยาวเรียบ ดูเป็นงานสำนักงานกว่างานชนบท',[],'office_button'),
'A183':('พักก่อน','เสื้อเข้ารูปสีเข้ม ทดสอบยุคและทรงก่อน',[],'dark_tight'),
'C230':('พิจารณา','เชิ้ตขาวแขนยาวเรียบ ต้องทดสอบความต่างจากคนอื่น',['แม่อำพร — วัยผู้ใหญ่'],'white_button'),
'C234':('พิจารณา','เสื้อแขนยาวสีอ่อนเรียบ เหมาะผู้หญิงชนบท',['น้องอำพรคนที่ 1 — วัยสาว'],'simple_long'),
'C235':('พิจารณา','เชิ้ตสีน้ำเงินแขนยาวแบบทำงาน พิจารณาคนงานหรือผู้ใหญ่',['คนงานโรงอิฐ A — วัยผู้ใหญ่'],'blue_work'),
'C240':('พิจารณา','เสื้อแขนสั้นผ้าหม่น มีคอปก ต้องตรวจระดับเปิดคอ',['น้องอำพรคนที่ 1 — วัยสาว'],'short_collar'),
'C245':('พิจารณา','เชิ้ตสีเทาอ่อนแขนยาว เหมาะชายร้านค้า แต่คล้ายเชิ้ตทั่วไป',['ชัยยศ — วัยหนุ่ม'],'light_long_button'),
'C247':('พิจารณา','เชิ้ตลายสก็อตน้ำเงินแขนยาว เหมาะหนุ่มชนบท ต้องเช็กกางเกงไม่หาย',['ลูกแฝด B — วัยหนุ่ม','น้องชายชัยยศ — วัยหนุ่ม'],'blue_check'),
'C254':('พิจารณา','เชิ้ตฟ้าแขนสั้นแนวลำลอง เหมาะหนุ่มวัยทำงาน',['ลูกแฝด A — วัยหนุ่ม'],'blue_short_button'),
'C257':('พิจารณา','เสื้อผู้หญิงแขนสามส่วนคอกว้าง โทนกลาง ๆ',['น้ำผึ้ง — ช่วงน้ำหนักเพิ่มมากและมีโรคเรื้อรัง','แม่อำพร — วัยผู้ใหญ่'],'threequarter_scoop'),
'C260':('พักก่อน','เสื้อสีเขียวสดเปิดคอเด่น อาจไม่เหมาะกับโทนเรื่อง',[],'green_open'),
'C262':('พิจารณา','เสื้อคอกลมลายทางแขนสั้น เหมาะวัยรุ่น แต่ต้องดูความร่วมยุค',['น้องอำพรคนที่ 3 — วัยหนุ่ม'],'striped_tee')
}
avoid=re.compile(r'paja(s|ma)?\b|panties|underwear|lingerie|bikini|sportsfashion|basketball|galatasaray|barca\b|1 year|10 yrs|school|officer|polic|swat|hoodie|medieval|wint sweat|corset|islam|ihram|surgeon|doctor|scrub|sexy d|bra\b|suit|coat|jacket|pante\b|military|uniform|^cooperate$',re.I)
fontfile=Path('C:/Windows/Fonts/tahoma.ttf')
def font(sz):return ImageFont.truetype(str(fontfile),sz) if fontfile.is_file() else ImageFont.load_default()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while True:
   block=f.read(4*1024*1024)
   if not block:break
   h.update(block)
 return h.hexdigest()
mapped={}
for x in items:
 code=x['id']
 if not x['preview'] or x['excluded']:continue
 source={'A':'adult','C':'custom','N':'cc5'}[code[0]]
 source_images=list(SCAN.glob(f'{source}_batch_*/{int(code[1:]):03}.png'))
 if not source_images:continue
 fn=Path(x['file'])
 why=None
 if avoid.search(x['name']) or avoid.search(x.get('original_rel','')):
  why='กีดกันเบื้องต้น: ชุดนอน/ชุดพิเศษ/กีฬา/ผิดบท หรือชื่อไม่เหมาะ'
 status,note,actors,shape=manual.get(code,('รอคัดด้วยตา','ยังไม่ได้ตรวจลักษณะจากภาพรายตัว',[],'UNREVIEWED'))
 if status=='ไม่เลือก':why=note
 if why:continue
 e={**x,'suitability_status':status,'visual_review_note':note,
    'suggested_characters':actors,'silhouette_family':shape,
    'cc5_on_character':'NOT_FIT_TESTED','selection_lock':'NOT_APPROVED',
    'preview_source':str(max(source_images,key=lambda p:p.stat().st_mtime))}
 mapped[code]=e
assert len(mapped)>250
NEW.mkdir(exist_ok=True);DRIVE.mkdir(exist_ok=True)
rows_by_kind={}
for kind in ['เสื้อ','กางเกง']:
 rows_by_kind[kind]=[e for e in mapped.values() if e['category']==kind]
 rows_by_kind[kind].sort(key=lambda e:e['id'])
def sync_file(local):
 dst=DRIVE/local.relative_to(NEW)
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():
  assert dst.stat().st_size==local.stat().st_size and sha(dst)==sha(local),'Conflicting existing file '+str(dst)
 else:shutil.copy2(local,dst)
 return str(dst)
photos=[]
for kind,records in rows_by_kind.items():
 sub=NEW/kind;sub.mkdir(exist_ok=True)
 for batch_num,offset in enumerate(range(0,len(records),10),1):
  batch=records[offset:offset+10]
  W,H=540,472;HEAD=92;FOOT=54
  img=Image.new('RGB',(W*2,HEAD+H*5+FOOT),(242,244,247))
  draw=ImageDraw.Draw(img)
  draw.rectangle((0,0,img.width,HEAD),fill=(24,40,55))
  draw.text((18,10),f'ชัยชนะของคนไม่ยอมแพ้  |  {kind}  |  ชุดที่ {batch_num:02d}',font=font(26),fill='white')
  draw.text((18,50),'10 รูป/แผ่น • ภาพจริงจากคลัง CC5 • ใช้รหัสหา Asset ไม่สุ่ม',font=font(18),fill=(221,228,236))
  for i,entry in enumerate(batch):
   x=i%2*W;y=HEAD+i//2*H
   draw.rectangle((x+3,y+3,x+W-4,y+H-4),fill=(255,255,255),outline=(182,190,196),width=2)
   p=Path(entry['preview_source'])
   with Image.open(p) as orig:
    orig=orig.convert('RGB')
    orig.thumbnail((W-16,330),Image.Resampling.LANCZOS)
    img.paste(orig,(x+(W-orig.width)//2,y+7+(330-orig.height)//2))
   color={'พิจารณา':(25,125,77),'พักก่อน':(166,95,29),'รอคัดด้วยตา':(104,110,124)}.get(entry['suitability_status'],(90,90,90))
   name=entry['name']
   draw.text((x+12,y+340),f"{entry['id']}   {name[:31]}",font=font(23),fill=(26,39,53))
   draw.text((x+12,y+375),f"สถานะ: {entry['suitability_status']}",font=font(17),fill=color)
   notes=entry['visual_review_note']
   draw.text((x+12,y+401),notes[:41],font=font(16),fill=(63,73,84))
   if entry['suggested_characters']:
    s='ลองกับ: '+', '.join(entry['suggested_characters'])
    draw.text((x+12,y+429),s[:45],font=font(14),fill=(54,73,104))
  draw.rectangle((0,img.height-FOOT,img.width,img.height),fill=(218,226,234))
  draw.text((14,img.height-FOOT+14),f'รูป {offset+1}–{offset+len(batch)} / {len(records)} • ชื่อชุดและรหัสตรงภาพต้นทาง • ไม่ใช่ QA ผ่าน',font=font(16),fill=(28,46,60))
  local=sub/(f'{kind}_10รูปต่อแผ่น_{batch_num:02d}.jpg')
  img.save(local,'JPEG',quality=77,optimize=True)
  d=sync_file(local)
  photos.append({'kind':kind,'batch':batch_num,'ids':[x['id'] for x in batch],
                 'local':str(local),'google_drive':d,'size_px':list(img.size)})
# Keep script and locked data with project; do not rewrite historical catalog.
report={'story':'ชัยชนะของคนไม่ยอมแพ้','photo_group_size':10,
        'rationale':'2 columns, 5 rows; larger photos and text than prior 20/sheet test',
        'images_from_existing_cc5_preview':True,'original_3d_files_copied':False,
        'approval_policy':'NO random choice. Suggested only after a real picture inspection, CC5 fitting needed for PASS.',
        'counts':{'reviewable_with_image':len(mapped),'manual_reviewed':sum(e['id'] in manual for e in mapped.values()),
                  'not_yet_visually_reviewed':sum(e['id'] not in manual for e in mapped.values()),
                  'sheets':len(photos)},
        'items':list(mapped.values()),'sheets':photos}
out=NEW/'ชื่อชุด_เหมาะกับตัวละครอะไร.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
sync_file(out)
text=NEW/'อ่านก่อนเลือกชุด.txt'
text.write_text('ชัยชนะของคนไม่ยอมแพ้ — แค็ตตาล็อกเสื้อกางเกงจากภาพจริง 10 รูป/แผ่น\n'
 'รหัส A=adult C=custom N=CC5; full source path in ชื่อชุด_เหมาะกับตัวละครอะไร.json\n'
 '“พิจารณา” = เห็นจากรูปว่ามีแนวโน้มเหมาะเท่านั้น; ยังต้องทดลองโหลด CC5, ตรวจ 4 มุม, T-Pose และ UV\n'
 '“รอคัดด้วยตา” = ห้ามนำไปใส่ตัวละครอัตโนมัติ; ไม่ใช่ชุดที่ผ่านการอนุมัติ\n'
 'ไม่คัดชุดจากชื่อเท่านั้น, ไม่ใช้สุ่ม, ไม่เอาชุดนอนที่เห็นว่าไม่เหมาะ\n'
 'แค็ตตาล็อกเก่าที่มี 20 รูปต่อแผ่นไม่ถูกลบทิ้งเพื่อให้ย้อนดูได้\n',
 encoding='utf-8')
sync_file(text)
print('CATALOG_10_DONE',report['counts'],'TOP_SHEETS',sum(x['kind']=='เสื้อ' for x in photos),
      'PANT_SHEETS',sum(x['kind']=='กางเกง' for x in photos))
print('PROJECT',NEW)
print('DRIVE',DRIVE)
