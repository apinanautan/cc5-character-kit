import os,sys,json,traceback
import RLPy
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import kit
d=os.path.join(kit.JOBS,'story_1029_0051_06')
qa=os.path.join(d,'qa_new_clothes')
f=os.path.join(qa,'mun8_retextured.iAvatar')
log=[]
try:
 status=RLPy.RFileIO.LoadFile(f)
 avs=RLPy.RScene.GetAvatars()
 log.append('LOAD is_error=%s avatars=%d'%(status.IsError(),len(avs)))
 if len(avs)<1 or status.IsError():raise Exception('iAvatar load failed')
 av=avs[0]
 log.append('CLOTHES '+repr([(c.GetName(),sum(m.GetFacesCount() for m in c.GetMeshes())) for c in av.GetClothes()]))
 for tag,cam in (('front',RLPy.ECameraLocationType_Front),('left',RLPy.ECameraLocationType_Left),('back',RLPy.ECameraLocationType_Back),('right',RLPy.ECameraLocationType_Right)):
  RLPy.RScene.SelectObject(av)
  RLPy.RScene.GetCurrentCamera().SetCameraLocation(cam)
  p=os.path.join(qa,'reload_'+tag+'.png');RLPy.RGlobal.RenderImage(p)
  log.append('RENDER '+tag+' bytes='+str(os.path.getsize(p) if os.path.exists(p) else 0))
except:log.append('FAIL '+traceback.format_exc())
open(os.path.join(qa,'reload_result.txt'),'w',encoding='utf-8').write('\n'.join(log))
BRIDGE_RESULT='\n'.join(log)
