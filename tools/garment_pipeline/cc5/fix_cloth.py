# Repaint the converted garment (RRgb is 0-1), make it two-sided, re-render, save .ccCloth (new files only).
import os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc5util import settle, pose, shot
A = BRIDGE_ARGS  # noqa
out, name = A["out"], A["name"]
rgb = [float(x) for x in A.get("color", "0.16,0.36,0.38").split(",")]
av = RLPy.RScene.GetAvatars()[0]
cloth = [c for c in av.GetClothes() if c.GetName() == name][0]
comp = cloth.GetMaterialComponent(); log = []
for mesh in cloth.GetMeshNames():
    for mat in comp.GetMaterialNames(mesh):
        comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(*rgb))
        if hasattr(comp, "AddSelfIlluminationKey"): comp.AddSelfIlluminationKey(RLPy.RKey(), mesh, mat, 0.0)
        log.append("2side=%s" % comp.SetTwoSidedMaterial(mesh, mat, True))
cloth.Update(); settle(800)
F, L, B = RLPy.ECameraLocationType_Front, RLPy.ECameraLocationType_Left, RLPy.ECameraLocationType_Back
for tag, pname in (("A", "A-Pose"), ("stand", "Stand Pose_F")):
    pose(av, pname)
    for v, loc in (("front", F), ("side", L), ("back", B)):
        shot(os.path.join(out, "v2_%s_%s.png" % (tag, v)), loc)
pose(av, "A-Pose")
p = os.path.join(out, name + "_v2.ccCloth")
s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Upper)
if not os.path.exists(p):
    RLPy.RFileIO.SaveFile(cloth, s, p)
    if not os.path.exists(p):
        RLPy.RScene.SelectObject(cloth); RLPy.RFileIO.SaveFile(av, s, p)
log.append("ccCloth %s" % ("ok" if os.path.exists(p) else "FAILED"))
p2 = os.path.join(out, name + "_v2_on_character.ccProject")
s2 = RLPy.RSaveFileSetting(); s2.SetSaveType(RLPy.ESaveFileType_Character)
if not os.path.exists(p2): RLPy.RFileIO.SaveFile(av, s2, p2); log.append("project ok" if os.path.exists(p2) else "project FAILED")
BRIDGE_RESULT = "; ".join(log)
