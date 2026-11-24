"""Read-only Preview bridge for explicitly registered clothing AI jobs."""
import argparse
import json
import re
import struct
import time
import urllib.request
from pathlib import Path
from ai_cc5_state import State, identifier, load, save, lock, digest

PHASES = {
    "image": "สร้างภาพเสื้อ T-Pose",
    "generate": "สร้าง Mesh 3D",
    "decimate": "ลด Polygon",
    "uv": "จัดเรียง UV",
    "texture": "สร้าง Texture",
    "mesh_ready": "สร้างชุด 3D เสร็จ",
    "fit": "ฟิตชุด / Skin Weight",
    "render": "เรนเดอร์ตรวจชุด",
    "complete": "ตรวจชุด 3D เสร็จ",
    "blocked": "สร้างชุด 3D มีปัญหา",
    "cancelled": "ยกเลิกชุด 3D",
}
SERVER = "http://127.0.0.1:8188"

def registry(store, story):
    return store.runs / identifier(story) / "cloth3d_progress.json"

def task(store, state):
    if not state.get("story") or not state.get("actor"):
        return None
    item=load(registry(store,state["story"]),{}) or {}
    if any(item.get(k)!=state.get(k) for k in ("story","actor","label")):
        return None
    # A registered 20-step garment flow (flow_preview) supersedes an older StableGen job of the same round.
    flow=store.runs/identifier(state["story"])/"ai_cc5"/identifier(state["label"])/"garment"/"flow_config.json"
    if flow.is_file() and flow.stat().st_mtime>float(item.get("updated") or 0):
        return None
    return item if item.get("stage") in PHASES and item["stage"]!="cancelled" else None

def glb_info(path):
    path=Path(path)
    with path.open("rb") as f:
        magic,version,size=struct.unpack("<4sII",f.read(12))
        if magic!=b"glTF" or version!=2 or size!=path.stat().st_size:
            raise ValueError("Invalid GLB")
        n,typ=struct.unpack("<I4s",f.read(8))
        if typ!=b"JSON" or n>32*1024*1024:raise ValueError("Invalid GLB JSON")
        data=json.loads(f.read(n))
    primitives=[p for m in data.get("meshes",[]) for p in m.get("primitives",[])]
    if not primitives:raise ValueError("Empty mesh")
    faces=sum(data["accessors"][p["indices"]]["count"]//3 if "indices" in p else data["accessors"][p["attributes"]["POSITION"]]["count"]//3 for p in primitives if p.get("mode",4)==4)
    uv=sum("TEXCOORD_0" in p.get("attributes",{}) for p in primitives)
    if not faces or not uv or not data.get("images"):raise ValueError("Mesh/UV/texture missing")
    return {"faces":faces,"uv":uv,"images":len(data["images"])}

def request(endpoint):
    with urllib.request.urlopen(SERVER+endpoint,timeout=.65) as response:
        return json.load(response)

def log_progress(text):
    # Current phase percentage, not an estimated whole-job percentage.
    for line in reversed(text.splitlines()):
        match=re.search(r"(\d{1,3})%\|.*?\|\s*([\d,]+)/([\d,]+)",line)
        if not match:continue
        done,total=(int(x.replace(",","")) for x in match.groups()[1:])
        if not total or done>total:continue
        if "unwrap:" in line.lower():
            label="UV Packing" if "pack:" in line.lower() else "UV Unwrap"
            return "uv",done,total,label
        if "bake texture" in line.lower():return "texture",done,total,"Texture Bake"
        if "decimat" in line.lower():return "decimate",done,total,"Decimate"
        return "generate",done,total,"TRELLIS.2 sampling"
    return None

def display(store,state):
    item=task(store,state)
    if not item:return None
    stage=item["stage"]
    done=item.get("done",0);total=item.get("total",0)
    detail=item.get("detail","")
    if stage=="generate" and item.get("prompt_id"):
        try:
            pid=item["prompt_id"]
            history=request("/history/"+pid).get(pid)
            if history:
                status=history.get("status",{})
                if status.get("status_str")=="success" and status.get("completed"):
                    outputs=[x for n in history.get("outputs",{}).values() for x in n.get("3d",[]) if x.get("type")=="output"]
                    if len(outputs)!=1:raise ValueError("Output count is not one")
                    output=outputs[0]
                    root=Path(item["output_root"]).resolve()
                    path=(root/output.get("subfolder","")/output["filename"]).resolve()
                    if not path.is_relative_to(root):raise ValueError("Output outside expected directory")
                    info=glb_info(path)
                    return ("mesh_ready",1.0,f'{info["faces"]:,} สามเหลี่ยม · UV/Texture พร้อม · รอตรวจ Mesh ก่อนฟิต')
                return ("blocked",None,"งาน TRELLIS.2 ไม่สำเร็จ / ถูกยกเลิก")
            q=request("/queue")
            running=q.get("queue_running",[])
            if len(running)==1 and running[0][1]==pid:
                log=Path(item["log"])
                with log.open("rb") as f:
                    size=log.stat().st_size
                    f.seek(max(int(item.get("log_offset",0)),size-65536))
                    raw=f.read().decode("utf-8",errors="replace")
                current=log_progress(raw)
                if current:
                    stage,done,total,detail=current
                else:
                    detail="กำลังโหลดโมเดล / ยังไม่มีตัวเลขจากระบบ"
            elif any(x[1]==pid for x in q.get("queue_pending",[])):
                return ("generate",0.0,"รอคิว StableGen")
            else:
                return ("blocked",None,"ไม่พบคิวหรือผลสำเร็จของงานที่ลงทะเบียน")
        except (OSError,ValueError,KeyError,TypeError,struct.error) as exc:
            return ("generate",None,"อ่านสถานะ StableGen ไม่ได้: "+type(exc).__name__)
    level=done/total if isinstance(total,(int,float)) and total>0 and isinstance(done,(int,float)) and 0<=done<=total else None
    if stage=="mesh_ready":
        try:
            info=glb_info(item["mesh"])
            return stage,1.0,f'{info["faces"]:,} สามเหลี่ยม · UV/Texture พร้อม · รอตรวจ Mesh ก่อนฟิต'
        except (OSError,ValueError,KeyError,struct.error):
            return "blocked",None,"ไฟล์ GLB ไม่ผ่านการตรวจ"
    if level is not None:
        detail=(detail+" · " if detail else "")+f"{done:,}/{total:,}"
    return stage,level,detail or PHASES[stage]

def active(store,state):
    item=task(store,state)
    return bool(item and item["stage"] not in ("complete","cancelled"))

def require_visual_gate(item, evidence, stage):
    """Require explicit visual QA on the exact mesh and evidence images."""
    if not evidence:
        raise ValueError("ต้องตรวจภาพจริงและบันทึกผล PASS ก่อนทำขั้นถัดไป")
    report=load(Path(evidence),{}) or {}
    mesh=Path(item["mesh"])
    if report.get("status")!="PASS" or report.get("stage")!=stage or report.get("mesh_sha256")!=digest(mesh):
        raise ValueError("Visual QA ไม่ผ่าน หรือหลักฐานไม่ตรง Mesh ปัจจุบัน")
    keys=("fabric_continuity","silhouette","no_unintended_holes","topology","texture") if stage=="mesh" else ("fabric_continuity","silhouette","no_unintended_holes","texture","no_clipping","pose_deformation")
    if any(report.get("checks",{}).get(k) is not True for k in keys):
        raise ValueError("Visual QA ยังตรวจไม่ครบหรือมีข้อผิดพลาด")
    views=("front","side","back") if stage=="mesh" else ("front","side","back","t_pose","motion")
    for v in views:
        record=report.get("views",{}).get(v,{})
        path=Path(record.get("path",""))
        if not path.is_file() or digest(path)!=record.get("sha256"):
            raise ValueError("หลักฐานภาพหายหรือเปลี่ยน: "+v)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage",choices=PHASES)
    p.add_argument("--done",type=int,default=0)
    p.add_argument("--total",type=int,default=0)
    p.add_argument("--detail",default="")
    p.add_argument("--prompt-id")
    p.add_argument("--log",type=Path)
    p.add_argument("--log-offset",type=int,default=0)
    p.add_argument("--output-root",type=Path)
    p.add_argument("--mesh",type=Path)
    p.add_argument("--source",type=Path)
    p.add_argument("--evidence",type=Path)
    a=p.parse_args()
    s=State()
    with lock(s.runs/".cloth3d_progress.lock"):
        st=s.active()
        assert st.get("story") and st.get("actor") and st.get("label")
        assert 0<=a.done<=a.total
        prior=task(s,st) or {}
        item={**prior,**{k:st[k] for k in ("story","actor","label")},"stage":a.stage,
              "done":a.done,"total":a.total,"detail":a.detail,"updated":time.time()}
        if a.source:
            if not a.source.is_file():raise ValueError("Source not found")
            item["source"]=str(a.source.resolve())
        if a.stage=="generate":
            if not (a.prompt_id and a.log and a.output_root):raise ValueError("Need prompt id, log, output root")
            item.update(prompt_id=a.prompt_id,log=str(a.log.resolve()),log_offset=a.log_offset,output_root=str(a.output_root.resolve()))
        if a.stage=="mesh_ready":
            item.pop("mesh_qa",None)
            item.pop("evidence",None)
            if not a.mesh:raise ValueError("Need verified mesh")
            item.update(mesh=str(a.mesh.resolve()),mesh_info=glb_info(a.mesh))
        if a.stage in ("fit","render","complete"):
            mesh_qa=a.evidence if a.stage=="fit" and a.evidence else item.get("mesh_qa")
            require_visual_gate(item,mesh_qa,"mesh")
            item["mesh_qa"]=str(Path(mesh_qa).resolve())
        if a.stage=="complete":
            require_visual_gate(item,a.evidence,"fitted")
            item["evidence"]=str(a.evidence.resolve())
        save(registry(s,st["story"]),item)
        print(json.dumps(item,ensure_ascii=False))
if __name__=="__main__":main()
