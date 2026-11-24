import bpy,math,os
from pathlib import Path
from mathutils import Vector
out=Path(r'C:\Users\Apinan\Documents\CC5 Characters\runs\hairmesh_lak_jaew_cc5_test_v1')
for o in bpy.data.objects:
 if o.type=='LIGHT':
  print('LIGHT_BEFORE',o.name,o.data.energy)
  o.data.energy*=.06
for name in ['Natural black-brown hair','Very short hair']:
 m=bpy.data.materials.get(name)
 print('MATERIAL',name,bool(m),list(m.diffuse_color[:]) if m else None)
 if m:
  p=m.node_tree.nodes.get('Principled BSDF')
  if name=='Very short hair':
   p.inputs['Base Color'].default_value=(.018,.015,.014,1)
  else:
   p.inputs['Roughness'].default_value=.58
  m.diffuse_color=(.017,.014,.012,1)
for o in bpy.data.objects:
 if o.get('hairmesh_type')=='live':
  print('LIVE_SHADE',o.name,'material_count',len(o.data.materials),'slots',[(m.name if m else '-') for m in o.data.materials],'faces',len(o.data.polygons),'face_indices',set(f.material_index for f in o.data.polygons))
 if o.name=='Cropped short hair cap':
  print('CAP_MATERIALS',[m.name if m else None for m in o.data.materials])
scene=bpy.context.scene
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.43
scene.view_settings.look='AgX - Medium High Contrast'
cam=scene.camera
def render(name,pos):
 cam.location=pos
 cam.rotation_euler=(Vector((0,0,.687))-cam.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(out/name)
 bpy.ops.render.render(write_still=True)
 print('RENDERED',scene.render.filepath,flush=True)
render('hairmesh_lakjaew_front_v2.png',Vector((0,-1.7,.686)))
render('hairmesh_lakjaew_threequarter_v2.png',Vector((.9,-1.35,.74)))
render('hairmesh_lakjaew_side_v2.png',Vector((1.6,-.06,.71)))
cam.location=(0,-1.7,.686)
cam.rotation_euler=(Vector((0,0,.687))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'CC5_White_Base_LakJaew_HairMesh_v2.blend'),check_existing=False)
print('SAVED_V2',flush=True)

