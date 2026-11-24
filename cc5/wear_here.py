# Bridge: put a Y-up OBJ garment (+ <name>.mtl with map_Kd) on the avatar that is ALREADY open (T-pose, Transfer Skin Weight).
#   python tools\cc5.py run cc5\wear_here.py obj=<garment.obj> [drop=node_1]   (drop = prop to delete first)
import os
import RLPy
A = BRIDGE_ARGS  # noqa: F821
for o in RLPy.RScene.GetProps():
    if o.GetName() == A.get("drop"):
        RLPy.RScene.RemoveObject(o)
av = RLPy.RScene.GetAvatars()[0]
for c in list(av.GetClothes()):
    if A.get('dropcloth') and c.GetName() == A['dropcloth']:
        RLPy.RScene.RemoveObject(c)
if A.get('dropall'):   # take off every garment except shoes
    for c in list(av.GetClothes()):
        if not any(k in c.GetName().lower() for k in ('flop','sandal','sandle','shoe','boot','sneaker')):
            RLPy.RScene.RemoveObject(c)
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(os.path.join(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration", A.get("pose", "T-Pose") + ".rlPose"))
before = set(o.GetName() for o in av.GetClothes())
r = av.LoadAccessoryWithTransferSkinWeight(A["obj"], "Default")
tex = None
mtl = os.path.splitext(A["obj"])[0] + ".mtl"
for line in open(mtl, encoding="utf-8"):
    if line.lower().startswith("map_kd"):
        tex = os.path.join(os.path.dirname(A["obj"]), line.split(None, 1)[1].strip())
log = ["load %s" % ("error" if r.IsError() else "ok")]
for c in av.GetClothes():
    if c.GetName() not in before:
        comp = c.GetMaterialComponent()
        for mesh in c.GetMeshNames():
            for mat in comp.GetMaterialNames(mesh):
                if tex:
                    comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Diffuse, tex)
                    comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(1, 1, 1))
                comp.SetTwoSidedMaterial(mesh, mat, True)
        c.Update(); log.append("new cloth " + c.GetName())
BRIDGE_RESULT = "\n".join(log)
