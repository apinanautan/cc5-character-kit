# CC5: dress a finished job in clean base garments (even-quad remesh + UV from Blender/UVgami) instead of its
# crumpled ones: T-pose, remove the old clothes, load each OBJ with Transfer Skin Weight, put its fabric on,
# A-pose, render <name>.png, save the project.
#   tools\cc5.py run cc5\wear_base.py job=<job dir> "items=a.obj|fabric.png;b.obj|fabric.png" [pose=A-Pose] [keep=1]
import json, os
import RLPy

A = BRIDGE_ARGS  # noqa: F821
POSE = os.path.join(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose", "Calibration")
d = A["job"]
name = json.load(open(os.path.join(d, "job.json"), encoding="utf-8-sig"))["name"]
RLPy.RFileIO.LoadFile(os.path.join(d, name + ".ccProject"))
av = RLPy.RScene.GetAvatars()[0]
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(os.path.join(POSE, A.get("pose", "T-Pose") + ".rlPose"))  # the pose the garments were fitted in
for c in list(av.GetClothes()):
    if A.get("keep") != "1" and not any(s in c.GetName().lower() for s in ("shoe", "sandal", "flip")):
        RLPy.RScene.RemoveObject(c)
log = []
for spec in A["items"].split(";"):
    obj, fab = spec.split("|")
    before = set(c.GetName() for c in av.GetClothes())
    r = av.LoadAccessoryWithTransferSkinWeight(obj, "Default")
    log.append("%s -> %s" % (os.path.basename(obj), "error" if r.IsError() else "ok"))
    for c in av.GetClothes():
        if c.GetName() in before:
            continue
        comp = c.GetMaterialComponent()
        for mesh in c.GetMeshNames():
            for mat in comp.GetMaterialNames(mesh):
                comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Diffuse, fab)
                comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(1, 1, 1))
                comp.AddGlossinessKey(RLPy.RKey(), mesh, mat, 0.0)
                comp.SetTwoSidedMaterial(mesh, mat, True)
        c.Update()
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(os.path.join(POSE, "A-Pose.rlPose"))
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
for _ in range(2):
    RLPy.RGlobal.RenderImage(os.path.join(d, name + ".png"))
s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
RLPy.RFileIO.SaveFile(av, s, os.path.join(d, name + ".ccProject"))
log.append("clothes=%s" % [c.GetName() for c in av.GetClothes()])
BRIDGE_RESULT = "\n".join(log)
