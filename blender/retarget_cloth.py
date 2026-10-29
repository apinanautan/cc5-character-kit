# Blender (headless, CC5 closed): carry garments worn by one CC character over to another body shape (adult -> kid)
# without squeezing them: Surface Deform binds each garment to the source body, then the source body takes the
# target's shape (all CC bodies share CC_Base_Body's topology) and the garment follows, wrinkles / seams / UVs
# kept. Inputs are CC5 T-pose OBJs (cc5\smooth_cloth.py step=export). Output OBJs are Y-up for LoadAccessory.
#   blender -b --python blender\retarget_cloth.py -- <src_body.obj> <dst_body.obj> <out_dir> <cloth.obj> [...]
import os, sys
import bpy

a = sys.argv[sys.argv.index("--") + 1:]
src_body, dst_body, out_dir = a[:3]
cloths = a[3:]


def body_part(path):
    """CC_Base_Body vertices + faces from a CC5 OBJ (its index block, re-based to 0)."""
    allv, faces, group = [], [], None
    for line in open(path, encoding="utf-8", errors="ignore"):
        if line.startswith("g "):
            group = line[2:].strip()
        elif line.startswith("v "):
            allv.append(tuple(map(float, line.split()[1:4])))
        elif line.startswith("f ") and group == "CC_Base_Body":
            faces.append([int(t.split("/")[0]) - 1 for t in line.split()[1:]])
    used = sorted({i for f in faces for i in f})   # the body's own vertices, in file order
    remap = {old: new for new, old in enumerate(used)}
    return [allv[i] for i in used], [[remap[i] for i in f] for f in faces]


bpy.ops.wm.read_factory_settings(use_empty=True)
sv, sf = body_part(src_body)
dv, _ = body_part(dst_body)
if len(sv) != len(dv):
    raise SystemExit("bodies differ: %d vs %d vertices" % (len(sv), len(dv)))
me = bpy.data.meshes.new("body"); me.from_pydata(sv, [], sf)
body = bpy.data.objects.new("body", me); bpy.context.collection.objects.link(body)
body.shape_key_add(name="Basis")
kid = body.shape_key_add(name="dst")
for i, co in enumerate(dv):
    kid.data[i].co = co
kid.value = 0.0

for c in cloths:
    bpy.ops.wm.obj_import(filepath=c, forward_axis="Y", up_axis="Z")  # identity: raw CC5 coordinates
    ob = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = ob
    sd = ob.modifiers.new("follow", "SURFACE_DEFORM"); sd.target = body; sd.falloff = 4.0
    bpy.ops.object.surfacedeform_bind(modifier="follow")
    kid.value = 1.0
    bpy.context.view_layer.update()
    bpy.ops.object.modifier_apply(modifier="follow")
    kid.value = 0.0
    out = os.path.join(out_dir, os.path.splitext(os.path.basename(c))[0] + "_kid.obj")
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True)
    bpy.ops.wm.obj_export(filepath=out, export_selected_objects=True, export_materials=False,
                          forward_axis="NEGATIVE_Z", up_axis="Y", export_uv=True, export_normals=True)
    print("RETARGET %s -> %s (%d verts)" % (os.path.basename(c), out, len(ob.data.vertices)))
    bpy.data.objects.remove(ob)
