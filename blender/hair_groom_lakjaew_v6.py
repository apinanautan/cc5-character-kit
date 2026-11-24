import bpy, math, random
from math import sin,cos,pi,sqrt,exp
from mathutils import Vector
from pathlib import Path
out=Path(r'C:\Users\Apinan\Documents\CC5 Characters\runs\hairmesh_lak_jaew_cc5_test_v6')
out.mkdir(parents=True,exist_ok=True)
random.seed(619)
scene=bpy.context.scene
for obj in bpy.data.objects:
    if obj.get('hairmesh_type')=='live' or obj.name.startswith(('Flow hair fine strands','Short fuzzy fade strands')):
        obj.hide_render=True
cap=bpy.data.objects.get('Cropped short hair cap')
# Vertex-colour the short hair cap: dark on top, gradually skin-coloured near temple fade.
m=bpy.data.materials.get('Very short hair')
nodes=m.node_tree.nodes;links=m.node_tree.links
attr=nodes.new('ShaderNodeAttribute');attr.attribute_name='scalp_fade'
links.new(attr.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])

ca=cap.data.color_attributes.new(name='scalp_fade',type='FLOAT_COLOR',domain='CORNER')
for poly in cap.data.polygons:
    for loopind in poly.loop_indices:
        vid=cap.data.loops[loopind].vertex_index
        q=vid//144/30
        t=max(0,min(1,(q-.43)/.57))
        f=t*t*(3-2*t)
        # Dark upper hair, fade down into the neutral gray-white CC5 scalp.
        rgb=tuple((.022,.020,.018)[j]*(1-f)+(.79,.77,.73)[j]*f for j in range(3))
        ca.data[loopind].color=(*rgb,1)
cap.data.materials.clear();cap.data.materials.append(m)
# Use smooth subtle cinematic materials; NOT the huge original HairMesh ribbons.
haircols=[(.021,.016,.014),(.031,.024,.021),(.042,.034,.03),(.015,.012,.011)]
mats=[]
for i,c in enumerate(haircols):
    mat=bpy.data.materials.new(f'LakJaew groom shade {i}');mat.diffuse_color=(*c,1);mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*c,1)
    bs.inputs['Roughness'].default_value=.43+0.03*i
    mats.append(mat)
cx,cy,cz=0,-.022,.665
rx,ry,rz=.066,.077,.104
def skull(x,y):
    return cz+rz*sqrt(max(.001,1-((x-cx)/rx)**2-((y-cy)/ry)**2))
def path(sign,u,t,jitter=0):
    q=max(0,min(1,u))
    xx=sign*(.0018+.0543*q+.003*sin(pi*t)*q**.6)+sign*jitter*.3
    # Curved frontal hairline rises at center, and recedes at temples.
    root_y=cy-.066*sqrt(max(.08,1-(xx/.074)**2))
    end_y=cy+.064*sqrt(max(.08,1-(xx/.074)**2))
    yy=root_y+(end_y-root_y)*(t*.93+.07*sin(pi*t))
    yy+=jitter*(1-t)
    scalp=skull(xx,yy)
    # Build quiff height near frontal section, then comb back naturally.
    h=.003 + (.034*(1-.34*q))*(1-exp(-11*t))*exp(-1.95*t)+.009*sin(pi*t)**1.4
    zz=scalp+h
    return Vector((xx,yy,zz))
# Thick fine clumps, each a volumetric flattened fiber rather than a flat rectangular sheet.
def volume_locks(sign,u,k):
    vertices=[];faces=[]; nring=32; sides=8
    hue_group=random.choices(range(4),[52,28,11,9])[0]
    root_j=random.uniform(-.0011,.0011)
    width=random.uniform(.0014,.0020)
    for i in range(nring+1):
        t=i/nring
        q=max(.025,(1-(t**5)*.98))
        center=path(sign,u,t,root_j)
        # cross section width in x direction and thickness vertical
        w=width*q*(.68+.33*sin(pi*t))
        depth=.0007*q
        for j in range(sides):
            a=2*pi*j/sides
            rr=Vector((w*cos(a),0,depth*sin(a)))
            vertices.append(tuple(center+rr))
    for i in range(nring):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides
            faces.append((a,b,b+sides,a+sides))
    mesh=bpy.data.meshes.new('groomed lock')
    mesh.from_pydata(vertices,[],faces)
    mesh.materials.append(mats[hue_group])
    ob=bpy.data.objects.new(f'LakJaew top lock {sign:+d} {k:02d}',mesh)
    scene.collection.objects.link(ob)
    for p in mesh.polygons:p.use_smooth=True
for sign in (-1,1):
    for i in range(27):
        volume_locks(sign,(i+.55)/27,i)
def make_fiber(name,strands,material,r):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=10;data.bevel_depth=r;data.bevel_resolution=2
    for pts in strands:
        s=data.splines.new('POLY');s.points.add(len(pts)-1)
        for i,(pt,bp) in enumerate(zip(pts,s.points)):
            bp.co=(*pt,1)
            bp.radius=max(.05,(1-i/(len(pts)-1))**.4)
    ob=bpy.data.objects.new(name,data)
    scene.collection.objects.link(ob);data.materials.append(material)
fibers=[[] for _ in range(4)]
for sign in (-1,1):
    for i in range(3400):
        u=random.uniform(.006,.986)
        shift=random.gauss(0,.0010)
        drift=random.gauss(0,.0007)
        n=16
        pts=[]
        for j in range(n):
            t=j/(n-1)
            v=path(sign,min(.99,max(.005,u+drift*t)),t,shift)
            v.z+=random.uniform(.00075,.0019)
            pts.append(v)
        fibers[random.choices(range(4),[42,29,18,11])[0]].append(pts)
for k,grp in enumerate(fibers):
    make_fiber(f'LakJaew silky short strand fibers {k}',grp,mats[k],.000077)
print('PROCEDURAL_LOCKS',54,'PROCEDURAL_FIBERS',sum(len(x) for x in fibers),flush=True)
# mild fill lighting, restore soft black specular without a glossy plastic helmet
for obj in bpy.data.objects:
    if obj.type=='LIGHT':
        obj.data.energy*=1.3
scene.render.resolution_x=940
scene.render.resolution_y=1070
scene.render.resolution_percentage=100
cam=scene.camera
def render(name,pos):
    cam.location=pos
    cam.rotation_euler=(Vector((0,0,.685))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(out/name)
    bpy.ops.render.render(write_still=True)
    print('RENDERED',scene.render.filepath,flush=True)
render('actual_front.png',Vector((0,-1.7,.69)))
render('actual_threequarter.png',Vector((.9,-1.35,.74)))
render('actual_side.png',Vector((1.6,-.06,.71)))
cam.location=(0,-1.7,.69)
cam.rotation_euler=(Vector((0,0,.685))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'CC5_White_Base_LakJaew_HairMesh_Groom_v6.blend'),check_existing=False)
print('SAVED_FINISHED',str(out),flush=True)

