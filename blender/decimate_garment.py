# Blender headless: make an AI garment lighter WITHOUT remeshing: weld the torn seams, reduce faces with Decimate,
# keep the original UVs + texture. Light on RAM and seconds to run.
#   blender -b --python blender/decimate_garment.py -- <in.obj (Y-up, textured)> <out.obj> [faces] [scale]
import bpy, bmesh, os, sys

a = sys.argv[sys.argv.index("--") + 1:]
src, out = a[:2]
faces = int(a[2]) if len(a) > 2 else 12000
scale = float(a[3]) if len(a) > 3 else 1.0  # 100 = Hunyuan's metres -> CC5 centimetres
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=src, forward_axis="NEGATIVE_Z", up_axis="Y")
o = [x for x in bpy.context.scene.objects if x.type == "MESH"][0]
bm = bmesh.new(); bm.from_mesh(o.data)
if scale != 1.0:
    bmesh.ops.scale(bm, vec=(scale, scale, scale), verts=bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005 * max(scale, 1.0))  # weld torn seams; UVs stay per corner
bm.to_mesh(o.data); bm.free()
n0 = len(o.data.polygons)
bpy.context.view_layer.objects.active = o
o.select_set(True)
if n0 > faces:
    d = o.modifiers.new("dec", "DECIMATE"); d.ratio = faces / n0; d.use_collapse_triangulate = True
    d.delimit = {"UV"}  # do not merge across texture seams -> texture stays right
    bpy.ops.object.modifier_apply(modifier="dec")
for poly in o.data.polygons:  # smooth shading: no faceted look
    poly.use_smooth = True
print("DECIMATE %d -> %d faces" % (n0, len(o.data.polygons)))
for img in bpy.data.images:  # write textures next to the OBJ
    if img.size[0]:
        p = os.path.join(os.path.dirname(out), os.path.basename(bpy.path.abspath(img.filepath)) or img.name + ".png")
        if not os.path.exists(p):
            img.filepath_raw = p; img.save()
bpy.ops.wm.obj_export(filepath=out, export_selected_objects=True, forward_axis="NEGATIVE_Z", up_axis="Y",
                      export_materials=True, path_mode="COPY", export_normals=True, export_uv=True,
                      export_smooth_groups=True)
print("WROTE", out)
