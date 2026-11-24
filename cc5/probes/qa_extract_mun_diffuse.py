import os,json,sys
import RLPy
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import kit
A=BRIDGE_ARGS
d=os.path.join(kit.JOBS,A['job'])
job=json.load(open(os.path.join(d,'job.json'),encoding='utf-8-sig'))
RLPy.RFileIO.LoadFile(os.path.join(d,job['name']+'.ccProject'))
av=RLPy.RScene.GetAvatars()[0]
outdir=os.path.join(d,'qa_new_clothes');os.makedirs(outdir,exist_ok=True)
log=[]
for i,c in enumerate(av.GetClothes()):
 comp=c.GetMaterialComponent()
 for j,mesh in enumerate(c.GetMeshNames()):
  for k,mat in enumerate(comp.GetMaterialNames(mesh)):
   try:
    img=comp.GetImage(mesh,mat,RLPy.EMaterialTextureChannel_Diffuse)
    path=os.path.join(outdir,'orig_cloth%d_mesh%d_mat%d.png'%(i,j,k))
    result=img.SaveFile(path)
    log.append('%s/%s -> %s bytes=%s result=%s'%(c.GetName(),mat,path,os.path.getsize(path) if os.path.exists(path) else 0,result))
   except Exception as e:
    log.append('FAIL %s/%s %s'%(c.GetName(),mat,e))
BRIDGE_RESULT='\n'.join(log)
