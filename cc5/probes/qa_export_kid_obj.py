# QA-only: export donor child's working clothing from CC5 in A-pose, no save.
import os,json,RLPy
a=BRIDGE_ARGS; d=a["job"]; dst=a["out"]
name=json.load(open(os.path.join(d,"job.json"),encoding="utf-8-sig"))["name"]
RLPy.RFileIO.LoadFile(os.path.join(d,name+".ccProject"))
av=RLPy.RScene.GetAvatars()[0];RLPy.RScene.SelectObject(av)
pose=r"C:\Users\Public\Documents\Reallusion\Reallusion Templates\Animation\Pose\Calibration\A-Pose.rlPose"
RLPy.RFileIO.LoadFile(pose)
os.makedirs(dst,exist_ok=True)
log=[]
for c in av.GetClothes():
 role=("shirt" if c.GetName()=="node_0" else ("jong" if c.GetName()=="new" else "other"))
 if role=="other":continue
 path=os.path.join(dst,"donor_apose_"+role+"_zup.obj")
 r=RLPy.RFileIO.ExportObjFile(c,path,RLPy.EExport3DFileOption__None)
 log.append("%s -> %s result_error=%s bytes=%d" %(role,path,r.IsError(),os.path.getsize(path) if os.path.exists(path) else 0))
BRIDGE_RESULT="\n".join(log)
