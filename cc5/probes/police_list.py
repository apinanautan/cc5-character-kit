# python tools/cc5.py run cc5/probes/police_list.py path=<iAvatar> out=<folder>
# Load a finished character, list its clothes/accessories and try to save the upper/lower as .ccCloth (avatar-level save).
import os
import RLPy

A = BRIDGE_ARGS  # noqa: F821
RLPy.RFileIO.LoadFile(A["path"])
av = RLPy.RScene.GetAvatars()[0]
os.makedirs(A["out"], exist_ok=True)
log = ["clothes: %s" % [c.GetName() for c in av.GetClothes()],
       "acc: %s" % [c.GetName() for c in av.GetAccessories()],
       "hair: %s" % [c.GetName() for c in av.GetHairs()]]
for role, t in (("upper", RLPy.ESaveFileType_Upper), ("lower", RLPy.ESaveFileType_Lower)):
    s = RLPy.RSaveFileSetting(); s.SetSaveType(t)
    dest = os.path.join(A["out"], "police_" + role + ".ccCloth")
    try:
        r = RLPy.RFileIO.SaveFile(av, s, dest)
        log.append("%s is_error=%s bytes=%d" % (role, r.IsError(), os.path.getsize(dest) if os.path.isfile(dest) else 0))
    except Exception as e:
        log.append("%s exception=%s" % (role, e))
BRIDGE_RESULT = "\n".join(log)
