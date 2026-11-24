"""CC5 code-driven full production flow. One command, resumable and fail-closed.

Stages: SCHEMA -> LIBRARY -> TIDMUNZ_FACE -> HEADSHOT_AND_CLOTH ->
        FOUR_VIEWS -> IAVATAR_EXPORT -> REOPEN -> NTFY -> QA_REVIEW.

Actual face/CC5 work is delegated to the existing studio.runner.Runner.
Missing input/face/output/image/network is a blocker, never a fake PASS.
No implicit restart of an unsaved CC5 session; execution requires an explicit
safe-session approval flag because the legacy Runner may restart CC5.

Examples:
 python tools/cc5_production_flow.py --story STORY --status
 python tools/cc5_production_flow.py --story STORY --execute --approve-cc5-session-control
 python tools/cc5_production_flow.py --story STORY --deliver-only
 python tools/cc5_production_flow.py --selftest
"""
import argparse
import hashlib
import io
import json
import mimetypes
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error

ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT),str(ROOT/'studio')]
import kit
from tools.cc5_production_preflight import inspect_story,inspect_runtime

TOPIC='https://ntfy.sh/Pic-Gptz'
HOST='DESKTOP-F1PJT4S'
PY=sys.executable
CREATE_NO_WINDOW=getattr(subprocess,'CREATE_NO_WINDOW',0)
VIEWS=('front','left','back','right')

def now():
    return time.strftime('%Y-%m-%d %H:%M:%S')

def save_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.writing')
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    os.replace(tmp,path)

def load_json(path,default=None):
    if not path.is_file():
        return {} if default is None else default
    return json.loads(path.read_text(encoding='utf-8-sig'))

def story_path(name):
    p=Path(name)
    if not p.is_file():
        p=ROOT/'stories'/(name if name.lower().endswith('.json') else name+'.json')
    if not p.is_file():
        raise ValueError('Story JSON not found: '+str(name))
    return p.resolve()

def location(story_file,story):
    slug=story_file.stem
    return ROOT/'runs'/slug

def is_png(path):
    try:
        with Path(path).open('rb') as f:
            b=f.read(24)
        return b[:8]==bytes((137,80,78,71,13,10,26,10)) and int.from_bytes(b[16:20],'big')>=64 and int.from_bytes(b[20:24],'big')>=64
    except OSError:
        return False

def is_image(path):
    p=Path(path)
    if not p.is_file() or p.stat().st_size<1000:
        return False
    if p.suffix.lower()=='.png':
        return is_png(p)
    if p.suffix.lower() in ('.jpg','.jpeg'):
        with p.open('rb') as f:return f.read(3)==bytes((255,216,255))
    return False

def get_jobs(story,only):
    jobs=list(story['characters'])
    if not only:return jobs
    unknown=set(only)-set(jobs)
    if unknown:raise ValueError('Unknown job IDs: '+','.join(sorted(unknown)))
    return [j for j in jobs if j in only]

def export_file(story,job):
    c=story['characters'][job]
    return Path(story['out_dir'])/c.get('folder','')/(c['name']+'.iAvatar')

def work_files(story,job):
    c=story['characters'][job]
    folder=Path(kit.JOBS)/job
    return {'folder':folder,'face':folder/'face.png','body':folder/(c['name']+'.png'),
            'project':folder/(c['name']+'.ccProject'),
            'export':export_file(story,job)}

def resolve_sources(story,jobs):
    """Before starting UI: verify actual wardrobe paths, not just IDs."""
    issues=[]
    wardrobe_path=Path(kit.data_file('wardrobe_verified.json'))
    wardrobe={}
    if wardrobe_path.is_file():
        wardrobe={x['id']:x['path'] for x in load_json(wardrobe_path,{'items':[]}).get('items',[]) if 'id' in x and 'path' in x}
    hair_pool_path=Path(kit.data_file('cc5_hair_pool.json'))
    hairs=load_json(hair_pool_path,{'hairs':[]}).get('hairs',[])
    used={}
    shared_clothes = {
        os.path.normcase(os.path.normpath(path)).casefold()
        for path in story.get("approved_shared_clothes", [])
        if isinstance(path, str) and Path(path).suffix.lower() in (".cccloth", ".ccshoes")
    }
    for job in jobs:
        c=story['characters'][job]
        if c.get('head_from') and c['head_from'] not in story['characters']:
            issues.append(job+': missing source head actor')
        for i,item in enumerate(c.get('outfit',[])):
            try:
                source=kit.resolve_item(item[0],wardrobe)
                if not Path(source).is_file():
                    issues.append(job+': outfit '+str(i)+' missing at '+source)
                canonical=os.path.normcase(os.path.normpath(source)).casefold()
                existing=used.get(canonical)
                if existing and existing!=job and canonical not in shared_clothes:
                    issues.append(job+': reused exact outfit source also used by '+existing+' (review identity/role)')
                used.setdefault(canonical,job)
            except (OSError,KeyError,ValueError,TypeError) as exc:
                issues.append(job+': cannot resolve outfit '+str(i)+': '+str(exc)[:140])
        hair=c.get('hair')
        if hair:
            if os.path.isabs(hair):
                options=[hair]
            else:
                options=[h.get('path','') for h in hairs if hair.lower() in h.get('path','').lower()]
            if not options or not Path(options[0]).is_file():
                issues.append(job+': hair not found in library: '+str(hair))
        if not c.get('head_from') and c.get('age_group')!='baby' and not hair:
            issues.append(job+': hair unspecified; auto-select tool may choose unreviewed or duplicate hairstyle')
    return issues

def inspect_existing_checkpoints(story,jobs):
    problems=[]
    for job in jobs:
        files=work_files(story,job)
        st=story.get('status',{}).get(job,{})
        if not isinstance(st,dict):
            problems.append(job+': status entry is not a dictionary')
            continue
        if str(st.get('face','')).startswith('ok') and not story['characters'][job].get('head_from') and not is_png(files['face']):
            problems.append(job+': marked face OK but face.png missing/invalid')
        if str(st.get('build','')).startswith('ok') and (not files['project'].is_file() or not is_png(files['body'])):
            problems.append(job+': marked build OK but ccProject or body render missing')
        if str(st.get('export','')).startswith('ok') and (not files['export'].is_file() or files['export'].stat().st_size<=1024):
            problems.append(job+': marked export OK but iAvatar missing/empty')
        if files['export'].is_file() and not str(st.get('export','')).startswith(('ok','skip')):
            problems.append(job+': output iAvatar exists without verified flow status; refuse silent overwrite')
    return problems

def inspect(story_file,story,jobs,runtime=False):
    errors,warnings=inspect_story(story)
    if runtime:
        a,b,checks=inspect_runtime()
        errors+=a;warnings+=b
    else:checks={}
    if not errors:
        from tools.cc5_culture_gate import inspect_culture
        era_errors,era_warnings,classifications=inspect_culture(story,jobs)
        errors.extend(era_errors)
        warnings.extend(era_warnings)
        checks['cultural_role_classifications']=classifications
    if not errors:
        errors+=resolve_sources(story,jobs)
        errors+=inspect_existing_checkpoints(story,jobs)
    return errors,warnings,checks

def ntfy_send(story_file,job,kind,path,directory):
    """Dedup by image SHA; record server-acknowledged real attachments."""
    path=Path(path)
    # A garment trial is not a user review until the actual fitted images pass QA.
    if kind in ("garment_trial","garment_preview"):
        try:
            from ai_cc5_cloth3d import require_visual_gate
            garment=load_json(directory/"cloth3d_progress.json",{})
            if garment.get("story","")+"_"+garment.get("actor","")!=job or garment.get("stage")!="complete":
                return False,"Garment visual QA has not passed"
            report=require_visual_gate(garment,garment.get("evidence"),"fitted")
            if report.get("review_sha256")!=hashlib.sha256(path.read_bytes()).hexdigest():
                return False,"Garment review image does not match approved QA"
        except (OSError,ValueError,KeyError,TypeError) as exc:
            return False,"Garment visual QA blocked: "+str(exc)
    if not is_image(path):
        return False,'No valid image: '+str(path)
    receipts_file=directory/'flow_ntfy_receipts.json'
    receipts=load_json(receipts_file,{'topic':TOPIC,'sent':{}})
    receipts.setdefault('sent',{})
    content=path.read_bytes()
    digest=hashlib.sha256(content).hexdigest()
    key=job+'/'+kind+'/'+digest
    if key in receipts['sent']:
        return True,'already sent (dedup)'
    # Recognize prior one-off deliveries to avoid re-sending the identical preview.
    legacy=load_json(directory/'ntfy_character_delivery.json',{})
    if kind=='body' and job in legacy.get('deliveries',{}):
        existing=legacy['deliveries'][job]
        if Path(existing.get('preview_path',''))==path and existing.get('ntfy_id'):
            receipts['sent'][key]={'id':existing['ntfy_id'],'legacy':True,'at':now()}
            save_json(receipts_file,receipts)
            return True,'already sent by prior delivery'
    label=story_file.stem+' '+job+' '+kind
    headers={'Title':'CC5 '+label,'Message':'Review actual generated character image: '+label,
        'Filename':job+'_'+kind+path.suffix.lower(),
        'Content-Type':'image/png' if path.suffix.lower()=='.png' else 'image/jpeg',
        'Priority':'3','Tags':'art'}
    req=urllib.request.Request(TOPIC,data=content,headers=headers,method='POST')
    try:
        with urllib.request.urlopen(req,timeout=30) as resp:
            if resp.status<200 or resp.status>=300:
                return False,'ntfy HTTP '+str(resp.status)
            ack=json.loads(resp.read().decode('utf-8'))
        if ack.get('topic')!='Pic-Gptz' or not ack.get('id') or not ack.get('attachment'):
            return False,'ntfy did not acknowledge an actual image attachment'
        receipts['sent'][key]={'id':ack['id'],'at':now(),'file':str(path),
             'bytes':len(content),'hash':digest,'topic':'Pic-Gptz'}
        save_json(receipts_file,receipts)
        return True,'ntfy id '+ack['id']
    except (OSError,ValueError,TimeoutError,urllib.error.URLError) as exc:
        return False,type(exc).__name__+': '+str(exc)[:160]

def make_sheet(job,folder,directory):
    files=[folder/('view_'+x+'.png') for x in VIEWS]
    if not all(is_png(f) for f in files):
        return None
    try:
        from PIL import Image,ImageDraw
        tile=(400,430)
        canvas=Image.new('RGB',(tile[0]*2,tile[1]*2),'#17202b')
        drawer=ImageDraw.Draw(canvas)
        for i,(view,path) in enumerate(zip(VIEWS,files)):
            with Image.open(path) as incoming:
                im=incoming.convert('RGB')
                im.thumbnail((tile[0]-12,tile[1]-38))
                x=(i%2)*tile[0]+(tile[0]-im.width)//2
                y=(i//2)*tile[1]+25
                canvas.paste(im,(x,y))
            drawer.text(((i%2)*tile[0]+15,(i//2)*tile[1]+7),job+' '+view,fill='white')
        out=directory/(job+'_four_views.jpg')
        out.parent.mkdir(parents=True,exist_ok=True)
        canvas.save(out,format='JPEG',quality=85,optimize=True)
        return out if is_image(out) else None
    except (OSError,ImportError,ValueError):
        return None

def bridge_exec(args,timeout):
    result=subprocess.run([PY,str(ROOT/'tools'/'cc5.py'),'run',*args],
             cwd=ROOT,capture_output=True,text=True,encoding='utf-8',
             errors='replace',timeout=timeout,creationflags=CREATE_NO_WINDOW)
    return result.returncode,(result.stdout+result.stderr)[-1400:]

def qa_job(story_file,story,job,directory,reopen=True):
    f=work_files(story,job)
    progress=story.get('status',{}).get(job,{})
    problems=[];evidence={}
    for k in ('face','body','project','export'):
        p=f[k]
        if k in ('face','body'):
            ok=is_png(p)
        else:
            ok=p.is_file() and p.stat().st_size>1024
        evidence[k]={'exists':ok,'path':str(p)}
        if not ok and (k!='face' or not story['characters'][job].get('head_from')):
            problems.append(k+' missing or invalid')
    render_errors=[]
    if not problems and reopen:
        try:
            code,out=bridge_exec([str(ROOT/'cc5'/'open_job.py'),'job='+job],600)
            if code or 'avatars=1' not in out:
                render_errors.append('open_job: '+out[-240:])
            else:
                code,out=bridge_exec([str(ROOT/'cc5'/'render_views.py'),'job='+job],620)
                if code:
                    render_errors.append('four_views: '+out[-240:])
        except (OSError,subprocess.TimeoutExpired) as exc:
            render_errors.append('render_views: '+type(exc).__name__)
    views={view:is_png(f['folder']/('view_'+view+'.png')) for view in VIEWS}
    evidence['views']=views
    if not all(views.values()):
        problems.append('Missing multi-angle visual evidence')
    problems+=render_errors
    # A real iAvatar reopen check is separate from opening the ccProject.
    evidence['avatar_reopened_in_cc5']=False
    if not problems and reopen:
        try:
            code,out=bridge_exec([str(ROOT/'cc5'/'probes'/'open_iavatar.py'),'path='+str(f['export'])],600)
            evidence['avatar_reopened_in_cc5']=code==0 and 'avatars=1' in out
            if not evidence['avatar_reopened_in_cc5']:
                problems.append('iAvatar reopen verification failed: '+out[-170:])
        except (OSError,subprocess.TimeoutExpired) as exc:
            problems.append('iAvatar reopen verification error: '+type(exc).__name__)
    if not evidence['avatar_reopened_in_cc5']:
        problems.append('No verified iAvatar reopen evidence')
    sheet=make_sheet(job,f['folder'],directory)
    if sheet:
        evidence['review_sheet']=str(sheet)
    # Subjective Thai face, period, material, clipping, visual color and family resemblance
    # cannot be marked PASS by checking file existence alone.
    status='MISSING' if not evidence['export']['exists'] else 'REVIEW'
    return {'job':job,'status':status,'technical_export':evidence['export']['exists'],
      'visual_qa':'REVIEW_REQUIRED','checks':evidence,'issues':problems,
      'stage_status':progress,'updated_at':now()}

def write_inventory(story,directory):
    """Persist paths and exact metadata, but NEVER duplicate original 3D source files."""
    from collections import defaultdict
    wardrobe_path=Path(kit.data_file('wardrobe_verified.json'))
    ward={}
    if wardrobe_path.is_file():
        ward={x['id']:x['path'] for x in load_json(wardrobe_path,{'items':[]}).get('items',[]) if 'id' in x and 'path' in x}
    entries={}
    hairpool=load_json(Path(kit.data_file('cc5_hair_pool.json')),{'hairs':[]}).get('hairs',[])
    for job,c in story['characters'].items():
        items=[]
        if c.get('hair'):
            hair=c['hair']
            hits=[hair] if os.path.isabs(hair) else [h.get('path','') for h in hairpool if hair.lower() in h.get('path','').lower()]
            items.append({'slot':'hair','source':hits[0] if hits else hair,
                'color_rgb_requested':c.get('hair_rgb'), 'visually_verified_color':False})
        for index,outfit in enumerate(c.get('outfit',[])):
            try:p=kit.resolve_item(outfit[0],ward)
            except (KeyError,ValueError,OSError):p=outfit[0]
            items.append({'slot':'outfit_'+str(index),'source':p,'fabric_id':outfit[1],
                'visually_verified_color':False})
        entries[job]={'name':c['name'],'era':story.get('era',''),
            'requested_style':c.get('style',''),'assets':items,
            'note':'Catalog source paths only; render colors/cut/fit must be verified'}
    from tools.cc5_culture_gate import inspect_culture
    _,_,classification=inspect_culture(story,list(story['characters']))
    for job,entry in entries.items():
        entry['style_classification']=classification.get(job,{})
    save_json(directory/'flow_asset_registry.json',{'story':story['title'],
        'updated_at':now(),'characters':entries})

def run_story(args,source,story,dirpath,jobs,observer=None,stop_requested=None):
    errors,warnings,_=inspect(source,story,jobs,runtime=True)
    if errors:
        for e in errors:print('BLOCKED',e,flush=True)
        return 2
    if os.environ.get('COMPUTERNAME','').upper()!=HOST:
        print('BLOCKED: unexpected host; refusing to control CC5',flush=True)
        return 2
    if not args.approve_cc5_session_control:
        print('BLOCKED: existing Runner can restart CC5; use --approve-cc5-session-control only after saving all interactive CC5 work',flush=True)
        return 2
    # Single process lock via Windows CRT. Protects against two workflows.
    lockfile=ROOT/'runs'/'.cc5_global_production_flow.lock'
    lockfile.parent.mkdir(parents=True,exist_ok=True)
    lock=lockfile.open('a+b')
    try:
        import msvcrt
        lock.seek(0)
        lock.write(b'0')
        lock.flush()
        lock.seek(0)
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:
            print('BLOCKED: another production flow holds the lock')
            return 2
    except ImportError:
        print('BLOCKED: Windows lock unavailable')
        return 2
    try:
        from studio.runner import Runner,load
        write_inventory(story,dirpath)
        report_file=dirpath/'flow_report.json'
        report=load_json(report_file,{'story':story['title'],'jobs':{},'events':[]})
        print('FLOW_START',story['title'],'jobs',len(jobs),flush=True)
        for job in jobs:
            if stop_requested and stop_requested():
                print('FLOW_STOP_REQUESTED_BEFORE',job,flush=True)
                break
            print('CHARACTER_START',job,flush=True)
            if observer:observer('log','Production Flow started character '+job)
            issues=[]
            active_runner=[None]
            def callback(event,value):
                if active_runner[0] and stop_requested and stop_requested():
                    active_runner[0].stop=True
                if observer:
                    try:observer(event,value)
                    except Exception as exc:
                        print('OBSERVER_ERROR',type(exc).__name__,str(exc)[:100],flush=True)
                if event=='log':
                    print('RUNNER',str(value)[:320],flush=True)
                elif event=='status':
                    print('STAGE',str(value)[:300],flush=True)
                elif event=='image':
                    p=Path(value)
                    role='face' if p.name=='face.png' else 'body'
                    ok,msg=ntfy_send(source,job,role,p,dirpath)
                    print('NTFY',job,role,ok,msg,flush=True)
                    if not ok:issues.append('ntfy '+role+': '+msg)
            try:
                active_runner[0]=Runner(str(source),{'only':{job},'export':True,'weights':args.weights},callback)
                active_runner[0].run()
            except Exception as exc:
                issues.append('Runner raised '+type(exc).__name__+': '+str(exc)[:220])
            updated=load(source)
            f=work_files(updated,job)
            # Existing image on disk may have been skipped by Runner as already complete.
            if is_png(f['face']):
                ok,msg=ntfy_send(source,job,'face',f['face'],dirpath)
                if not ok:issues.append('ntfy face: '+msg)
            q=qa_job(source,updated,job,dirpath,reopen=True)
            if q['checks'].get('review_sheet'):
                ok,msg=ntfy_send(source,job,'four_views',q['checks']['review_sheet'],dirpath)
                if not ok:issues.append('ntfy four_views: '+msg)
            elif is_png(f['body']):
                ok,msg=ntfy_send(source,job,'body',f['body'],dirpath)
                if not ok:issues.append('ntfy body: '+msg)
            q['issues']+=issues
            report['jobs'][job]=q
            report['updated_at']=now()
            save_json(report_file,report)
            if observer:
                observer('log','Production Flow '+job+' -> '+q['status']+'; visual QA required')
            print('CHARACTER_FINISHED',job,q['status'],'TECHNICAL_EXPORT',q['technical_export'],
                'ISSUES',len(q['issues']),flush=True)
        print('FLOW_END',report_file,flush=True)
        return 0 if all(report['jobs'][j]['technical_export'] for j in jobs) else 2
    finally:
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
        except Exception:pass
        lock.close()

def selftest():
    # No network, no CC5, no real story files changed.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='cc5_flow_selftest_') as temp:
        d=Path(temp)
        p=d/'face.png'
        p.write_bytes(bytes((137,80,78,71,13,10,26,10))+b'\x00\x00\x00\x0dIHDR'+(256).to_bytes(4,'big')+(256).to_bytes(4,'big')+b'\x00'*14)
        assert is_png(p)
        assert not is_png(d/'missing.png')
        assert not is_image(d/'missing.png')
        doc={'title':'TEST','out_dir':str(d),'characters':{'a':{'name':'AAA','sex':'female','age':25,'age_group':'adult','outfit':[['LIB:example',None]],
               'face':{'อายุ':'25','เพศ':'หญิง','บทบาท':'ชาวบ้าน','สีผิว':'สองสี','ใบหน้า':'รูปไข่'}}},'status':{'a':{}}}
        bad=dict(doc,characters=[],status='planning_only',out_dir=None)
        assert len(inspect_story(bad)[0])>=3
        assert inspect_story(doc)[0]==[]
        save_json(d/'test.json',{'status':'ok'})
        assert load_json(d/'test.json')['status']=='ok'
        assert get_jobs(doc,['a'])==['a']
        try:get_jobs(doc,['bad'])
        except ValueError:pass
        else:raise AssertionError('Unknown job not blocked')
        print('SELFTEST_PASS workflow CLI, image checks, schema, atomic report, selection, no network/CC5')
    return 0

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--story',help='Story slug or JSON path; no fixed story name')
    ap.add_argument('--execute',action='store_true',help='Run existing Tidmunz/CC5 pipeline and QA')
    ap.add_argument('--approve-cc5-session-control',action='store_true',help='I saved all CC5 work and permit legacy Runner restarts')
    ap.add_argument('--deliver-only',action='store_true',help='Retry missing preview image deliveries without CC5')
    ap.add_argument('--selftest',action='store_true')
    ap.add_argument('--jobs',nargs='*',help='Only these character job IDs')
    ap.add_argument('--weights',action='store_true')
    args=ap.parse_args()
    if args.selftest:
        return selftest()
    if not args.story:
        ap.error('--story required unless --selftest')
    source=story_path(args.story)
    story=load_json(source)
    dirpath=location(source,story)
    errors,warnings,_=inspect(source,story,list(story.get('characters',{})) if isinstance(story.get('characters'),dict) else [],runtime=False)
    if args.deliver_only:
        report=load_json(dirpath/'flow_report.json',{'jobs':{}})
        delivered=0;failed=0
        for job in report.get('jobs',{}):
            files=work_files(story,job)
            for kind,p in (('face',files['face']),('four_views',dirpath/(job+'_four_views.jpg')),('body',files['body'])):
                if is_image(p):
                    ok,msg=ntfy_send(source,job,kind,p,dirpath)
                    print('DELIVERY',job,kind,ok,msg)
                    delivered+=int(ok);failed+=int(not ok)
        return 2 if failed else 0
    if args.execute:
        if errors:
            for e in errors:print('BLOCKED',e)
            return 2
        return run_story(args,source,story,dirpath,get_jobs(story,args.jobs))
    print('FLOW_PREFLIGHT','BLOCKED' if errors else 'READY_FOR_NEXT_GATE')
    for e in errors:print('ERROR',e)
    for w in warnings:print('WARNING',w)
    if not errors:
        for job in get_jobs(story,args.jobs):
            f=work_files(story,job)
            print('JOB',job,'FACE',is_png(f['face']),'RENDER',is_png(f['body']),
                  'EXPORT',f['export'].is_file())
    print('RUN_COMMAND',f'python tools/cc5_production_flow.py --story {source.stem} --execute --approve-cc5-session-control')
    return 2 if errors else 0

if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,KeyError,TypeError) as exc:
        print('BLOCKED',type(exc).__name__+': '+str(exc)[:350],file=sys.stderr)
        sys.exit(2)
