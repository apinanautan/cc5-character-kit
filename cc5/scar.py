# Bridge: put a burn-scar overlay on this character's skin (arm / face / leg) and save.
#   python tools\cc5.py run cc5\scar.py job=<job> where=arm|face|leg tex=<overlay.png from tools\scar_overlay.py>
# The overlay goes into the skin's DiffuseBlend channel (on top of the character's own skin colour), so no texture
# export is needed (exporting the body with textures crashed CC5 on 2026-10-19).
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

A = BRIDGE_ARGS  # noqa: F821
d = os.path.join(kit.JOBS, A["job"])
MAT = {"arm": "Std_Skin_Arm", "face": "Std_Skin_Head", "leg": "Std_Skin_Leg"}[A.get("where", "arm")]
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
proj = os.path.join(d, name + ".ccProject")
RLPy.RFileIO.LoadFile(proj)
av = RLPy.RScene.GetAvatars()[0]
comp = av.GetMaterialComponent()
log = []
for mesh in av.GetMeshNames():
    if MAT in comp.GetMaterialNames(mesh):
        r = comp.LoadImageToTexture(mesh, MAT, RLPy.EMaterialTextureChannel_DiffuseBlend, A["tex"])
        comp.AddTextureWeightKey(RLPy.RKey(), mesh, MAT, RLPy.EMaterialTextureChannel_DiffuseBlend, 1.0)
        log.append("blend %s/%s -> %s" % (mesh, MAT, "error" if r.IsError() else "ok"))
av.Update()
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(d, name + ".png"))
s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
RLPy.RFileIO.SaveFile(av, s, proj)
log.append("OK scar on " + MAT if any(l.endswith("ok") for l in log) else "NO material " + MAT)
BRIDGE_RESULT = "\n".join(log)
