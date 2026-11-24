# Mun 8Y QA: use existing skinned outfit and replace only its diffuse texture.
import os,json,sys,traceback
import RLPy
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import kit
A=BRIDGE_ARGS
d=os.path.join(kit.JOBS,'story_1029_0051_06')
name=json.load(open(os.path.join(d,'job.json'),encoding='utf-8-sig'))['name']
qa=os.path.join(d,'qa_new_clothes');os.makedirs(qa,exist_ok=True)
tex=os.path.join(qa,'mun_bluegrey_fabric.png')
log=[]
try:
 src=os.path.join(d,name+'.ccProject')
 RLPy.RFileIO.LoadFile(src)
 avatars=RLPy.RScene.GetAvatars()
 if len(avatars)!=1:raise RuntimeError('Expected 1 avatar, got '+str(len(avatars)))
 av=avatars[0]
 clothes=av.GetClothes()
 target=[c for c in clothes if c.GetName()=='texture_pbr_v128_001']
 if len(target)!=1:raise RuntimeError('Expected original shirt mesh, got '+repr([c.GetName() for c in clothes]))
 c=target[0]
 comp=c.GetMaterialComponent()
 for mesh in c.GetMeshNames():
  for mat in comp.GetMaterialNames(mesh):
   result=comp.LoadImageToTexture(mesh,mat,RLPy.EMaterialTextureChannel_Diffuse,tex)
   log.append('MAP %s/%s result=%s'%(mesh,mat,str(result)))
   comp.AddDiffuseKey(RLPy.RKey(),mesh,mat,RLPy.RRgb(1,1,1))
 c.Update()
 RLPy.RScene.SelectObject(av)
 for tag,loc in (('front',RLPy.ECameraLocationType_Front),('left',RLPy.ECameraLocationType_Left),('back',RLPy.ECameraLocationType_Back),('right',RLPy.ECameraLocationType_Right)):
  RLPy.RScene.GetCurrentCamera().SetCameraLocation(loc)
  out=os.path.join(qa,'mun_new_'+tag+'.png')
  RLPy.RGlobal.RenderImage(out)
  log.append('RENDER '+tag+' bytes='+str(os.path.getsize(out) if os.path.exists(out) else 0))
 setting=RLPy.RSaveFileSetting();setting.SetSaveType(RLPy.ESaveFileType_Character)
 outproj=os.path.join(qa,'mun8_retextured.ccProject')
 status=RLPy.RFileIO.SaveFile(av,setting,outproj)
 log.append('SAVE status_error=%s bytes=%s'%(status.IsError(),os.path.getsize(outproj) if os.path.exists(outproj) else 0))
except:
 log.append('ERROR '+traceback.format_exc())
open(os.path.join(qa,'retexture_result.txt'),'w',encoding='utf-8').write('\n'.join(log))
BRIDGE_RESULT='\n'.join(log)
