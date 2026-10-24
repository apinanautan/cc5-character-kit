# Bridge: put a fitted AI garment (OBJ from blender/fit_garment.py, made in T-pose) on a job's character.
#   python tools\cc5.py run cc5\wear_garment.py job=<job> obj=<fitted.obj> [remove=top|none] [template=Default] [save=<name>]
# T-pose -> LoadAccessoryWithTransferSkinWeight (arms and torso far apart = clean weights) -> back to A-pose ->
# renders <job>\garment_T.png (T-pose) and garment_A.png (A-pose), and saves <save>.ccProject in the job folder
# (never overwrites the character's own project).
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

A = BRIDGE_ARGS  # noqa: F821
d = os.path.join(kit.JOBS, A["job"])
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
POSES = r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration"
log = []
RLPy.RFileIO.LoadFile(os.path.join(d, name + ".ccProject"))
av = RLPy.RScene.GetAvatars()[0]
SHOE = ("flop", "sandal", "sandle", "shoe", "boot")
if A.get("remove") == "all":  # new top AND bottom: take off every old garment except shoes
    for c in av.GetClothes():
        if not any(k in c.GetName().lower() for k in SHOE):
            RLPy.RScene.RemoveObject(c)
            log.append("removed " + c.GetName())
elif A.get("remove", "top") == "top":  # take off the old top (upper.txt) so only the new one shows
    up = os.path.join(d, "upper.txt")
    names = open(up, encoding="utf-8").read().splitlines() if os.path.exists(up) else []
    for c in av.GetClothes():
        if c.GetName() in names:
            RLPy.RScene.RemoveObject(c)
            log.append("removed " + c.GetName())
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(os.path.join(POSES, "T-Pose.rlPose"))
def texture_of(obj):
    """diffuse map named in the OBJ's .mtl (Blender copies it next to the OBJ)"""
    mtl = os.path.splitext(obj)[0] + ".mtl"
    if os.path.exists(mtl):
        for line in open(mtl, encoding="utf-8", errors="ignore"):
            if line.strip().lower().startswith("map_kd"):
                t = line.split(None, 1)[1].strip()
                t = t if os.path.isabs(t) else os.path.join(os.path.dirname(obj), t)
                if os.path.exists(t):
                    return t
    return None


for obj in A["obj"].split(";"):  # several fitted garments: obj=a.obj;b.obj
    before_c = set(o.GetName() for o in av.GetClothes())
    before = set(o.GetName() for o in av.GetAccessories())
    r = av.LoadAccessoryWithTransferSkinWeight(obj, A.get("template", "Default"))
    new = [o.GetName() for o in av.GetAccessories() if o.GetName() not in before]
    log.append("load %s -> %s, new accessories %s (avatar has %d accessories, %d clothes)" % (
        os.path.basename(obj), "error" if r.IsError() else "ok", new, len(av.GetAccessories()), len(av.GetClothes())))
    tex = texture_of(obj)  # CC5 loads the shape but not the AI texture: put it back
    for c in av.GetClothes():
        if c.GetName() not in before_c and not tex:
            comp = c.GetMaterialComponent()
            for mesh in c.GetMeshNames():
                for mat in comp.GetMaterialNames(mesh):
                    comp.SetTwoSidedMaterial(mesh, mat, True)
        if c.GetName() not in before_c and tex:
            comp = c.GetMaterialComponent()
            for mesh in c.GetMeshNames():
                for mat in comp.GetMaterialNames(mesh):
                    comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Diffuse, tex)
                    comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(1, 1, 1))
                    comp.SetTwoSidedMaterial(mesh, mat, True)  # AI shells have inward-facing parts (collar, hem)
            c.Update()
            log.append("texture %s -> %s" % (os.path.basename(tex), c.GetName()))


def shot(png):
    RLPy.RScene.SelectObject(av)
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
    RLPy.RGlobal.RenderImage(os.path.join(d, png))


shot("garment_T.png")
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(os.path.join(POSES, "A-Pose.rlPose"))
shot("garment_A.png")
if A.get("save"):
    s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
    RLPy.RFileIO.SaveFile(av, s, os.path.join(d, A["save"] + ".ccProject"))
    log.append("saved " + A["save"])
BRIDGE_RESULT = "\n".join(log)
