# Blender (headless, CC5 closed or idle): turn a long-sleeve jacket OBJ (CC5 export: cm, Z-up, T-pose) into short sleeves
# with a turned-up cuff.   blender -b --python blender\short_sleeve.py -- <in.obj> <diffuse.png> <out.obj> [cut=33] [cuff=4]
# cut = distance from the body centre (cm) where the sleeve ends; cuff = width (cm) of the folded band, pushed out a bit.
import math, os, shutil, sys
import bmesh, bpy

a = sys.argv[sys.argv.index("--") + 1:]
src, tex, out = a[:3]
opt = dict(x.split("=") for x in a[3:] if "=" in x)
CUT, CUFF, FLARE = float(opt.get("cut", 33)), float(opt.get("cuff", 4)), float(opt.get("flare", 1.10))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=src, forward_axis="Y", up_axis="Z")
o = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = o
bm = bmesh.new(); bm.from_mesh(o.data)

for sign in (1, -1):
    # cut the sleeve off (everything beyond CUT on this side)
    for plane in (CUT * sign, (CUT - CUFF) * sign):
        pass
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(CUT * sign, 0, 0), plane_no=(sign, 0, 0), clear_outer=True)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=((CUT - CUFF) * sign, 0, 0), plane_no=(sign, 0, 0))
    # the sleeve cross-section there: centre of its vertices
    ring = [v for v in bm.verts if abs(abs(v.co.x) - CUT) < 0.3 and v.co.x * sign > 0]
    band = [v for v in bm.verts if (CUT - CUFF) * 1.0 - 0.3 < abs(v.co.x) < CUT + 0.3 and v.co.x * sign > 0]
    if not ring:
        print("NO RING", sign); continue
    cy = sum(v.co.y for v in ring) / len(ring); cz = sum(v.co.z for v in ring) / len(ring)
    for v in band:   # turned-up cuff: the band sits slightly proud of the sleeve
        v.co.y = cy + (v.co.y - cy) * FLARE
        v.co.z = cz + (v.co.z - cz) * FLARE
    print("side", sign, "ring verts", len(ring), "band verts", len(band), "centre y%.1f z%.1f" % (cy, cz))

# close the cut ends with a thin inner lip so no hole shows (fill boundary loops that are the sleeve openings)
bm.edges.ensure_lookup_table()
for sign in (1, -1):
    edges = [e for e in bm.edges if e.is_boundary and all(abs(abs(v.co.x) - CUT) < 0.3 and v.co.x * sign > 0 for v in e.verts)]
    print("opening edges", sign, len(edges))
bm.to_mesh(o.data); bm.free()

bpy.ops.object.select_all(action="DESELECT"); o.select_set(True)
bpy.ops.wm.obj_export(filepath=out, export_selected_objects=True, export_materials=False,
                      forward_axis="NEGATIVE_Z", up_axis="Y", export_uv=True, export_normals=True)
shutil.copy(tex, os.path.splitext(out)[0] + ".png")
print("WROTE", out, "verts", len(o.data.vertices))
