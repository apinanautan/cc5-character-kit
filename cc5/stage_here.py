# Bridge: in the character that is ALREADY open in CC5 (nothing reloaded): T-pose, then load a garment OBJ as a prop with its texture.
#   python tools\cc5.py run cc5\stage_here.py obj=<garment.obj> tex=<tex.png>
import RLPy
A = BRIDGE_ARGS  # noqa: F821
av = RLPy.RScene.GetAvatars()[0]
RLPy.RScene.SelectObject(av)
RLPy.RFileIO.LoadFile(r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration\T-Pose.rlPose")
before = set(o.GetName() for o in RLPy.RScene.GetProps())
RLPy.RFileIO.LoadFile(A["obj"])
new = [o for o in RLPy.RScene.GetProps() if o.GetName() not in before]
for o in new:
    comp = o.GetMaterialComponent()
    for mesh in o.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Diffuse, A["tex"])
            comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(1, 1, 1))
            comp.SetTwoSidedMaterial(mesh, mat, True)
BRIDGE_RESULT = "props %s" % [o.GetName() for o in new]
