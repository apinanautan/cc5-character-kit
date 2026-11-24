# Headless: raw TRELLIS glb -> clean quad mesh (QuadriFlow, built into Blender). Never touches the input.
# blender -b -P quad_remesh.py -- <raw.glb> <out.glb> <quad_faces>
import bpy, bmesh, sys, time
a = sys.argv[sys.argv.index("--") + 1:]; src, dst, nq = a[0], a[1], int(a[2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = [x for x in bpy.context.scene.objects if x.type == "MESH"][0]
bpy.context.view_layer.objects.active = o; o.select_set(True)
t = time.time()
bm = bmesh.new(); bm.from_mesh(o.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
print("RAW faces", len(bm.faces), "boundary", sum(1 for e in bm.edges if e.is_boundary),
      "nonmanifold", sum(1 for e in bm.edges if not e.is_manifold))
bm.to_mesh(o.data); bm.free()
# keep the largest piece (drop crumbs)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT")
bpy.ops.mesh.separate(type="LOOSE"); bpy.ops.object.mode_set(mode="OBJECT")
parts = [x for x in bpy.context.scene.objects if x.type == "MESH"]
o = max(parts, key=lambda x: len(x.data.polygons))
for x in parts:
    if x is not o: bpy.data.objects.remove(x)
bpy.context.view_layer.objects.active = o; o.select_set(True)
# pre-reduce (fast C collapse) so QuadriFlow does not choke on millions of faces
m = o.modifiers.new("dec", "DECIMATE"); m.ratio = min(1.0, 400000 / len(o.data.polygons))
bpy.ops.object.modifier_apply(modifier="dec")
print("pre-decimated", len(o.data.polygons), round(time.time() - t), "s")
r = bpy.ops.object.quadriflow_remesh(target_faces=nq, use_preserve_sharp=True, use_mesh_symmetry=False, smooth_normals=False)
print("quadriflow", r, len(o.data.polygons), round(time.time() - t), "s")
bpy.ops.export_scene.gltf(filepath=dst, use_selection=True, export_materials="NONE")
print("WROTE", dst)
