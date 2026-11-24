# Inside CC5 via bridge: real fabric surface on one cloth (proven on Nongrak v9, 2026-11-25).
#   Roughness = the weave picture as is (light/white tone)
#   Metallic  = the SAME weave picture inverted (dark tone)  -> rough + metal = 255 everywhere
#   Tiling 25 on both (Metallic by API here; Roughness only via cc5/set_channel_tiling_ui.py - API cannot reach it)
#   Diffuse print is reloaded LAST (loading textures can disturb it).
# args: cloth=<name> rough=<weave png> metal=<inverted weave png> diffuse=<print png> [normal=<button normal png>] [tile=25] [out=<dir>]
# Make the inverted file first:  .venv\Scripts\python.exe tile_texture.py --invert <weave.png> <out_invert.png>
# PROVEN: LoadImageToTexture(Roughness) does NOT reach the PBR Roughness slot (it said OK but the slot kept another picture).
#   Working way: im = GetImage(Roughness); im.LoadFile(path); SetImage(im, mesh, mat, Roughness)
# Never put test UV keys on Diffuse (it blanked the print once).
import os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc5util import settle, shot
A = BRIDGE_ARGS  # noqa
E = RLPy
av = E.RScene.GetAvatars()[0]
cl = {c.GetName(): c for c in av.GetClothes()}
c = cl.get(A["cloth"])
if c is None: raise RuntimeError("no cloth %s (have %s)" % (A["cloth"], list(cl)))
mc = c.GetMaterialComponent(); T = float(A.get("tile", 25)); log = []
R, ME, D = E.EMaterialTextureChannel_Roughness, E.EMaterialTextureChannel_Metallic, E.EMaterialTextureChannel_Diffuse


def size(mesh, mat, ch):
    im = mc.GetImage(mesh, mat, ch)
    return (im.GetWidth(), im.GetHeight()) if im is not None else None


for mesh in c.GetMeshNames():
    for mat in mc.GetMaterialNames(mesh):
        im = mc.GetImage(mesh, mat, R)
        if im is None:      # empty slot: the only way in is LoadImageToTexture, then replace through the image object
            mc.LoadImageToTexture(mesh, mat, R, A["rough"]); im = mc.GetImage(mesh, mat, R)
        if im is None: raise RuntimeError("cannot reach Roughness slot of %s/%s" % (mesh, mat))
        if im.LoadFile(A["rough"]).IsError(): raise RuntimeError("load rough failed")
        mc.SetImage(im, mesh, mat, R)
        mc.LoadImageToTexture(mesh, mat, ME, A["metal"])
        mc.AddUvDataKey(E.RKey(), mesh, mat, ME, E.RVector2(0.0, 0.0), E.RVector2(T, T), 0.0)
        if A.get("normal"): mc.LoadImageToTexture(mesh, mat, E.EMaterialTextureChannel_Normal, A["normal"])
        mc.LoadImageToTexture(mesh, mat, D, A["diffuse"])                      # LAST
        o, k = E.RVector2(), E.RVector2(); mc.GetUvData(mesh, mat, ME, o, k, 0.0)
        log.append("%s rough=%s metal=%s metal_tile=%s diffuse=%s" % (mat, size(mesh, mat, R), size(mesh, mat, ME), k.x, size(mesh, mat, D)))
c.Update(); settle(800)
if A.get("out"):
    os.makedirs(A["out"], exist_ok=True)
    shot(os.path.join(A["out"], "fabric_pbr_front.png"), E.ECameraLocationType_Back)   # Back preset = real front
    shot(os.path.join(A["out"], "fabric_pbr_side.png"), E.ECameraLocationType_Left)
BRIDGE_RESULT = "; ".join(log)
