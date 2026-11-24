# Headless: a CC5 OBJ export keeps the avatar's scene rotation/position. Bring it into the frame of the reference
# body_tpose.obj by a rigid fit (Kabsch) of the CC_Base_Body vertices (same mesh, same vertex order), then write all groups.
#   blender -b -P align_export.py -- <reference body_tpose.obj> <cc5 export.obj> <out aligned.obj>
import bpy, sys
import numpy as np
from mathutils import Matrix
a = sys.argv[sys.argv.index("--") + 1:]
ref_p, src_p, out_p = a
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene


def load(p):
    before = set(sc.objects)
    bpy.ops.wm.obj_import(filepath=p, forward_axis="Y", up_axis="Z", use_split_groups=True)
    new = [o for o in sc.objects if o not in before]
    for o in new: o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
    return new


def body_pts(objs):
    b = next(o for o in objs if o.name.split(".")[0] == "CC_Base_Body")
    return np.array([v.co[:] for v in b.data.vertices])


ref = load(ref_p); R = body_pts(ref)
for o in ref: bpy.data.objects.remove(o)
src = load(src_p); S = body_pts(src)
if len(R) != len(S): sys.exit("CC_Base_Body vertex counts differ %d vs %d" % (len(R), len(S)))
cs, cr = S.mean(0), R.mean(0)
U, _, Vt = np.linalg.svd((S - cs).T @ (R - cr))
D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]); Rot = Vt.T @ D @ U.T
M = np.eye(4); M[:3, :3] = Rot; M[:3, 3] = cr - Rot @ cs
err = np.abs((S @ Rot.T + M[:3, 3]) - R).max()
print("ALIGN rot_deg", round(float(np.degrees(np.arccos(np.clip((np.trace(Rot) - 1) / 2, -1, 1)))), 1), "max_err_cm", round(float(err), 3))
if err > 1.0: sys.exit("bodies do not match (pose differs?) max err %.2f cm" % err)
for o in src: o.data.transform(Matrix(M.tolist()))
for o in src: o.select_set(True)
bpy.ops.wm.obj_export(filepath=out_p, export_selected_objects=True, export_uv=True, export_normals=True,
                      export_materials=False, forward_axis="Y", up_axis="Z", export_object_groups=True)
print("WROTE", out_p)
