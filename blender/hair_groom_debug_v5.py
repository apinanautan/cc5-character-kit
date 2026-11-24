import bpy
from pathlib import Path
from mathutils import Vector
root=Path(r'C:\Users\Apinan\Documents\CC5 Characters\runs\hairmesh_lak_jaew_cc5_test_v5')
root.mkdir(exist_ok=True)
for ob in bpy.data.objects:
 if ob.get('hairmesh_type')=='live':
  ob.hide_render=True
  print('HIDE_LIVE',ob.name)
bpy.context.scene.render.filepath=str(root/'test_front.png')
bpy.context.scene.camera.location=(0,-1.7,.686)
bpy.context.scene.camera.rotation_euler=(Vector((0,0,.686))-bpy.context.scene.camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.render.render(write_still=True)
print('RENDERED',bpy.context.scene.render.filepath)
