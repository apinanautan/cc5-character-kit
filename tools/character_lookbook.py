"""Record source-path hair/clothing/colors for every CC5 character and look.
No model copying, no backup snapshots. Before choosing assets run check.
After actual export run verify, never mark 'done' on preview alone.
"""
import argparse,json,os,sys
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parent.parent
DEFAULT=ROOT/'runs'/'rak_lam_iang'/'LOOKBOOK.json'
SLOTS={'hair','upper','lower','full','outer','shoes','base_body','accessory','accessory_2','accessory_3','prop'}
IMPORTANT={'hair','upper','lower','full','outer'}
REQUIRED_COLOR={'hair','upper','lower','full','outer','shoes'}
def now():return datetime.now().isoformat(timespec='seconds')
def load(path):
 if not path.is_file():raise ValueError(f'Lookbook not found: {path}')
 data=json.loads(path.read_text(encoding='utf-8-sig'))
 if 'characters' not in data:raise ValueError('Invalid lookbook')
 return data
def normalize(path):return os.path.normcase(os.path.normpath(str(path))).casefold()
def current(data,char_id,look_id):
 if char_id not in data['characters']:raise ValueError(f'Character not registered: {char_id}')
 looks=data['characters'][char_id]['looks']
 if look_id not in looks:raise ValueError(f'Look not registered: {char_id}/{look_id}')
 return looks[look_id]
def overlaps(data,char_id,slot,source):
 hits=[]
 src=normalize(source)
 for uid,c in data['characters'].items():
  if uid==char_id:continue
  for lk,look in c['looks'].items():
   for other_slot,v in look['assets'].items():
    if not isinstance(v,dict):continue
    path=v.get('path') or ''
    if normalize(path)==src and path:
     hits.append((c['name'],uid,lk,other_slot))
 return hits
def save(path,data):
 data['last_updated']=now()
 temp=path.with_suffix(path.suffix+'.writing')
 temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 os.replace(temp,path)
 report(path,data)
def report(path,data):
 lines=['# บัญชีทรงผมและเครื่องแต่งกาย — '+data.get('story',''),
        '',
        '| ตัวละคร | ลุค | สถานะ | ทรงผม (พาธ/สี) | ชุด (พาธ/สี) | รองเท้า/เครื่องประดับ | ส่งออก |',
        '|---|---|---|---|---|---|---|']
 for uid,c in data['characters'].items():
  for lid,lk in c['looks'].items():
   a=lk.get('assets',{})
   def fmt(slot):
    x=a.get(slot,{})
    if not x:return '—'
    src=x.get('path','')
    return (x.get('name') or Path(src).name)+' ('+(x.get('color') or 'ไม่ระบุสี')+')'
   def esc(x):return str(x).replace('|',' / ').replace('\n',' ')
   clothes='; '.join(f'{k}: {fmt(k)}' for k in ('upper','lower','full','outer') if k in a) or '—'
   extras='; '.join(f'{k}: {fmt(k)}' for k in ('shoes','accessory','accessory_2','accessory_3') if k in a) or '—'
   lines.append('| '+' | '.join(esc(x) for x in (c['name'],lk['label'],lk['status'],
                  fmt('hair'),clothes,extras,lk.get('export_path') or '—'))+' |')
 lines.append('\nไฟล์ต้นฉบับดูจากพาธใน LOOKBOOK.json — ไม่มีการคัดลอกโมเดลไว้ในโฟลเดอร์นี้')
 (path.parent/'LOOKBOOK_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
def cmd_report(args,data):
 report(args.ledger,data)
 print('STORY',data.get('story'))
 for uid,c in data['characters'].items():
  st=', '.join(f'{k}:{v["status"]}' for k,v in c['looks'].items())
  print(uid,c['name'],st)
 print('CHARACTERS',len(data['characters']),'LOOKS',sum(len(c['looks']) for c in data['characters'].values()))
def cmd_check(args,data):
 hits=overlaps(data,args.character,args.slot,args.path)
 print('ASSET',args.slot,Path(args.path).name)
 print('SOURCE_EXISTS',Path(args.path).is_file())
 print('OTHER_CHARACTER_REUSES',len(hits))
 for name,uid,look,slot in hits:print('CONFLICT',name,uid,look,slot)
 if hits and args.slot in IMPORTANT:sys.exit(2)
def cmd_set(args,data):
 look=current(data,args.character,args.look)
 if args.slot not in SLOTS:raise ValueError('Invalid asset slot: '+args.slot)
 source=Path(args.path)
 if not source.is_file() and not args.allow_offline:
  raise ValueError('Source file inaccessible (cannot claim actual assignment): '+args.path)
 if args.slot in REQUIRED_COLOR and not args.color:
  raise ValueError('Color mandatory for hair or clothing; pass --color')
 asset=look['assets'].get(args.slot)
 if asset and normalize(asset.get('path',''))!=normalize(args.path) and not args.replace:
  raise ValueError('Slot already assigned. Use --replace after deliberate change.')
 if look['status']=='verified' and not args.replace:
  raise ValueError('Verified look is locked. Use --replace to explicitly revoke verification.')
 hits=overlaps(data,args.character,args.slot,args.path)
 if hits and args.slot in IMPORTANT and not args.shared_reason:
  raise ValueError('Asset already used by a DIFFERENT character: '+str(hits)+'. Choose different cut/style or pass --shared-reason with why.')
 rec={'path':str(source),'name':source.name,'color':args.color or '',
       'style':args.style or '','material':args.material or '',
       'notes':args.note or '','source_accessible':source.is_file(),'updated':now()}
 look['assets'][args.slot]=rec
 if args.color:look['colors'][args.slot]=args.color
 if args.slot=='hair':look['hair_style']=args.style or look.get('hair_style','')
 if args.slot in {'upper','full','outer'}:
  if args.material:look['fabric']=args.material
  if args.style:look['silhouette']=args.style
 if args.shared_reason:
  look['exceptions'].append({'slot':args.slot,'source':str(source),'reason':args.shared_reason,'at':now()})
 look['status']='planned'
 look['export_path']=None
 look['last_updated']=now()
 save(args.ledger,data)
 print('RECORDED',args.character,args.look,args.slot,source.name,'COLOR',args.color)
 if hits:print('SHARED_WITH',hits,'REASON',args.shared_reason)
def cmd_verify(args,data):
 look=current(data,args.character,args.look)
 assets=look['assets']
 outfit=('full' in assets or ('upper' in assets and 'lower' in assets))
 if not outfit:raise ValueError('Cannot verify: need full outfit or upper+lower asset paths')
 if not any(k=='hair' for k in assets) and not args.bald_or_infant:
  raise ValueError('Missing hair asset. Only baby/bald actors may use --bald-or-infant')
 for slot,a in assets.items():
  if not Path(a['path']).is_file():raise ValueError('Missing source: '+slot+' '+a['path'])
  if slot in REQUIRED_COLOR and not a.get('color'):
   raise ValueError('Missing real color: '+slot)
 outfile=Path(args.export)
 if not outfile.is_file() or outfile.suffix.lower()!='.iavatar' or outfile.stat().st_size<1024:
  raise ValueError('Actual exported .iAvatar file not found or too small: '+str(outfile))
 look['export_path']=str(outfile)
 look['status']='verified'
 look['last_updated']=now()
 save(args.ledger,data)
 print('VERIFIED',args.character,args.look,'EXPORT',outfile)
def cmd_addlook(args,data):
 c=data['characters'].get(args.character)
 if c is None:raise ValueError('Unknown character; add-character first')
 if args.look in c['looks']:raise ValueError('Look ID already exists')
 c['looks'][args.look]={'label':args.label,'status':'unassigned','assets':{},'colors':{},
 'hair_style':'','silhouette':'','fabric':'','accessory_notes':'',
 'scene_notes':'','export_path':None,'preview_path':None,
 'exceptions':[],'last_updated':None}
 save(args.ledger,data)
 print('LOOK_ADDED',args.character,args.look)
def cmd_addchar(args,data):
 if args.character in data['characters']:raise ValueError('Character already exists')
 data['characters'][args.character]={'name':args.name,'group':args.group or '',
 'looks':{'everyday':{'label':'ลุคปกติ','status':'unassigned','assets':{},'colors':{},
 'hair_style':'','silhouette':'','fabric':'','accessory_notes':'',
 'scene_notes':'','export_path':None,'preview_path':None,'exceptions':[],'last_updated':None}}}
 save(args.ledger,data)
 print('CHARACTER_ADDED',args.character,args.name)
def main():
 parser=argparse.ArgumentParser(description='Track asset source paths, clothing colors, and verified looks for the CURRENT story')
 parser.add_argument('--ledger',type=Path,default=DEFAULT)
 subs=parser.add_subparsers(dest='cmd',required=True)
 subs.add_parser('report')
 for action in ('check','set'):
  p=subs.add_parser(action)
  p.add_argument('--character',required=True)
  if action=='set':p.add_argument('--look',required=True)
  p.add_argument('--slot',required=True,choices=sorted(SLOTS))
  p.add_argument('--path',required=True)
  if action=='set':
   p.add_argument('--color')
   p.add_argument('--style')
   p.add_argument('--material')
   p.add_argument('--note')
   p.add_argument('--shared-reason')
   p.add_argument('--replace',action='store_true')
   p.add_argument('--allow-offline',action='store_true')
 p=subs.add_parser('verify')
 p.add_argument('--character',required=True)
 p.add_argument('--look',required=True)
 p.add_argument('--export',required=True)
 p.add_argument('--bald-or-infant',action='store_true')
 p=subs.add_parser('add-look')
 p.add_argument('--character',required=True)
 p.add_argument('--look',required=True)
 p.add_argument('--label',required=True)
 p=subs.add_parser('add-character')
 p.add_argument('--character',required=True)
 p.add_argument('--name',required=True)
 p.add_argument('--group')
 args=parser.parse_args()
 data=load(args.ledger)
 {'report':cmd_report,'check':cmd_check,'set':cmd_set,'verify':cmd_verify,
 'add-look':cmd_addlook,'add-character':cmd_addchar}[args.cmd](args,data)
if __name__=='__main__':
 try:main()
 except (ValueError,FileNotFoundError,KeyError) as exc:
  print('ERROR',str(exc),file=sys.stderr)
  sys.exit(1)