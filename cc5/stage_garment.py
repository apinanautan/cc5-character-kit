# Bridge: open a character for hand-fitting a new garment: remove its old top, T-pose, load the garment OBJ as a
# separate object (prop) with its texture, for the user to move/scale. Then run cc5\skin_garment.py.
#   python tools\cc5.py run cc5\stage_garment.py job=<job> obj=<garment.obj>[;b.obj] [tex=a.png;b.png] [remove=top|all|none]
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

A = BRIDGE_ARGS  # noqa: F821
d = os.path.join(kit.JOBS, A["job"])
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
RLPy.RFileIO.LoadFile(os.path.join(d, name + ".ccProject"))
av = RLPy.RScene.GetAvatars()[0]
log = []
up = os.path.join(d, "upper.txt")
tops = open(up, encoding="utf-8").read().splitlines() if os.path.exists(up) else []
SHOE = ("flop", "sandal", "sandle", "shoe", "boot")
mode = A.get("remove", "top")
for c in av.GetClothes():
    n = c.GetName()
    if (mode == "top" and n in tops) or (mode == "all" and not any(k in n.lower() for k in SHOE + ("sock",))):
        RLPy.RScene.RemoveObject(c)
        log.append("removed " + n)
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration\T-Pose.rlPose")
before = set(o.GetName() for o in RLPy.RScene.GetProps())
for f in A["obj"].split(";"):  # several garments: obj=a.obj;b.obj
    RLPy.RFileIO.LoadFile(f)
new = [o for o in RLPy.RScene.GetProps() if o.GetName() not in before]
for o, tex in zip(new, [t for t in A.get("tex", "").split(";") if t]):  # tex=a.png;b.png, same order as obj
    comp = o.GetMaterialComponent()
    for mesh in o.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Diffuse, tex)
            comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(1, 1, 1))
            comp.SetTwoSidedMaterial(mesh, mat, True)
log.append("loaded props %s" % [o.GetName() for o in new])
BRIDGE_RESULT = "\n".join(log)
