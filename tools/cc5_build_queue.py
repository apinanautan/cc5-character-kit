"""CC5 consumer lane: build any already-rendered face while Tidmunz generates the next.
One CC5 job at a time, no automatic CC5/Windows restart, no chat deletion.
Operates on project story and source asset paths; job staging is temporary under Tidmunz.
"""
import argparse,json,os,re,subprocess,sys,time,traceback
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'studio'))
import kit
from tools.cc5_production_flow import is_png,is_image,ntfy_send,save_json

def now():return time.strftime('%Y-%m-%d %H:%M:%S')
def process_check():
    """Fail closed when the CC5 task environment cannot be observed."""
    ps=r"""
$p=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'python.exe' -and $_.CommandLine -match 'cc5\.py"?\s+run'})
'CC5_CMDS='+$p.Count
$a=Get-Process CharacterCreator -ErrorAction SilentlyContinue
if($a){'CC5_ALIVE=True';'CC5_RESPONDS='+[bool]$a.Responding;'CC5_SCENE_DIRTY='+[bool]($a.MainWindowTitle -match '\*\s*$')}
else{'CC5_ALIVE=False';'CC5_RESPONDS=False';'CC5_SCENE_DIRTY=True'}
"""
    try:
        r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',ps],
              capture_output=True,text=True,timeout=20,encoding='utf-8',errors='replace')
        out=r.stdout
        match=re.search(r'CC5_CMDS=(\d+)',out)
        if r.returncode or not match:
            return False,'Windows process check failed: '+r.stderr[-150:]
        return int(match.group(1))==0 and 'CC5_RESPONDS=True' in out and 'CC5_SCENE_DIRTY=False' in out, out.replace('\n',' ')
    except (OSError,subprocess.TimeoutExpired) as exc:
        return False,type(exc).__name__

def bridge(script,**args):
    argv=[sys.executable,str(ROOT/'tools'/'cc5.py'),'run',str(ROOT/script)]
    argv+=['%s=%s'%pair for pair in args.items()]
    cp=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     timeout=2100,text=True,encoding='utf-8',errors='replace')
    out=cp.stdout[-1600:]
    if cp.returncode:
        raise RuntimeError('CC5 bridge '+script+' code '+str(cp.returncode)+' '+out[-300:])
    return out

def validated_build(job,c):
    d=Path(kit.JOBS)/job
    result=d/'result.txt'
    project=d/(c['name']+'.ccProject')
    image=d/(c['name']+'.png')
    if result.is_file():
        text=result.read_text(encoding='utf-8-sig',errors='replace')
        if any(line.startswith('FAIL') or 'BATCH FAIL' in line for line in text.splitlines()):
            raise RuntimeError('Existing CC5 build reports a real FAIL: '+text[-600:])
    if project.is_file() and project.stat().st_size>4096 and is_png(image) and result.is_file():
        return True,'existing verified render + project'
    if result.is_file() or project.is_file() or image.is_file():
        raise RuntimeError('Partial CC5 build output found; do not overwrite or rerun blindly')
    if not is_png(d/'face.png'):
        raise RuntimeError('Face not ready: '+job)
    plan=subprocess.run([sys.executable,str(ROOT/'tools'/'plan.py'),STORY,job],
                        cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                        text=True,encoding='utf-8',errors='replace',timeout=900)
    if plan.returncode:
        raise RuntimeError('Plan failure: '+plan.stdout[-550:])
    print('CC5_START_HEADSHOT',job,now(),flush=True)
    out=bridge('cc5/build.py')
    if not result.is_file():
        raise RuntimeError('CC5 finished without result.txt: '+out[-350:])
    text=result.read_text(encoding='utf-8-sig',errors='replace')
    if any(line.startswith('FAIL') or 'BATCH FAIL' in line for line in text.splitlines()):
        raise RuntimeError('CC5 Headshot/clothes failure: '+text[-800:])
    if not (project.is_file() and project.stat().st_size>4096 and is_png(image)):
        raise RuntimeError('CC5 build lacks saved ccProject and/or PNG')
    return True,'Headshot and actor project verified'

def review_picture(job,image,stage,folder):
    if not is_image(image):
        return False,'No review image'
    p=folder/(job+'_'+stage+'_review.jpg')
    with Image.open(image) as im:
        img=im.convert('RGB')
        img.thumbnail((1050,1300))
        img.save(p,'JPEG',quality=75,optimize=True)
    if p.stat().st_size>850000:
        with Image.open(image) as im:
            img=im.convert('RGB')
            img.thumbnail((790,1000))
            img.save(p,'JPEG',quality=62,optimize=True)
    if p.stat().st_size>880000:
        return False,'Review JPEG still too large'
    return ntfy_send(STORY_FILE,job,stage,p,folder)

def resume_existing_build(job,c,folder):
    d=Path(kit.JOBS)/job
    output=Path(DATA['out_dir'])/c.get('folder','')/(c['name']+'.iAvatar')
    report={'job':job,'updated':now(),'face_source':str(d/'face.png'),
      'chat_preserved':(d/'face_chat_context.json').is_file()}
    print('CC5_CONSUME',job,now(),flush=True)
    ok,note=validated_build(job,c)
    report.update(headshot_build=note,project=str(d/(c['name']+'.ccProject')))
    report['original_render']=str(d/(c['name']+'.png'))
    sent,msg=review_picture(job,d/(c['name']+'.png'),'body',folder)
    report['body_ntfy']={'ok':sent,'result':msg}
    print('BODY_NTFY',job,sent,msg,flush=True)
    if not sent:raise RuntimeError('body review ntfy failed: '+msg)
    # Open saved job, render four angles while retaining project.
    opened=bridge('cc5/open_job.py',job=job)
    if not re.search(r'avatars=[1-9]\d*',opened):
        raise RuntimeError('Open project returned no avatar: '+opened[-220:])
    views=bridge('cc5/render_views.py',job=job)
    for view in ('front','left','back','right'):
        if not is_png(d/('view_'+view+'.png')):
            raise RuntimeError('Missing '+view+' QA view')
    from tools.cc5_production_flow import make_sheet
    sheet=make_sheet(job,d,folder)
    if not sheet:raise RuntimeError('Cannot assemble four-view QA contact sheet')
    sent,msg=ntfy_send(STORY_FILE,job,'four_views',sheet,folder)
    report['four_view_ntfy']={'ok':sent,'result':msg,'file':str(sheet)}
    print('FOUR_VIEW_NTFY',job,sent,msg,flush=True)
    if not sent:raise RuntimeError('QA review ntfy failed: '+msg)
    # Do not overwrite/move an existing real output or create hidden backups.
    if output.is_file() and output.stat().st_size>4096:
        report['export_note']='pre-existing file: no overwrite'
    else:
        if output.exists():
            raise RuntimeError('Incomplete export destination exists; refusing to overwrite')
        saved=bridge('cc5/probes/save_as.py',path=str(output))
        if 'saved error=False' not in saved:
            raise RuntimeError('Scripted iAvatar save failed: '+saved[-300:])
        report['export_note']='scripted iAvatar save'
    if not output.is_file() or output.stat().st_size<4096:
        raise RuntimeError('iAvatar missing or too small')
    report['export']=str(output)
    report['export_bytes']=output.stat().st_size
    reopen=bridge('cc5/probes/open_iavatar.py',path=str(output))
    if not re.search(r'avatars=[1-9]\d*',reopen):
        raise RuntimeError('Reopen verification failed: '+reopen[-250:])
    report['reopen_verified']=True
    report['status']='TECHNICAL_EXPORT_REOPENED_REVIEW_REQUIRED'
    report['visual_qa']='REVIEW_REQUIRED'
    report['updated']=now()
    return report

def do_selftest():
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as t:
        folder=Path(t)
        assert not is_png(folder/'missing.png')
        assert not (folder/'fake.iAvatar').exists()
    print('BUILD_CONSUMER_SELFTEST_PASS no files touched')
    return 0

def main():
    global STORY,STORY_FILE,DATA
    ap=argparse.ArgumentParser()
    ap.add_argument('--story')
    ap.add_argument('--selftest',action='store_true')
    a=ap.parse_args()
    if a.selftest:return do_selftest()
    if os.environ.get('COMPUTERNAME','').upper()!='DESKTOP-F1PJT4S':
        raise RuntimeError('Wrong Windows host')
    STORY=a.story
    STORY_FILE=ROOT/'stories'/(STORY+'.json')
    DATA=json.loads(STORY_FILE.read_text(encoding='utf-8-sig'))
    if not isinstance(DATA.get('characters'),dict):
        raise RuntimeError('Invalid story data')
    folder=ROOT/'runs'/STORY
    folder.mkdir(parents=True,exist_ok=True)
    statusfile=folder/'cc5_build_queue_progress.json'
    status=json.loads(statusfile.read_text(encoding='utf-8-sig')) if statusfile.exists() else {'story':STORY,'jobs':{}}
    records=status.setdefault('jobs',{})
    # One writer for every CC5 project at a time.
    import msvcrt
    lockpath=ROOT/'runs'/'.cc5_global_production_flow.lock'
    with lockpath.open('a+b') as lock:
        lock.seek(0)
        lock.write(b'0')
        lock.flush()
        lock.seek(0)
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:
            print('CC5_LANE_BLOCKED another production workflow owns CC5',flush=True)
            return 2
        print('CC5_CONSUMER_START',STORY,now(),flush=True)
        while True:
            jobs=list(DATA['characters'].items())
            candidates=[(j,c) for j,c in jobs
               if is_png(Path(kit.JOBS)/j/'face.png')
               and records.get(j,{}).get('status') not in
                   ('TECHNICAL_EXPORT_REOPENED_REVIEW_REQUIRED','BLOCKED')]
            ready_count=len(candidates)
            if not candidates:
                if len(records)==len(jobs) and all(records.get(j,{}).get('status') in
                      ('TECHNICAL_EXPORT_REOPENED_REVIEW_REQUIRED','BLOCKED') for j,c in jobs):
                    blocked=[j for j,c in jobs if records.get(j,{}).get('status')=='BLOCKED']
                    status['state']='partially_blocked' if blocked else 'all_processed_review_required'
                    status['updated']=now()
                    status['blocked_jobs']=blocked
                    save_json(statusfile,status)
                    if blocked:
                        print('CC5_QUEUE_PARTIAL_BLOCKERS',','.join(blocked),flush=True)
                        return 2
                    print('CC5_QUEUE_DONE_PENDING_VISUAL_REVIEW',flush=True)
                    return 0
                print('WAIT_FOR_NEXT_FACE',now(),len(records),'/',len(jobs),flush=True)
                time.sleep(20)
                continue
            idle,reason=process_check()
            if not idle:
                print('CC5_LANE_WAIT',now(),reason[:180],flush=True)
                time.sleep(20)
                continue
            job,c=candidates[0]
            records[job]={'status':'in_progress','started':now()}
            save_json(statusfile,status)
            try:
                report=resume_existing_build(job,c,folder)
                records[job]=report
                print('ACTOR_DELIVERED',job,report['export_bytes'],
                      'QA',report['visual_qa'],now(),flush=True)
            except Exception:
                records[job]={'status':'BLOCKED','error':traceback.format_exc()[-1300:],
                             'updated':now()}
                print('ACTOR_BLOCKED',job,records[job]['error'],flush=True)
                # When the bridge is hung, do not start another character.
                idle,reason=process_check()
                if not idle:
                    status['state']='paused_cc5_unavailable'
                    save_json(statusfile,status)
                    return 2
            status['updated']=now()
            save_json(statusfile,status)

if __name__=='__main__':
    try:sys.exit(main())
    except Exception:
        print('CONSUMER_FATAL',traceback.format_exc()[-1500:],flush=True)
        sys.exit(2)
