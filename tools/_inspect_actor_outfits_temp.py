import json, pathlib
r=pathlib.Path(r'C:\Users\Apinan\Documents\CC5 Characters')
for fn in ['rak_lam_iang.json','rak_lam_iang_natural_v1.json']:
 p=r/'stories'/fn;d=json.loads(p.read_text(encoding='utf-8-sig'))
 print('\nSTORY',fn,'title',ascii(d.get('title')),'num',len(d.get('characters',{})))
 for i,(k,c) in enumerate(d.get('characters',{}).items(),1):
  print(i,k,ascii(c.get('name')),ascii(c.get('folder')),'outfit',repr(c.get('outfit')))
for sub in sorted((r/'runs').iterdir(),key=lambda p:p.stat().st_mtime,reverse=True)[:20]:
 print('RUN',sub.name,'timestamp',sub.stat().st_mtime)

