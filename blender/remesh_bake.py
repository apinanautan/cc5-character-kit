# Blender (headless, run with CC5 closed): rebuild a crumpled garment as an even quad mesh and bake its texture.
#   blender -b --python blender\remesh_bake.py -- <in.obj> <diffuse.png> <out.obj> <out.png> [faces] [voxel_cm]
# voxel remesh (closes the AI shell's holes) -> QuadriFlow even quads -> shrinkwrap back onto the original shape ->
# smart UV -> bake the original's colour onto the new UVs (selected to active). The new mesh has a new topology,
# so it goes back into CC5 as a new garment with Transfer Skin Weight (cc5\reskin_cloth.py), not ReplaceMesh.
import sys
import bpy

a = sys.argv[sys.argv.index("--") + 1:]
src, tex, out_obj, out_png = a[:4]
faces = int(a[4]) if len(a) > 4 else 8000
voxel = float(a[5]) if len(a) > 5 else 0.6
front_back = "fb" in a  # UV like a sewing pattern: front panel on the left half, back on the right (for GPT to paint)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=src, forward_axis="Y", up_axis="Z")
orig = bpy.context.selected_objects[0]
orig.name = "orig"
mat = bpy.data.materials.new("orig"); mat.use_nodes = True
nt = mat.node_tree
img = nt.nodes.new("ShaderNodeTexImage"); img.image = bpy.data.images.load(tex)
nt.links.new(img.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
orig.data.materials.clear(); orig.data.materials.append(mat)

new = orig.copy(); new.data = orig.data.copy(); new.name = "new"
bpy.context.collection.objects.link(new)
new.data.materials.clear()
bpy.ops.object.select_all(action="DESELECT")
bpy.context.view_layer.objects.active = new; new.select_set(True)
new.data.remesh_voxel_size = voxel
bpy.ops.object.voxel_remesh()
bpy.ops.object.quadriflow_remesh(target_faces=faces, use_preserve_sharp=False, use_mesh_symmetry=False)
sw = new.modifiers.new("fit", "SHRINKWRAP"); sw.target = orig; sw.wrap_method = "NEAREST_SURFACEPOINT"
cs = new.modifiers.new("smooth", "CORRECTIVE_SMOOTH"); cs.iterations = 4; cs.smooth_type = "LENGTH_WEIGHTED"
for m in list(new.modifiers):
    bpy.ops.object.modifier_apply(modifier=m.name)
bpy.ops.object.shade_smooth()

if front_back:
    me = new.data
    xs = [v.co.x for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    size = max(x1 - x0, z1 - z0)
    uv = me.uv_layers.new(name="UVMap") if not me.uv_layers else me.uv_layers[0]
    for poly in me.polygons:
        back = poly.normal.y > 0          # CC5 OBJ: the character faces -Y
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            u = (co.x - x0) / size
            if back:
                u = (x1 - co.x) / size        # mirrored, as seen from behind
            me_u = 0.02 + u * 0.46 + (0.5 if back else 0.0)
            uv.data[li].uv = (me_u, 0.02 + (co.z - z0) / size * 0.96)
else:
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.003)
    bpy.ops.object.mode_set(mode="OBJECT")
bake = bpy.data.images.new("bake", 2048, 2048)
bm = bpy.data.materials.new("bake"); bm.use_nodes = True
bn = bm.node_tree.nodes.new("ShaderNodeTexImage"); bn.image = bake
bm.node_tree.nodes.active = bn
new.data.materials.append(bm)

sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 4
sc.render.bake.use_pass_direct = False; sc.render.bake.use_pass_indirect = False
sc.render.bake.use_selected_to_active = True; sc.render.bake.cage_extrusion = 1.0; sc.render.bake.margin = 8
bpy.ops.object.select_all(action="DESELECT")
orig.select_set(True); new.select_set(True); bpy.context.view_layer.objects.active = new
bpy.ops.object.bake(type="DIFFUSE")
bake.filepath_raw = out_png; bake.file_format = "PNG"; bake.save()

bpy.ops.object.select_all(action="DESELECT"); new.select_set(True)
bpy.ops.wm.obj_export(filepath=out_obj, export_selected_objects=True, export_materials=False,
                      forward_axis="Y", up_axis="Z", export_normals=True, export_uv=True)
print("REMESHED %d faces -> %s" % (len(new.data.polygons), out_obj))
