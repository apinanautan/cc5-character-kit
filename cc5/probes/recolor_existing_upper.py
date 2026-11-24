"""Recolor only an identified upper garment, preserving all source objects."""
import json,sys
from pathlib import Path
import RLPy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from texture_ready import wait_for_textures,settle
plan=json.loads(Path(BRIDGE_ARGS["plan"]).read_text(encoding="utf-8"))
source,target,out=map(Path,(plan["source"],plan["target"],plan["out"]))
if not source.is_file() or target.exists() or not Path(plan["texture"]).is_file():
    raise RuntimeError("Source/texture missing or target exists")
loaded=RLPy.RFileIO.LoadFile(str(source))
settle(1000)
actors=list(RLPy.RScene.GetAvatars())
if loaded.IsError() or len(actors)!=1:
    raise RuntimeError("Could not open one saved source actor")
av=actors[0]
def inventory():
    return [(o.GetName(),sum(m.GetFacesCount() for m in o.GetMeshes())) for o in [av]+list(av.GetClothes())+list(av.GetHairs())+list(av.GetAccessories())]
before=inventory()
shirts=[o for o in av.GetClothes() if o.GetName()==plan["upper"]]
if len(shirts)!=1:
    raise RuntimeError("Expected one upper garment: "+repr(before))
wait_for_textures(BRIDGE_ARGS.get("scratch"))
shirt=shirts[0]
comp=shirt.GetMaterialComponent()
changed=[]
for mesh in shirt.GetMeshNames():
    for material in comp.GetMaterialNames(mesh):
        status=comp.LoadImageToTexture(mesh,material,RLPy.EMaterialTextureChannel_Diffuse,plan["texture"])
        if status is not None and hasattr(status,"IsError") and status.IsError():
            raise RuntimeError("Diffuse replacement failed "+material)
        comp.AddDiffuseKey(RLPy.RKey(),mesh,material,RLPy.RRgb(1,1,1))
        changed.append([mesh,material])
if not changed:
    raise RuntimeError("No materials changed")
shirt.Update()
RLPy.RScene.SelectObject(av)
wait_for_textures(BRIDGE_ARGS.get("scratch"))
if inventory()!=before:
    raise RuntimeError("Object inventory changed")
setting=RLPy.RSaveFileSetting()
setting.SetSaveType(RLPy.ESaveFileType_Character)
status=RLPy.RFileIO.SaveFile(av,setting,str(target))
if status.IsError() or not target.is_file() or target.stat().st_size<4096:
    raise RuntimeError("Could not save color revision")
for name,location in (("front",RLPy.ECameraLocationType_Front),("side",RLPy.ECameraLocationType_Left),("back",RLPy.ECameraLocationType_Back)):
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(location)
    settle(500)
    RLPy.RGlobal.RenderImage(str(out/(name+".png")))
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
record={"source":str(source),"target":str(target),"inventory":before,"changed":changed,"upper":plan["upper"],"color":plan["color"]}
(out/"color_evidence.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
BRIDGE_RESULT=json.dumps(record,ensure_ascii=False)
