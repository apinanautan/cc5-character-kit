# Bridge: in the avatar that is already open, take off the hair, put on another hair file (.rlHair / .rlHairStyle ...), dye it
# (black by default), render a front picture and a head close-up, optionally save the project.
#   python tools\cc5.py run cc5\swap_hair.py hair=<file> out=<png prefix> [rgb=18,16,15] [save=<project path>]
import os
import RLPy
A = BRIDGE_ARGS  # noqa: F821
av = RLPy.RScene.GetAvatars()[0]
old = [h.GetName() for h in av.GetHairs()]
for h in list(av.GetHairs()):
    RLPy.RScene.RemoveObject(h)
RLPy.RScene.SelectObject(av)
if A["hair"] != "none":   # hair=none -> shaved head (no hair)
    RLPy.RFileIO.LoadFile(A["hair"])
c01 = tuple(int(v) / 255.0 for v in A.get("rgb", "18,16,15").split(","))
gray = max(int(v) for v in A.get("rgb", "18,16,15").split(",")) > 60
for h in av.GetHairs():
    comp = h.GetMaterialComponent()
    for mesh in h.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(*c01))
            names = comp.GetShaderParameterNames(mesh, mat)
            for p in names:
                if p in ("RootColor", "TipColor", "_1st Dye Color", "_2nd Dye Color"):
                    comp.SetShaderParameter(mesh, mat, p, c01)
                elif p in ("_1st Dye Strength", "_2nd Dye Strength"):
                    comp.SetShaderParameter(mesh, mat, p, (0.0,))
            for p, v in (("ActiveChangeHairColor", (1.0,) if gray else (0.0,)), ("BaseColorMapStrength", (0.0,) if gray else None),
                         ("VertexColorStrength", (0.0,) if gray else None), ("VertexGrayToColor", c01 if gray else None)):
                if v is not None and p in names:
                    comp.SetShaderParameter(mesh, mat, p, v)
    h.Update()
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(A["out"] + "_front.png")
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Face)
RLPy.RGlobal.RenderImage(A["out"] + "_face.png")
if A.get("save"):
    s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character)
    RLPy.RFileIO.SaveFile(av, s, A["save"])
BRIDGE_RESULT = "hair %s -> %s" % (old, [h.GetName() for h in av.GetHairs()])
