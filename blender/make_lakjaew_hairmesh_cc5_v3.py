import bpy, math, random, json, traceback
from math import sin,cos,pi,sqrt
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from bl_ext.user_default.hairmesh.core import edit, walls
from bl_ext.user_default.hairmesh.core.vec3 import V3
from bl_ext.user_default.hairmesh.blender import scene_build, project_ops, session, live

OUT=Path(r'C:\Users\Apinan\Documents\CC5 Characters\runs\hairmesh_lak_jaew_cc5_test_v3')
OUT.mkdir(parents=True,exist_ok=True)
random.seed(14)
# Existing cc5 baby as real CC5 anatomical reference. Keep original file intact.
scene=bpy.context.scene
for ob in list(bpy.data.objects):
    if ob.name not in ('CC_Base_Body','CC_Base_Eye'):
        bpy.data.objects.remove(ob,do_unlink=True)
body=bpy.data.objects['CC_Base_Body']
eyes=bpy.data.objects['CC_Base_Eye']
# Frozen clean duplicate, so CC5 skin does not depend on armature in this preview.
for ob in (body,eyes):
    original=ob.matrix_world.copy()
    copy=ob.data.copy()

    for m in list(ob.modifiers):ob.modifiers.remove(m)
    ob.data=copy
    ob.matrix_world=original
def material(name,color,rough=0.5,metal=0):
    m=bpy.data.materials.new(name)
    m.use_nodes=True;m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m
porcelain=material('CC5 clay-white matte',(.79,.77,.73),.91)
hairdark=material('Natural black-brown hair',(.022,.018,.017),.37)
darkside=material('Very short hair',(.035,.031,.030),.62)
bg=material('background slate grey',(.11,.12,.14),.83)
for ob in (body,eyes):
    ob.data.materials.clear();ob.data.materials.append(porcelain)
    for poly in ob.data.polygons:poly.use_smooth=True
body.name='CC5 WHITE mannequin - original CC5 body'
eyes.name='CC5 WHITE eyes'
# Body coordinates from the CC5 baby file are centimeters; world scale already .01.
bpy.context.view_layer.update()
v=[body.matrix_world@q.co for q in body.data.vertices]
# Extract head faces only, for HairMesh's actual Head in project source, separate from visible CC5 mannequin.
verts=[];faces=[];indices={}
for f in body.data.polygons:
    src=list(f.vertices)
    center=sum([v[j].z for j in src])/len(src)
    if center<.601: continue
    poly=[]
    for old in src:
        if old not in indices:
            indices[old]=len(verts)
            verts.append(tuple(v[old]))
        poly.append(indices[old])
    faces.append(poly)
mesh=bpy.data.meshes.new('CC5 head only geometry reference')
mesh.from_pydata(verts,[],faces);mesh.update()
head=bpy.data.objects.new('CC5 head source for HairMesh',mesh)
scene.collection.objects.link(head)
# Create actual HairMesh project, with the CC5 mesh as the head source.
proj=edit.new_project('LakJaew_ThaiMensHair.hairmesh')
root,col=scene_build.make_root(bpy.context,'LakJaew CC5 HairMesh',proj,scale=1.0)
project_ops.set_head_object(bpy.context,root,proj,head)
head.hide_render=True
print('CC5_HEAD_ADDED',len(verts),'head_height',proj.S.headH,flush=True)

# Short clipped sides, fitted to measured CC5 head bounds; no short hair spikes.
# Profile approximation of scalp, stays just outside white skin.
cx,cy,cz=0.,-.022,.665
rx,ry,rz=.066,.077,.104
def skull(x,y):
    r=((x-cx)/rx)**2+((y-cy)/ry)**2
    return cz+rz*sqrt(max(.005,1-r))
def cap_edge(phi):
    # a sharper high-cut frontal hairline, taper lower behind ear and nape
    sy=sin(phi)
    return 1.47 + .22*max(0,sy) - .56*max(0,-sy)
head_bvh=BVHTree.FromPolygons([Vector(p) for p in verts],[tuple(f) for f in faces],all_triangles=False)
verts_cap=[];faces_cap=[]
rings=30;side=144
for j in range(rings+1):
    for i in range(side):
        phi=2*pi*i/side
        t=j/rings * cap_edge(phi)
        xx=cx+(rx+.0015)*sin(t)*cos(phi)
        yy=cy+(ry+.0015)*sin(t)*sin(phi)
        zz=cz+(rz+.0015)*cos(t)
        cp,norm,idx,dd=head_bvh.find_nearest(Vector((xx,yy,zz)),.04)
        if cp is not None and dd<.029:
            # Follow actual CC5 scalp instead of the approximate ellipsoid.
            normal=Vector(norm)
            direction=Vector((xx-cx,yy-cy,zz-cz))
            if normal.dot(direction)>0:
                cp=cp+normal*.00145
                verts_cap.append(tuple(cp))
            else: verts_cap.append((xx,yy,zz))
        else: verts_cap.append((xx,yy,zz))
for j in range(rings):
    for i in range(side):
        a=j*side+i;b=j*side+(i+1)%side
        c=(j+1)*side+(i+1)%side;d=(j+1)*side+i
        faces_cap.append((a,b,c,d))
mesh=bpy.data.meshes.new('Short back and sides mesh')
mesh.from_pydata(verts_cap,[],faces_cap);mesh.materials.append(darkside)
side_obj=bpy.data.objects.new('Cropped short hair cap',mesh);scene.collection.objects.link(side_obj)
for f in mesh.polygons:f.use_smooth=True
# HairMesh curves: top left & right sweeps with a distinct center part.
# Edges are driven by HairMesh curve anchors and walls, not stand-alone custom ribbons.
topcount=16
groups=[]
for sign in (-1,1):
    g=edit.addItem(proj,'group',None,{'name':'LEFT SWEEP' if sign<0 else 'RIGHT SWEEP'})
    groups.append(g)
    edge_curves=[]
    for j in range(topcount+1):
        u=j/topcount
        cur=edit.makeCurve(proj,g.id)
        cur.name=f'Parted sweep {sign:+d} strand {j:02d}'
        edit.newCurveLook(cur)
        cur.round=.62;cur.fair=.66
        for k in range(8):
            t=k/7
            # from front hairline to rear crown; comb tracks splay outward to temples
            xx=sign*(.005 + .059*u + .006*sin(pi*t)*(u-.30))
            yy=-.088 + .126*t + .002*cos(pi*u)
            # CC5 head top (front & rear): scalp cap upper shell
            zz=skull(xx,yy) + .0035 + (.011-.002*u)*sin(pi*t)**1.25 + .0015*(1-u)*sin(2*pi*t) 
            # height at hairline slightly lifted so hair can comb backward, not stick flat
            zz+=.0045*(1-t)**4
            a=edit.newAnchor(proj,V3(xx,zz,-yy))
            cur.anchors.append(a)
        edge_curves.append(cur)
    for j in range(topcount):
        surf=walls.makeSurface(proj,edge_curves[j],edge_curves[j+1])
        if surf:
            surf.p={'segs':2,'bulge':.11,'flip':False}
print('HAIRMESH_CURVES',len(proj.curves()),'HAIRMESH_WALLS',len(proj.surfaces()),flush=True)
session.save_project(root,proj,head=True)
scene.hairmesh.live_preview=True
out=live.update(bpy.context,root)
print('LIVE_RESULT',len(out),flush=True)
real_meshes=[]
for o in bpy.data.objects:
    if o.get('hairmesh_type')=='live':
        if o.type=='MESH':
            real_meshes.append(o)
            o.data.materials.clear();o.data.materials.append(hairdark)
            for p in o.data.polygons:p.use_smooth=True
        print('HAIRMESH_LIVE',o.name,o.type,len(o.data.vertices) if o.type=='MESH' else '-',flush=True)
assert len(real_meshes)>0, 'HairMesh created no native live meshes'
assert sum(len(o.data.polygons) for o in real_meshes)>500, 'HairMesh geometry unexpectedly empty'

# Keep generated source and rendered HairMesh walls visible but hide Head overlay.
head.hide_render=True
head.hide_set(True)
root.hide_render=True
# Custom shader with directional color streaks not hair cards.
p=hairdark.node_tree.nodes.get('Principled BSDF')
tex=hairdark.node_tree.nodes.new('ShaderNodeTexNoise')
tex.inputs['Scale'].default_value=1100
tex.inputs['Roughness'].default_value=.3
ramp=hairdark.node_tree.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position=.24
ramp.color_ramp.elements[0].color=(.013,.010,.009,1)
ramp.color_ramp.elements[1].position=.75
ramp.color_ramp.elements[1].color=(.069,.055,.047,1)
hairdark.node_tree.links.new(tex.outputs['Fac'],ramp.inputs['Fac'])
hairdark.node_tree.links.new(ramp.outputs['Color'],p.inputs['Base Color'])

def add_area(name,location,energy,color,size):
    l=bpy.data.lights.new(name,'AREA');l.energy=energy;l.color=color;l.shape='DISK';l.size=size
    o=bpy.data.objects.new(name,l);scene.collection.objects.link(o);o.location=location
    o.rotation_euler=(Vector((0,0,.7))-o.location).to_track_quat('-Z','Y').to_euler()
add_area('large soft light',(-.6,-.6,1.2),5.4,(1.0,.94,.84),.9)
add_area('cool highlight',(.45,.28,1.13),3.6,(.78,.86,1.0),.6)
add_area('soft fill',(.35,-.6,.84),2.4,(1,1,1),.7)
world=bpy.data.worlds.new('grey studio environment')
scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.22,.22,.24,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.43

camera_data=bpy.data.cameras.new('HAIR PREVIEW CAMERA')
camera=bpy.data.objects.new('HAIR PREVIEW CAMERA',camera_data);scene.collection.objects.link(camera)
scene.camera=camera;camera_data.type='ORTHO';camera_data.ortho_scale=.34
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=900;scene.render.resolution_y=1050
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
def render(name,cam):
    camera.location=cam
    camera.rotation_euler=(Vector((0,0,.686))-camera.location).to_track_quat('-Z','Y').to_euler()
    path=OUT/name;scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
    print('RENDER',str(path),path.stat().st_size,flush=True)
# portrait front and right three quarter, and side showing fade.
render('hairmesh_lakjaew_front.png',Vector((0,-1.7,.686)))
render('hairmesh_lakjaew_threequarter.png',Vector((.9,-1.35,.74)))
render('hairmesh_lakjaew_side.png',Vector((1.6,-.06,.71)))
# restore camera front in saved file, select project root.
camera.location=(0,-1.7,.686)
camera.rotation_euler=(Vector((0,0,.686))-camera.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.select_all(action='DESELECT');root.select_set(True);bpy.context.view_layer.objects.active=root
target=OUT/'CC5_White_Base_LakJaew_HairMesh_v3.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
print('SAVED',target,target.stat().st_size,flush=True)

