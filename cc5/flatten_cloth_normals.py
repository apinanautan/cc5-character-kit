# Bridge: remove the (often broken) normal/bump maps of a job's clothes - AI-made garments get dark streaks and a
# crumpled look from them. Renders view_*.png; saves only with save=1.
#   python tools\cc5.py run cc5\flatten_cloth_normals.py job=<job> [save=1]
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit
A = BRIDGE_ARGS  # noqa: F821
d = os.path.join(kit.JOBS, A["job"])
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
proj = os.path.join(d, name + ".ccProject")
RLPy.RFileIO.LoadFile(proj)
av = RLPy.RScene.GetAvatars()[0]
log = []
for c in av.GetClothes():
    if any(k in c.GetName().lower() for k in ("shoe", "sock")):
        continue
    comp = c.GetMaterialComponent()
    for mesh in c.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            for ch in (RLPy.EMaterialTextureChannel_Normal, RLPy.EMaterialTextureChannel_Bump):
                comp.RemoveMaterialTexture(mesh, mat, ch)
    c.Update()
    log.append("flattened " + c.GetName())
for tag, loc in (("front", RLPy.ECameraLocationType_Front), ("left", RLPy.ECameraLocationType_Left),
                 ("back", RLPy.ECameraLocationType_Back)):
    RLPy.RScene.SelectObject(av)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(loc)
    RLPy.RGlobal.RenderImage(os.path.join(d, "view_%s.png" % tag))
if A.get("save") == "1":
    s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
    RLPy.RFileIO.SaveFile(av, s, proj)
    log.append("saved")
BRIDGE_RESULT = "\n".join(log)
