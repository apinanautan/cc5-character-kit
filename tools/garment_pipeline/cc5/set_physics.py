# Inside CC5 via bridge: turn on light soft-cloth physics for our garments (weight maps from blender/make_weightmap.py).
# args: cloths=<name>|<wmap.png>;<name>|<wmap.png>   out=<dir>   save=<file name of the NEW project, never overwrites>
#       props=Name:value,Name:value   (optional overrides of CC5 soft-cloth properties, applied to every cloth)
# Renders the character after the cloth settles for ~2 s of timeline (settle_*.png) so the drape can be checked.
import os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc5util import settle, pose, shot
A = BRIDGE_ARGS  # noqa
out = A["out"]; log = []
av = RLPy.RScene.GetAvatars()[0]
cl = {c.GetName(): c for c in av.GetClothes()}
# gentle defaults: heavy damping + low inertia = moves a little, never flutters
# (CC5 scale, read from a CC5 library skirt: Mass 1, Damping 0.2, Drag 0.1, Inertia 8, Bending 30, Stretch 1, Elasticity 15)
GENTLE = {"Mass": 1.0, "Damping": 0.5, "Drag": 0.1, "Inertia": 4.0, "Bending": 30.0, "Stretch": 1.0, "Elasticity": 15.0}
for k, v in (x.split(":") for x in A.get("props", "").split(",") if x): GENTLE[k] = float(v)
for item in A["cloths"].split(";"):
    name, wmap = item.split("|")
    c = cl.get(name)
    if c is None: raise RuntimeError("no cloth %s on the character (have %s)" % (name, list(cl)))
    pc = c.GetPhysicsComponent()
    for mesh in pc.GetSoftPhysicsMeshNameList():
        for mat in pc.GetSoftPhysicsMaterialNameList(mesh):
            if wmap != "-":                          # "-" = keep the weight map the cloth already has (CC5 library clothes)
                r = pc.SetPhysicsSoftColthWeightMap(mesh, mat, wmap)
                log.append("%s/%s weightmap %s" % (name, mat, r))
            elif pc.GetPhysicsSoftColthWeightMap(mesh, mat) is None:
                log.append("%s/%s has NO weight map, physics skipped" % (name, mat)); continue
            before = {k: pc.GetSoftPhysXProperty(mesh, mat, k) for k in GENTLE}
            for k, v in GENTLE.items():
                if before[k] != -1.0: pc.SetSoftPhysXProperty(mesh, mat, k, v)
            after = {k: round(pc.GetSoftPhysXProperty(mesh, mat, k), 3) for k in GENTLE}
            log.append("props before %s after %s" % (before, after))
    pc.SetActivatePhysicsEnable(True)
    log.append("%s physics on=%s" % (name, pc.IsActivatePhysicsEnable()))
# let it settle: step the timeline (simulation runs while time advances), then render
pose(av, "A-Pose")
fps = 60
for f in range(0, 121, 4):
    RLPy.RGlobal.SetTime(RLPy.RTime.FromValue(int(f * 1000 / fps))); settle(60)
F, L, B = RLPy.ECameraLocationType_Front, RLPy.ECameraLocationType_Left, RLPy.ECameraLocationType_Back
for vtag, loc in (("front", F), ("side", L), ("back", B)):
    shot(os.path.join(out, "physics_settle_%s.png" % vtag), loc)
RLPy.RGlobal.SetTime(RLPy.RTime.FromValue(0))
p = os.path.join(out, A.get("save", "outfit_physics_on_character.ccProject"))
if not os.path.exists(p):
    s = RLPy.RSaveFileSetting(); s.SetSaveType(RLPy.ESaveFileType_Character); RLPy.RFileIO.SaveFile(av, s, p); log.append("saved " + p)
else:
    log.append("NOT saved, exists: " + p)
BRIDGE_RESULT = "; ".join(str(x) for x in log)
