"""Read-only structural gate for any CC5 Character Studio story.

Usage:
  python tools/cc5_production_preflight.py --story <slug-or-file>
  python tools/cc5_production_preflight.py --story <slug-or-file> --runtime --json
  python tools/cc5_production_preflight.py --selftest

Checks the actual studio/runner.py and tools/gen_faces.py contract; never
launches CC5, generates faces, copies assets, modifies stories or prints tokens.
Exit 0 = required structural checks passed, 2 = blocked, 1 = execution issue.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import sys

ROOT=Path(__file__).resolve().parent.parent
STORIES=ROOT/'stories'
RELAY=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData'/'Local')))/'Tidmunz Studio'/'snapgen_data'/'chrome_relay.json'
ENGINE=RELAY.parent.parent
FACE_FIELDS=('อายุ','เพศ','บทบาท','สีผิว','ใบหน้า')
ALLOWED_SEX={'male','female','m','f'}
ALLOWED_GROUP={'baby','child','adult','middle','old','teen','senior','elderly'}

def inspect_story(d):
    errors=[];warnings=[]
    if not isinstance(d,dict):
        return ['Story JSON root must be an object'],warnings
    chars=d.get('characters')
    if not isinstance(chars,dict) or not chars:
        errors.append('characters must be a nonempty {job_id: character_object} dictionary (not a list)')
        chars={}
    stat=d.get('status')
    if not isinstance(stat,dict):
        errors.append('status must be a dictionary of job progress; strings such as "planning_only" cannot be used')
        stat={}
    out=d.get('out_dir')
    if not isinstance(out,str) or not out.strip():
        errors.append('out_dir must be a nonempty real destination path string (not null)')
    elif os.name=='nt' and not Path(os.path.expandvars(out)).is_absolute():
        warnings.append('out_dir is not absolute on Windows')
    if not isinstance(d.get('title'),str) or not d['title'].strip():
        errors.append('title is required and must be nonempty text')
    for job,c in chars.items():
        label='characters.'+str(job)
        if not isinstance(job,str) or not job.strip():
            errors.append('character job IDs must be nonempty strings')
            continue
        if not isinstance(c,dict):
            errors.append(label+' must be an object')
            continue
        if not isinstance(c.get('name'),str) or not c['name'].strip():
            errors.append(label+'.name must be nonempty')
        if c.get('sex') not in ALLOWED_SEX:
            errors.append(label+'.sex required (male or female; m/f accepted by supporting scripts)')
        if 'age' not in c or not isinstance(c['age'],int) or c['age']<0:
            errors.append(label+'.age must be a nonnegative integer')
        if c.get('age_group') not in ALLOWED_GROUP:
            warnings.append(label+'.age_group absent or nonstandard; check wardrobe and face picker compatibility')
        outfit=c.get('outfit')
        if not isinstance(outfit,list) or not outfit:
            errors.append(label+'.outfit must contain [[source_asset, fabric_or_null], ...]')
        else:
            for i,x in enumerate(outfit):
                if not isinstance(x,(list,tuple)) or len(x)!=2 or not isinstance(x[0],str) or not x[0].strip():
                    errors.append(label+'.outfit['+str(i)+'] must have [nonempty source ID/path, fabric ID or null]')
                elif x[1] is not None and not isinstance(x[1],str):
                    errors.append(label+'.outfit['+str(i)+'] fabric must be string or null')
        parent=c.get('head_from')
        face=c.get('face')
        if parent:
            if parent not in chars or parent==job:
                errors.append(label+'.head_from must refer to another job in the same story')
            if face is not None:
                warnings.append(label+' specifies head_from and face; check identity reuse intent')
        else:
            if not isinstance(face,dict) or not face:
                errors.append(label+'.face must be a nonempty object for Tidmunz Studio ID-portrait generation')
            else:
                missing=[x for x in FACE_FIELDS if not face.get(x)]
                if missing:
                    warnings.append(label+'.face lacks Thai prompt builder descriptors: '+', '.join(missing))
                ref=face.get('ref')
                if ref and (ref not in chars or ref==job):
                    errors.append(label+'.face.ref must refer to another job')
        if job in stat and not isinstance(stat[job],dict):
            errors.append('status.'+job+' must be a dictionary, not text')
        if 'folder' in c and not isinstance(c['folder'],str):
            errors.append(label+'.folder must be text')
    era=d.get('era')
    if not isinstance(era,str) or not era.strip():
        warnings.append('era/period missing; choose an era+social-tier profile before clothing')
    return errors,warnings

def inspect_runtime():
    errors=[];warnings=[];checks={}
    components={
      'tidmunz_program':ENGINE,
      'tidmunz_face_prompt_builder':ENGINE/'snapgen_gui_v2.py',
      'tidmunz_image_generator':ENGINE/'snapgen_modules'/'snapgen_image_gen.py',
      'story_face_generator':ROOT/'tools'/'gen_faces.py',
      'story_kit':ROOT/'kit.py',
      'runner':ROOT/'studio'/'runner.py',
      'cc5_builder':ROOT/'cc5'/'build.py',
      'face_guide':ROOT/'docs'/'FACE_GUIDE.md',
      'qa_standard':ROOT/'docs'/'CHARACTER_QA_STANDARD.md',
    }
    for name,path in components.items():
        ok=path.exists()
        checks[name]=ok
        if not ok: errors.append('Runtime component missing: '+name)
    checks['relay_configuration_exists']=RELAY.is_file()
    if not RELAY.is_file():
        errors.append('Tidmunz Chrome Relay configuration absent; do not use fallback CC5 default faces')
    else:
        try:
            cfg=json.loads(RELAY.read_text(encoding='utf-8-sig'))
            port=int(cfg.get('port',0))
            checks['relay_port_configured']=port>0
            checks['relay_token_configured']=bool(cfg.get('token'))
            if port<=0 or not cfg.get('token'):
                errors.append('Chrome Relay port/token not configured; secrets intentionally not displayed')
            else:
                try:
                    with socket.create_connection(('127.0.0.1',port),timeout=1.3):
                        checks['relay_port_listening']=True
                except OSError:
                    checks['relay_port_listening']=False
                    warnings.append('Relay port is not accepting local TCP connections')
        except (ValueError,OSError,TypeError,json.JSONDecodeError):
            errors.append('Chrome Relay configuration invalid')
    warnings.append('Runtime checks do not prove an image is generated; still require real face.png and Headshot QA')
    return errors,warnings,checks

def selftest():
    base={
      'title':'TEST', 'era':'modern_rural','out_dir':r'C:\temporary\test_out',
      'characters':{'test_01':{
        'name':'ตัวละครทดสอบ','sex':'female','age':30,'age_group':'adult',
        'outfit':[['LIB:sample.ccCloth',None]],
        'face':{'อายุ':'30 ปี','เพศ':'หญิง','บทบาท':'ชาวบ้านไทย',
                'สีผิว':'สองสี','ใบหน้า':'รูปไข่'}
      }},
      'status':{'test_01':{'plan':'ok'}}
    }
    ok,_=inspect_story(base)
    bad=dict(base,characters=[base['characters']['test_01']],status='planning_only',out_dir=None)
    blocked,_=inspect_story(bad)
    if ok or len(blocked)<3:
        raise RuntimeError('Schema gate self-test failed: positive='+str(ok)+' negative='+str(blocked))
    print('SELFTEST_PASS correct Runner shape accepted; malformed story blocked with',len(blocked),'errors')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--story')
    ap.add_argument('--runtime',action='store_true')
    ap.add_argument('--json',action='store_true')
    ap.add_argument('--selftest',action='store_true')
    a=ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.story and not a.runtime:
        ap.error('Pass --story <slug-or-file> and/or --runtime')
    errors=[];warnings=[];checks={}
    if a.story:
        source=Path(a.story)
        if not source.is_file():
            source=STORIES/(a.story if a.story.lower().endswith('.json') else a.story+'.json')
        if not source.is_file():
            errors.append('Cannot find story JSON: '+str(source))
        else:
            try:
                doc=json.loads(source.read_text(encoding='utf-8-sig'))
                e,w=inspect_story(doc)
                errors.extend(e)
                warnings.extend(w)
                checks['story_path']=str(source)
                checks['character_count']=len(doc.get('characters',{}))
            except (UnicodeDecodeError,ValueError,TypeError) as exc:
                errors.append('Story cannot be read: '+type(exc).__name__)
    if a.runtime:
        e,w,details=inspect_runtime()
        errors.extend(e)
        warnings.extend(w)
        checks.update(details)
    output={'status':'BLOCKED' if errors else 'READY_FOR_NEXT_GATE',
            'errors':errors,'warnings':warnings,'checks':checks}
    if a.json:
        print(json.dumps(output,ensure_ascii=False,indent=2))
    else:
        print('PREFLIGHT',output['status'])
        for s in errors:print('ERROR',s)
        for s in warnings:print('WARNING',s)
        for k,v in checks.items():print('CHECK',k,v)
    return 2 if errors else 0

if __name__=='__main__':
    sys.exit(main())