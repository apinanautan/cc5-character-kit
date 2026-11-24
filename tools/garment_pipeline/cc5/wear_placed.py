# Garment pipeline stage 4b/5 (inside CC5 via bridge). Uses the scene that prep_body.py left open
# (character in T-pose with the old top taken off). Never overwrites files.
# args: obj=<placed.obj (Y-up cm)>, out=<run dir>, name=<garment name>, color=r,g,b (0-1), stage_only=0|1
# 1) loads the OBJ as a prop at the exact placed position -> renders staged_T_*.png (check before converting)
# 2) removes the prop and loads the same OBJ with CC5 "Transfer Skin Weight" (becomes clothing, weights from body)
# 3) renders T-pose, A-pose and several real poses, saves <name>_on_character.ccProject (character only; no separate cloth file)
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc5util import settle, pose, shot, POSES
A = BRIDGE_ARGS  # noqa
out, obj, name = A["out"], A["obj"], A.get("name", "ai_garment")
rgb = [float(x) for x in A.get("color", "0.16,0.36,0.38").split(",")]
F, L, B = RLPy.ECameraLocationType_Front, RLPy.ECameraLocationType_Left, RLPy.ECameraLocationType_Back
log = []
avs = RLPy.RScene.GetAvatars()
if len(avs) != 1: raise RuntimeError("expected exactly one character in the scene")
av = avs[0]
for c in list(av.GetClothes()):                      # take off an earlier test garment we made (already saved in its own project)
    if c.GetName() in A.get("remove", "").split(","):
        RLPy.RScene.RemoveObject(c); log.append("removed " + c.GetName())
pose(av, "T-Pose")


def paint(o):
    comp = o.GetMaterialComponent()
    for mesh in o.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            if A.get("diffuse"):                     # baked fabric texture (from bake_fabric.py); white tint = true colours
                comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Diffuse, A["diffuse"])
                comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(1, 1, 1))
            else:
                comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(*rgb))
            comp.SetTwoSidedMaterial(mesh, mat, True)
            if A.get("normal"):                      # seams/buttons/collar edges baked as a normal (bump) map
                comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Normal, A["normal"])


# 1) staged prop check
before = set(o.GetName() for o in RLPy.RScene.GetProps())
RLPy.RFileIO.LoadFile(obj); settle(800)
props = [o for o in RLPy.RScene.GetProps() if o.GetName() not in before]
for p in props: paint(p)
for tag, loc in (("front", F), ("side", L), ("back", B)):
    shot(os.path.join(out, "staged_T_%s.png" % tag), loc)
for p in props: RLPy.RScene.RemoveObject(p)
log.append("staged prop rendered")
# 2) clothing with transferred skin weights
def convert():
    global log
    before_c = set(c.GetName() for c in av.GetClothes())
    RLPy.RScene.SelectObject(av)
    r = av.LoadAccessoryWithTransferSkinWeight(obj, A.get("template", "Default"))
    new = [c for c in av.GetClothes() if c.GetName() not in before_c]
    if r.IsError() or len(new) != 1: raise RuntimeError("Transfer Skin Weight failed: %s" % [c.GetName() for c in av.GetClothes()])
    cloth = new[0]; cloth.SetName(name); paint(cloth); cloth.Update(); settle(800)
    log.append("clothing %s faces=%d" % (name, sum(m.GetFacesCount() for m in cloth.GetMeshes())))

    if A.get("final", "1") == "0":                   # an under-layer of a multi-piece outfit: no poses/save yet
        return "; ".join(log)
    # 3) pose tests
    tests =[("T", "T-Pose"), ("A", "A-Pose"), ("stand", "Stand Pose_F"), ("openA", "Open A")]
    for tag, pname in tests:
        pose(av, pname)
        for vtag, loc in (("front", F), ("side", L), ("back", B)):
            shot(os.path.join(out, "worn_%s_%s.png" % (tag, vtag)), loc)
    log.append("rendered poses " + ",".join(t for t, _ in tests))
    pose(av, "A-Pose")
    s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
    p = os.path.join(out, name + "_on_character.ccProject")
    if not os.path.exists(p): RLPy.RFileIO.SaveFile(av, s, p); log.append("saved " + p)
    return "; ".join(log)


BRIDGE_RESULT = "; ".join(log) if A.get("stage_only") == "1" else convert()
