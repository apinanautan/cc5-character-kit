"""Character face producer: independent conversations, delayed retries, no head-of-line blocking.
No history deletion, no CC5 control. Output appears as face.png, immediately ntfy acknowledged.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import kit
from tools.cc5_production_flow import is_png,ntfy_send,save_json

def clock():return time.strftime('%Y-%m-%d %H:%M:%S')
def epoch():return time.time()
def pending(jobs,states,files,when):
    """Return runnable jobs; a blocked job never delays an independent later job."""
    todo=[]
    for job,c in jobs.items():
        if not isinstance(c.get('face'),dict):continue
        if is_png(files(job)):
            continue
        st=states.get(job,{})
        if st.get('status')=='blocked_retry_limit':continue
        if float(st.get('next_retry_epoch',0))>when:continue
        parent=c.get('face',{}).get('ref')
        if parent and not is_png(files(parent)):continue
        todo.append(job)
    return todo

def send_face(file,folder,job,face,states):
    if not is_png(face):return False
    if states.get(job,{}).get('status')=='face_ready':
        receipt=folder/'flow_ntfy_receipts.json'
        acknowledged=states.get(job,{}).get('ntfy','')
        if receipt.is_file() and acknowledged.startswith(('ntfy id ','already sent')):
            return True
    preview=folder/(job+'_face_review.jpg')
    with Image.open(face) as im:
        im.convert('RGB').save(preview,'JPEG',quality=76,optimize=True)
    if preview.stat().st_size>800000:
        with Image.open(face) as im:
            im.thumbnail((820,1100))
            im.convert('RGB').save(preview,'JPEG',quality=65,optimize=True)
    if preview.stat().st_size>900000:raise RuntimeError('review JPEG too large')
    ok,msg=ntfy_send(file,job,'face',preview,folder)
    states[job]={'status':'face_ready' if ok else 'face_ready_ntfy_retry',
                 'ntfy':msg,'source_face':str(face),'preview':str(preview),
                 'chat_preserved':(face.parent/'face_chat_context.json').exists(),
                 'updated':clock()}
    print('FACE_READY',job,'NTFY',ok,msg,'FILE_BYTES',face.stat().st_size,flush=True)
    return ok

def choose_backoff(output,attempt):
    low=output.lower()
    if '429' in low or 'rate_limit' in low or 'rate limit' in low:
        return 660,'rate_limit'
    if '10054' in low or 'connection reset' in low or 'connection was forcibly closed' in low:
        return min(30*attempt,150),'connection_reset'
    if 'timed out' in low or 'timeout' in low:
        return min(60*attempt,240),'timeout'
    return min(60*attempt,180),'other_error'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--story',required=True)
    ap.add_argument('--max-attempts',type=int,default=8)
    ap.add_argument('--selftest',action='store_true')
    args=ap.parse_args()
    if args.selftest:
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as t:
            a=Path(t)
            jobs={'a':{'face':{}},'b':{'face':{}},'dependent':{'face':{'ref':'a'}}}
            st={'a':{'next_retry_epoch':200}}
            assert pending(jobs,st,lambda j:a/j,100)==['b']
            assert pending(jobs,st,lambda j:a/j,300)==['a','b']
            assert choose_backoff('WinError 10054',1)[1]=='connection_reset'
            assert choose_backoff('HTTP 429',1)[0]==660
        print('SELFTEST_PASS no head-of-line blocking / dependencies / rate-limit timing')
        return 0
    if os.environ.get('COMPUTERNAME','').upper()!='DESKTOP-F1PJT4S':
        raise RuntimeError('wrong host')
    file=ROOT/'stories'/(args.story+'.json')
    story=json.loads(file.read_text(encoding='utf-8-sig'))
    if not isinstance(story.get('characters'),dict):raise RuntimeError('invalid story')
    jobs=story['characters']
    folder=ROOT/'runs'/args.story
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/'face_queue_progress.json'
    current=json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}
    states=current.setdefault('characters',{})
    current['story']=args.story
    current['state']='running'
    def face(job):return Path(kit.JOBS)/job/'face.png'
    print('FACE_QUEUE_V2_START',clock(),'CHARACTERS',len(jobs),flush=True)
    try:
        while True:
            complete=[j for j,c in jobs.items() if isinstance(c.get('face'),dict) and is_png(face(j))]
            # Send actual produced images before starting new requests.
            for job in complete:
                if states.get(job,{}).get('status')!='face_ready':
                    if not send_face(file,folder,job,face(job),states):
                        states[job]['next_retry_epoch']=epoch()+90
                    current['updated']=clock()
                    save_json(path,current)
            required=[j for j,c in jobs.items() if isinstance(c.get('face'),dict)]
            if len(complete)==len(required) and all(states.get(j,{}).get('status')=='face_ready' for j in required):
                current['state']='all_faces_ready'
                current['updated']=clock()
                save_json(path,current)
                print('ALL_FACES_READY',clock(),flush=True)
                return 0
            runnable=pending(jobs,states,face,epoch())
            if not runnable:
                statuses=[states.get(j,{}) for j in required if not is_png(face(j))]
                if statuses and all(s.get('status')=='blocked_retry_limit' for s in statuses):
                    current['state']='blocked_retry_limit'
                    save_json(path,current)
                    print('BLOCKED_ALL_PENDING_FACES',flush=True)
                    return 2
                waiting=[float(s.get('next_retry_epoch',0)) for s in statuses
                         if float(s.get('next_retry_epoch',0))>epoch()]
                sleep_for=max(5,min(30,(min(waiting)-epoch()) if waiting else 15))
                print('QUEUE_WAIT',round(sleep_for,1),'PENDING',len(required)-len(complete),flush=True)
                time.sleep(sleep_for)
                continue
            job=runnable[0]
            attempts=int(states.get(job,{}).get('attempts',0))+1
            print('FACE_START',job,'TRY',attempts,clock(),flush=True)
            output=''
            try:
                p=subprocess.run([sys.executable,'-u',str(ROOT/'tools'/'gen_faces.py'),args.story,job],
                      cwd=ROOT,capture_output=True,text=True,encoding='utf8',
                      errors='replace',timeout=1100)
                output=p.stdout+'\n'+p.stderr
                code=p.returncode
            except subprocess.TimeoutExpired:
                output='Timeout waiting face image'
                code=2
            if is_png(face(job)):
                states[job]={'status':'generated','attempts':attempts,'updated':clock()}
                print('FACE_GENERATED',job,'BYTES',face(job).stat().st_size,flush=True)
            else:
                seconds,kind=choose_backoff(output,attempts)
                if attempts>=args.max_attempts:
                    states[job]={'status':'blocked_retry_limit','attempts':attempts,
                        'last_error':output[-750:],'error_type':kind,'updated':clock()}
                    print('FACE_BLOCKED',job,'AFTER_ATTEMPTS',attempts,flush=True)
                else:
                    states[job]={'status':'waiting_retry','attempts':attempts,
                        'next_retry_epoch':epoch()+seconds,
                        'last_error':output[-750:],'error_type':kind,'updated':clock()}
                    print('FACE_DEFER',job,'REASON',kind,'SECONDS',seconds,
                          'NEXT_INDEPENDENT_JOB_CAN_START',flush=True)
            current['updated']=clock()
            save_json(path,current)
    except Exception:
        current['state']='error'
        current['error']=traceback.format_exc()[-1500:]
        save_json(path,current)
        print('QUEUE_ERROR',current['error'],flush=True)
        return 2

if __name__=='__main__':
    sys.exit(main())