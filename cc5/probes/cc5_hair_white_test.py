# Run inside CC5: try making current hair truly gray/white -> render hair_white_test.png
import os
import RLPy
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs")
av = RLPy.RScene.GetAvatars()[0]
c = (0.80, 0.79, 0.78)
for hair in av.GetHairs():
    comp = hair.GetMaterialComponent()
    for mesh in hair.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            names = comp.GetShaderParameterNames(mesh, mat)
            for p, v in (("ActiveChangeHairColor", (1.0,)), ("BaseColorMapStrength", (0.0,)), ("VertexColorStrength", (0.0,)),
                         ("VertexGrayToColor", c), ("RootColor", c), ("TipColor", c)):
                if p in names:
                    comp.SetShaderParameter(mesh, mat, p, v)
    hair.Update()
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(J, "hair_white_test.png"))
