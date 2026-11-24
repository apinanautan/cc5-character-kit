"""Export-only recovery for an existing CC5 actor project after Save dialog failure.

No image re-generation, no Headshot re-build, no source asset duplication,
no backup and no overwriting prior iAvatar files.
Run after any other CC5 consumer has exited:
  python tools/cc5_export_recovery.py --story SLUG --job ID --execute
Default without --execute only prints readiness and does not touch CC5.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT),str(ROOT/'studio')]
import kit
from tools.cc5_build_queue import bridge,process_check
from tools.cc5_production_flow import is_png,save_json

def load_context(story_slug,job):
    if os.environ.get('COMPUTERNAME','').upper()!='DESKTOP-F1PJT4S':
        raise RuntimeError('Unexpected machine; remote CC5 control blocked')
    source=ROOT/'stories'/(story_slug+'.json')
    if not source.is_file():raise ValueError('Unknown story '+story_slug)
    story=json.loads(source.read_text(encoding='utf-8-sig'))
    if job not in story.get('characters',{}):
        raise ValueError('Job ID not present: '+job)
    c=story['characters'][job]
    folder=Path(kit.JOBS)/job
    project=folder/(c['name']+'.ccProject')
    if not project.is_file() or project.stat().st_size<4096:
        raise RuntimeError('Saved CC5 project missing; cannot recover export alone')
    if not is_png(folder/'face.png') or not is_png(folder/(c['name']+'.png')):
        raise RuntimeError('Approved face or render missing; no export-only recovery')
    target=Path(story['out_dir'])/c.get('folder','')/(c['name']+'.iAvatar')
    progress=ROOT/'runs'/story_slug/'cc5_build_queue_progress.json'
    return c,folder,project,target,progress

def status(args):
    c,folder,project,target,progress=load_context(args.story,args.job)
    prior={}
    if progress.exists():
        info=json.loads(progress.read_text(encoding='utf-8-sig'))
        prior=info.get('jobs',{}).get(args.job,{})
    print('EXPORT_RECOVERY',args.job,'STATE',prior.get('status','no queue state'))
    print('PROJECT',project,'BYTES',project.stat().st_size)
    print('TARGET',target,'EXISTS',target.exists())
    print('PREVIOUS_FAILURE',str(prior.get('error',''))[-260:])
    return c,folder,project,target,progress,prior

def recover(args):
    c,folder,project,target,progress,prior=status(args)
    if prior.get('status')=='TECHNICAL_EXPORT_REOPENED_REVIEW_REQUIRED' and target.is_file() and target.stat().st_size>4096:
        print('ALREADY_VERIFIED_NO_ACTION')
        return 0
    if not args.execute:
        print('DRY_RUN_ONLY: pass --execute when CC5 is saved, healthy, and no other CC5 job is active')
        return 0
    if prior.get('status') not in ('BLOCKED','in_progress'):
        raise RuntimeError('Recovery allowed only after a recorded blocked/in-progress export')
    if target.exists() and target.stat().st_size<4096:
        raise RuntimeError('Incomplete destination exists; manual inspection required, no overwrite')
    import msvcrt
    lockfile=ROOT/'runs'/'.cc5_global_production_flow.lock'
    lockfile.parent.mkdir(parents=True,exist_ok=True)
    with lockfile.open('a+b') as lock:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
        try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:raise RuntimeError('Another actor workflow owns CC5, recovery blocked')
        healthy,detail=process_check()
        if not healthy:raise RuntimeError('CC5 not idle: '+detail[:150])
        import ctypes
        from ctypes import wintypes
        import export_ui
        hwnd=export_ui.cc5_window()
        if hwnd is None:raise RuntimeError('CC5 main window not found')
        txt=ctypes.create_unicode_buffer(260)
        export_ui.u32.GetWindowTextW(hwnd,txt,259)
        if '*' in txt.value:
            raise RuntimeError('Unsaved CC5 scene; will not interrupt')
        print('MAIN_WINDOW',txt.value,flush=True)
        if not target.exists():
            opened=bridge('cc5/open_job.py',job=args.job)
            if not re.search(r'avatars=[1-9]\d*',opened):
                raise RuntimeError('Saved project did not reopen a character: '+opened[-230:])
            ok,msg=export_ui.export(str(target),str(folder))
            if not ok:raise RuntimeError('GUI export failed: '+msg)
            print('EXPORT_COMPLETED',msg,flush=True)
        if not target.is_file() or target.stat().st_size<4096:
            raise RuntimeError('iAvatar target missing after export')
        result=bridge('cc5/probes/open_iavatar.py',path=str(target))
        if not re.search(r'avatars=[1-9]\d*',result):
            raise RuntimeError('Export iAvatar reopen failed: '+result[-220:])
        report=json.loads(progress.read_text(encoding='utf-8-sig')) if progress.exists() else {'story':args.story,'jobs':{}}
        report.setdefault('jobs',{})
        previous=report['jobs'].get(args.job,{})
        report['jobs'][args.job]={
            'job':args.job,'status':'TECHNICAL_EXPORT_REOPENED_REVIEW_REQUIRED',
            'technical_export':True,'visual_qa':'REVIEW_REQUIRED',
            'export':str(target),'export_bytes':target.stat().st_size,
            'project':str(project),'reopen_verified':True,
            'recovery_method':'reuse saved ccProject; no face/build rerender',
            'recovered_from_error':str(previous.get('error',''))[-500:],
            'updated':time.strftime('%Y-%m-%d %H:%M:%S')}
        report['updated']=time.strftime('%Y-%m-%d %H:%M:%S')
        # Never claim the batch is complete while an actor remains BLOCKED.
        states=[v.get('status') for v in report['jobs'].values()]
        if states and all(x=='TECHNICAL_EXPORT_REOPENED_REVIEW_REQUIRED' for x in states):
            report['state']='all_processed_review_required'
            report['blocked_jobs']=[]
        elif 'BLOCKED' in states:
            report['state']='partially_blocked'
            report['blocked_jobs']=[name for name,v in report['jobs'].items()
                                    if v.get('status')=='BLOCKED']
        save_json(progress,report)
        print('RECOVERY_VERIFIED',args.job,'BYTES',target.stat().st_size,flush=True)
        msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
    return 0

def selftest():
    assert 'iAvatar' in str(Path('actor.iAvatar'))
    print('SELFTEST_PASS recovery requires saved project and is dry-run by default')
    return 0

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--story')
    parser.add_argument('--job')
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--selftest',action='store_true')
    args=parser.parse_args()
    if args.selftest:return selftest()
    if not args.story or not args.job:parser.error('--story and --job required')
    return recover(args)

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('EXPORT_RECOVERY_BLOCKED',type(exc).__name__,str(exc)[:450],file=sys.stderr)
        sys.exit(2)