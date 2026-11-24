
import os,json
import RLPy
A=BRIDGE_ARGS
import kit
d=A['job'] if os.path.isabs(A['job']) else os.path.join(kit.JOBS,A['job'])
job=json.load(open(os.path.join(d,'job.json'),encoding='utf-8-sig'))
RLPy.RFileIO.LoadFile(os.path.join(d,job['name']+'.ccProject'))
av=RLPy.RScene.GetAvatars()[0]
out=[]
for c in av.GetClothes():
 out.append('CLOTH '+c.GetName()+' meshes '+repr(c.GetMeshNames()))
 comp=c.GetMaterialComponent()
 for mesh in c.GetMeshNames():
  try:
   for mat in comp.GetMaterialNames(mesh):
    vals={'mesh':mesh,'material':mat}
    for attr in ('GetTexturePath','GetMaterialColor','GetMaterialType'):
     try:
      fn=getattr(comp,attr);val=fn(mesh,mat,RLPy.EMaterialTextureChannel_Diffuse) if attr=='GetTexturePath' else fn(mesh,mat)
      vals[attr]=str(val)[:250]
     except Exception as e:vals[attr]='ERR '+str(e)[:120]
    out.append(repr(vals))
  except Exception as e:out.append('MESH_ERR '+str(e))
p=os.path.join(d,'qa_material_inventory.txt')
open(p,'w',encoding='utf-8').write('\n'.join(out))
BRIDGE_RESULT='\n'.join(out)[:4000]
