from pathlib import Path
import json
r=Path(r'C:\Users\Apinan\Documents\CC5 Characters')
for fn in ['rak_lam_iang_natural_v1.json','rak_lam_iang.json']:
 d=json.loads((r/'stories'/fn).read_text(encoding='utf-8-sig'))
 print(fn,'out_dir',ascii(d.get('out_dir')),'status',ascii(str(d.get('status'))[:1300]))
for d in [r/'runs'/'rak_lam_iang_natural_v1',r/'runs'/'rak_lam_iang',r/'runs'/'rak_lam_iang_natural_manop_redress_v3',r/'runs'/'rak_lam_iang_natural_clothing_fix_v2']:
 print('LOCATION',str(d),'EXISTS',d.exists())
 if not d.exists():continue
 print('SUBFILE')
 for f in list(d.rglob('*'))[:50]:
  if f.is_file():print('FILE',ascii(str(f.relative_to(d))),f.stat().st_size)
  else:print('DIR',ascii(str(f.relative_to(d))))

