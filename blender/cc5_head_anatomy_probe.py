import bpy, numpy as np
o=bpy.data.objects['CC_Base_Body'];m=o.data
v=np.array([tuple(x.co) for x in m.vertices])
print('OBJ',o.name,'MATRIX',np.array(o.matrix_world).round(2).tolist(),flush=True)
for lo,hi in [(55,58),(58,60),(60,62),(62,64),(64,66),(66,68),(68,70),(70,72),(72,74),(74,76),(76,78)]:
 p=v[(v[:,2]>=lo)&(v[:,2]<hi)]
 if len(p):
  print('BAND',lo,hi,len(p),'X',np.quantile(p[:,0],[0,.05,.5,.95,1]).round(2).tolist(),'Y',np.quantile(p[:,1],[0,.05,.5,.95,1]).round(2).tolist())
print('OBJECTS',[(x.name,x.type,x.hide_get()) for x in bpy.data.objects])
