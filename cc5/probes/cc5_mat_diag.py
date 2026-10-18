# Run inside CC5: dump material API + shader params of clothes containing 'material' (blouse).
import os, RLPy
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs")
av = RLPy.RScene.GetAvatars()[0]; log = []
for cl in av.GetClothes():
    if "material" not in cl.GetName():
        continue
    comp = cl.GetMaterialComponent()
    log.append("METHODS %r" % [m for m in dir(comp) if not m.startswith("_")])
    for mesh in cl.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            log.append("MAT %s/%s shader=%s" % (mesh, mat, comp.GetShader(mesh, mat) if hasattr(comp, "GetShader") else "?"))
            for p in comp.GetShaderParameterNames(mesh, mat):
                try: v = comp.GetShaderParameter(mesh, mat, p)
                except Exception as e: v = e
                log.append("  %s = %r" % (p, v))
            for ch in ("Diffuse",):
                for fn in ("GetTextureUVTiling", "GetUVTiling", "GetTextureTiling"):
                    if hasattr(comp, fn):
                        log.append("  %s %r" % (fn, getattr(comp, fn)))
open(os.path.join(J, "mat_diag.txt"), "w", encoding="utf-8").write("\n".join(log))
