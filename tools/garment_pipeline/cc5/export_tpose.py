# Inside CC5 via bridge: export the character as it is now (body + every worn cloth, e.g. a CC5 library skirt) in T-pose
# to a NEW OBJ, same space as prep_body's body_tpose.obj, so Blender scripts can fit our garments around library clothes.
# args: out=<new .obj path>  pose_after=<pose name to go back to, default A-Pose>. Changes nothing else in the scene.
import os, sys
import RLPy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc5util import settle, pose
A = BRIDGE_ARGS  # noqa
out = A["out"]
if os.path.exists(out): raise RuntimeError("exists, not overwriting: " + out)
av = RLPy.RScene.GetAvatars()[0]
pose(av, "T-Pose"); settle(500)
RLPy.RFileIO.ExportObjFile(av, out, RLPy.EExport3DFileOption__None)
pose(av, A.get("pose_after", "A-Pose"))
BRIDGE_RESULT = "exported %s clothes=%s" % (out, [c.GetName() for c in av.GetClothes()])
