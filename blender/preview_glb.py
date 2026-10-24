# Blender headless: render a GLB from 3 angles + report mesh stats (faces, is it hollow / open).
#   blender -b --python blender/preview_glb.py -- model.glb out.png
import bpy, bmesh, math, sys
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
faces = sum(len(o.data.polygons) for o in objs)
bm = bmesh.new()
for o in objs:
    bm.from_mesh(o.data)
open_edges = sum(1 for e in bm.edges if e.is_boundary)
print("STATS faces=%d verts=%d open_edges=%d objects=%d" % (faces, len(bm.verts), open_edges, len(objs)))
mn = Vector((min(v[i] for o in objs for v in [o.matrix_world @ c for c in [Vector(b) for b in o.bound_box]]) for i in range(3)))
mx = Vector((max(v[i] for o in objs for v in [o.matrix_world @ c for c in [Vector(b) for b in o.bound_box]]) for i in range(3)))
ctr, size = (mn + mx) / 2, max(mx - mn)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1500, 600
world = bpy.data.worlds.new("w"); world.color = (0.75, 0.75, 0.78); scene.world = world
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), 0, math.radians(30)); scene.collection.objects.link(sun)
# three copies side by side: front, 3/4, back
cams = []
import tempfile, os
tiles = []
for i, ang in enumerate((0, 45, 180)):
    cam = bpy.data.objects.new("cam%d" % i, bpy.data.cameras.new("c%d" % i))
    scene.collection.objects.link(cam)
    r = size * 2.2
    th = math.radians(ang)
    cam.location = ctr + Vector((math.sin(th) * r, -math.cos(th) * r, size * 0.15))
    cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = 500, 600
    p = os.path.join(tempfile.gettempdir(), "prev_%d.png" % i)
    scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    tiles.append(p)
imgs = [bpy.data.images.load(p) for p in tiles]
w, h = imgs[0].size
out = bpy.data.images.new("sheet", w * 3, h)
px = [0.0] * (w * 3 * h * 4)
for k, im in enumerate(imgs):
    src = list(im.pixels)
    for y in range(h):
        row = src[y * w * 4:(y + 1) * w * 4]
        px[(y * w * 3 + k * w) * 4:(y * w * 3 + k * w + w) * 4] = row
out.pixels = px
out.filepath_raw = a[1]; out.file_format = "PNG"; out.save()
print("WROTE", a[1])
