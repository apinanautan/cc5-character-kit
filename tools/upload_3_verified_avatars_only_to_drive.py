"""Publish only genuine .iAvatar files; NO JSON/JPG/HTML/TXT on shared Drive.
Copy 3 newly repaired actors, verify SHA-256, keep local originals and leave all other Drive files untouched.
"""
from pathlib import Path
import os,re,json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
assert os.environ.get('COMPUTERNAME','').upper()=='DESKTOP-F1PJT4S'
DRIVE=Path(r'G:\ไดรฟ์ของฉัน\ชัยชนะของคนไม่ยอมแพ้\ชัยชนะของคนไม่ยอมแพ้ ตัวละคร')
DESK=Path.home()/'Desktop'/'ชัยชนะของคนไม่ยอมแพ้'
ORIGINAL=json.loads((ROOT/'stories/chai_chana_khon_mai_yom_phae.json').read_text(encoding='utf-8-sig'))
V13='chai_chana_khon_mai_yom_phae_remaining3_reliable_pants_v13'
V14='chai_chana_khon_mai_yom_phae_remaining2_repair_v14'
TARGETS=[('twin_a_young',V13),('twin_b_young',V14),('namphueng_later',V14)]
assert DRIVE.is_dir() and DESK.is_dir() and len(ORIGINAL['characters'])==23
def sha(p):
 h=hashlib.sha256()
 with p.open('rb',buffering=8*1024*1024) as f:
  while True:
   b=f.read(8*1024*1024)
   if not b:break
   h.update(b)
 return h.hexdigest()
files=[]
for suffix,slug in TARGETS:
 manifest=json.loads((ROOT/'runs'/slug/'rework_manifest.json').read_text(encoding='utf-8-sig'))['jobs']
 progress=json.loads((ROOT/'runs'/slug/'build_reviewed_progress.json').read_text(encoding='utf-8-sig'))['jobs']
 job=slug+'_'+suffix
 x=manifest[job];status=progress[job]
 assert status.get('status')=='TECHNICAL_EXPORT_REOPENED_REVIEW_REQUIRED' and status.get('reopen_verified') is True,(job,status)
 stage=Path(x['dest_job'])
 n=x['name']
 assert (stage/(n+'.ccProject')).is_file() and all((stage/('view_'+side+'.png')).is_file() for side in ('front','left','back','right'))
 text=(stage/'result.txt').read_text(encoding='utf-8',errors='replace')
 count=re.search(r'clothes_count:\s*(\d+)',text)
 assert count and int(count.group(1))==3,job
 source=Path(x['target_avatar'])
 assert source.is_file() and source.suffix.lower()=='.iavatar' and source.stat().st_size>50*1024*1024
 orig=ORIGINAL['characters']['chai_chana_khon_mai_yom_phae_'+suffix]
 assert orig['name']==n and orig['folder'] in ('7.ลูกแฝด','8.น้ำผึ้งและสามี')
 dst=DRIVE/orig['folder']/source.name
 assert dst.parent.is_dir() and source.name==n+'.iAvatar'
 files.append((source,dst,n,slug))
before=list(DRIVE.rglob('*.iAvatar'))
assert len(before)==20,len(before)
for src,dst,name,slug in files:
 h=sha(src)
 if dst.exists():
  assert dst.stat().st_size==src.stat().st_size and sha(dst)==h,'Different existing avatar, no overwrite: '+str(dst)
  print('EXISTING_VERIFIED',name,flush=True)
 else:
  tmp=dst.with_name(dst.name+'.uploading_verified')
  if tmp.exists():
   assert tmp.stat().st_size==src.stat().st_size and sha(tmp)==h,'Incomplete transfer preserved, manual intervention: '+str(tmp)
  else:
   print('COPYING',name,'BYTES',src.stat().st_size,flush=True)
   with src.open('rb',buffering=8*1024*1024) as a,tmp.open('xb',buffering=8*1024*1024) as b:
    shutil.copyfileobj(a,b,length=8*1024*1024)
    b.flush();os.fsync(b.fileno())
  assert tmp.stat().st_size==src.stat().st_size and sha(tmp)==h
  tmp.rename(dst)
  assert dst.is_file() and sha(dst)==h
  print('COPIED_SHA_VERIFIED',name,flush=True)
allfiles=[x for x in DRIVE.rglob('*') if x.is_file()]
expect={x['name']+'.iAvatar' for x in ORIGINAL['characters'].values()}
actual={x.name for x in allfiles}
assert len(allfiles)==len(actual)==23 and actual==expect,(len(allfiles),len(actual),expect-actual,actual-expect)
assert all(x.suffix.lower()=='.iavatar' for x in allfiles)
print('DRIVE_DONE_23_IAVATAR_ONLY',len(allfiles), 'NON_ACTOR_FILES',0,'PATH',DRIVE,flush=True)
# Update report exclusively on LOCAL DESKTOP (never publish it).
p=DESK/'ไฟล์ประกอบที่สร้างเพิ่ม'/'รายงานและรูปที่สร้างเพิ่ม'/'ใบงานและสถานะตัวละคร_23เวอร์ชัน.json'
if p.exists():
 document=json.loads(p.read_text(encoding='utf-8-sig'))
 for row in document.get('items',[]):
  for src,dst,n,slug in files:
   if row.get('name')!=n:continue
   row.update(quality_status='REVIEW',technical_source='new_cc5_repaired_'+slug,
              quality_note='3 garment nodes, CC5 iAvatar exported and reopened, four views; motion/T-Pose not yet tested',
              drive_file=str(dst),bytes=src.stat().st_size,sha256=sha(src),transfer_status='copied_sha_verified')
 document.update(technically_exported_unapproved=23,missing_everyday_exports=0,visual_pass_count=0,
                 notice='All 23 real iAvatar files present; each requires final mesh/motion/T-Pose QA before PASS')
 tmp=p.with_suffix('.json.localwriting')
 tmp.write_text(json.dumps(document,ensure_ascii=False,indent=2),encoding='utf-8')
 tmp.replace(p)
 print('DESKTOP_REPORT_UPDATED_ONLY',p,flush=True)
