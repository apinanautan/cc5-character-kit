from pathlib import Path
import json,os
r=Path(r'C:\Users\Apinan\Documents\CC5 Characters\runs\rak_lam_iang_natural_v1')
for c in sorted(r.iterdir(),key=lambda p:p.name):
 if c.is_dir(): print('DIR',ascii(c.name),len(list(c.iterdir())))
for f in r.rglob('*.iAvatar'):
 if any(s in f.name.lower() for s in ('pichai','manop')) or any(s in str(f).lower() for s in ('5.','6.')):
  print('AVATAR',ascii(str(f.relative_to(r))),f.stat().st_size)
for f in r.rglob('*.json'):
 name=str(f.relative_to(r)).lower()
 if any(t in name for t in ('pichai','manop','wardrobe','lookbook','manifest','status')):
  print('JSON',ascii(name),f.stat().st_size)
for f in r.rglob('*.png'):
 name=str(f.relative_to(r)).lower()
 if any(t in name for t in ('pichai','manop','5.','6.')): print('PNG',ascii(name),f.stat().st_size)

