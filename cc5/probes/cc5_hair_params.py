# Run inside CC5: list hair shader parameters + values of the current avatar -> cc5_jobs\hair_params.txt
import os
import RLPy
out = []
av = RLPy.RScene.GetAvatars()[0]
for hair in av.GetHairs():
    comp = hair.GetMaterialComponent()
    for mesh in hair.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            out.append("== %s / %s / %s shader=%s" % (hair.GetName(), mesh, mat, comp.GetShader(mesh, mat) if hasattr(comp, "GetShader") else "?"))
            for p in comp.GetShaderParameterNames(mesh, mat):
                try:
                    v = comp.GetShaderParameter(mesh, mat, p)
                except Exception as e:
                    v = "err %r" % e
                out.append("  %s = %s" % (p, v))
open(os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs", "hair_params.txt"), "w", encoding="utf-8").write("\n".join(out))
