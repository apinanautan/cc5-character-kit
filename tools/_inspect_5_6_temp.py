import pathlib,os,json
r=pathlib.Path(r'C:\Users\Apinan\Documents\CC5 Characters\runs\rak_lam_iang_natural_v1')
print('ROOTFILE', [(x.name,x.stat().st_size) for x in r.iterdir() if x.is_file()][:60])
for item in r.iterdir():
 if not item.is_dir():continue
 if item.name.startswith(('5.','6.')) or 'pichai' in item.name.lower() or 'manop' in item.name.lower():
  print('FOLDER',ascii(item.name))
  for f in list(item.rglob('*'))[:80]:
   if f.is_file():print('FILE',str(f.relative_to(r)),f.stat().st_size)
for file in ['wardrobe_design.json','lookbook.json','status.json','outfit_lock.json','wardrobe_lock.json']:
 p=r/file
 if p.exists():
  print('META',file,p.read_text(encoding='utf-8-sig')[:9000].encode('unicode_escape').decode()[:9000])

