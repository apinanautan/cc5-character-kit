# Bridge: after the user placed the garment prop by hand (cc5\stage_garment.py), turn it into clothing on the
# character: export the prop where it stands, load it back with Transfer Skin Weight (character in T-pose), put the
# texture back, remove the prop, render T + A pose, save <job>\<save>.ccProject.
#   python tools\cc5.py run cc5\skin_garment.py job=<job> prop=node_0 tex=<diffuse.png> [save=name]
import json, os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

A = BRIDGE_ARGS  # noqa: F821
d = os.path.join(kit.JOBS, A["job"])
POSES = r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration"
av = RLPy.RScene.GetAvatars()[0]
prop = [p for p in RLPy.RScene.GetProps() if p.GetName() == A.get("prop", "node_0")][0]
log = []
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(os.path.join(POSES, "T-Pose.rlPose"))  # same pose the garment was placed in
tmp = os.path.join(d, "garment_placed.obj")
RLPy.RFileIO.ExportObjFile(prop, tmp, RLPy.EExport3DFileOption__None)
before = set(c.GetName() for c in av.GetClothes())
r = av.LoadAccessoryWithTransferSkinWeight(tmp, A.get("template", "Default"))
log.append("skin -> %s" % ("error" if r.IsError() else "ok"))
for c in av.GetClothes():
    if c.GetName() in before:
        continue
    comp = c.GetMaterialComponent()
    for mesh in c.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            if A.get("tex"):
                comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Diffuse, A["tex"])
                comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(1, 1, 1))
            comp.SetTwoSidedMaterial(mesh, mat, True)
    c.Update()
    log.append("new cloth " + c.GetName())
RLPy.RScene.RemoveObject(prop)
for tag, pose in (("T", "T-Pose"), ("A", "A-Pose")):
    RLPy.RScene.SelectObject(av)
    RLPy.RFileIO.LoadFile(os.path.join(POSES, pose + ".rlPose"))
    RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
    RLPy.RGlobal.RenderImage(os.path.join(d, "skinned_%s.png" % tag))
if A.get("save"):
    s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
    RLPy.RFileIO.SaveFile(av, s, os.path.join(d, A["save"] + ".ccProject"))
    log.append("saved " + A["save"])
BRIDGE_RESULT = "\n".join(log)
