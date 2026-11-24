# Bridge: on the avatar that is already open: take off all clothes except shoes, put on library cloth files (lower first, then top), A-pose, render front.
#   python tools\cc5.py run cc5\dress_open.py items=<file1>|<file2> out=<png> [save=<project path>]
import os
import RLPy
A = BRIDGE_ARGS  # noqa: F821
av = RLPy.RScene.GetAvatars()[0]
SHOE = ('flop', 'sandal', 'sandle', 'shoe', 'boot', 'sneaker', 'slipper')
for c in list(av.GetClothes()):
    if not any(k in c.GetName().lower() for k in SHOE):
        RLPy.RScene.RemoveObject(c)
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration\A-Pose.rlPose")
for p in A["items"].split("|"):   # item  or  item=<fabric png>  (fabric replaces the diffuse texture, matte, like build.py)
    p, _, fab = p.partition("=")
    before = set(o.GetName() for o in av.GetClothes())
    RLPy.RScene.SelectObject(av)
    RLPy.RFileIO.LoadFile(p)
    if fab:
        for cl in av.GetClothes():
            if cl.GetName() in before:
                continue
            comp = cl.GetMaterialComponent()
            for mesh in cl.GetMeshNames():
                for mat in comp.GetMaterialNames(mesh):
                    comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Diffuse, fab)
                    comp.AddGlossinessKey(RLPy.RKey(), mesh, mat, 0.0)
                    comp.RemoveMaterialTexture(mesh, mat, RLPy.EMaterialTextureChannel_Metallic)
                    comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(1, 1, 1))
            cl.Update()
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(A["out"])
if A.get("save"):
    s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
    RLPy.RFileIO.SaveFile(av, s, A["save"])
BRIDGE_RESULT = "wearing %s" % [c.GetName() for c in av.GetClothes()]
