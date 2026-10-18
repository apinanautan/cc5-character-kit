# Run inside CC5 on the open character: put a fabric texture on chosen clothes.
# Reads cc5_jobs\retexture.json: {"<cloth name part>": "<texture png>", ...}; logs to retexture_log.txt
import json, os, traceback
import RLPy
J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "cc5_jobs")
plan = json.load(open(os.path.join(J, "retexture.json"), encoding="utf-8"))
log = []
av = RLPy.RScene.GetAvatars()[0]
for cl in av.GetClothes():
    name = cl.GetName()
    tex = next((t for k, t in plan.items() if k.lower() in name.lower()), None)
    tile = isinstance(tex, dict)  # {"tex": path} = tiling fabric: keep the cloth's own UV tiling
    if tile:
        tex = tex["tex"]
    log.append("cloth %s -> %s" % (name, tex))
    if not tex:
        continue
    comp = cl.GetMaterialComponent()
    for mesh in cl.GetMeshNames():
        for mat in comp.GetMaterialNames(mesh):
            try:
                r = comp.LoadImageToTexture(mesh, mat, RLPy.EMaterialTextureChannel_Diffuse, tex)
                comp.AddDiffuseKey(RLPy.RKey(), mesh, mat, RLPy.RRgb(1, 1, 1))
                # baked projection textures use the UV 0..1 once: no tiling
                if not tile:
                    comp.AddUvDataKey(RLPy.RKey(), mesh, mat, RLPy.EMaterialTextureChannel_Diffuse,
                                      RLPy.RVector2(0, 0), RLPy.RVector2(1, 1), 0.0)
                log.append("  %s/%s %s" % (mesh, mat, r))
            except Exception:
                log.append("  FAIL %s/%s %s" % (mesh, mat, traceback.format_exc()[-200:]))
    cl.Update()
log.append("comp methods: %r" % [m for m in dir(comp) if "UV" in m or "Tiling" in m or "Texture" in m])
open(os.path.join(J, "retexture_log.txt"), "w", encoding="utf-8").write("\n".join(log))
RLPy.RScene.SelectObject(av)
RLPy.RScene.GetCurrentCamera().SetCameraLocation(RLPy.ECameraLocationType_Front)
RLPy.RGlobal.RenderImage(os.path.join(J, "retexture_test.png"))
