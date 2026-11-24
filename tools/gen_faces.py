"""Generate Thai face portraits with a physically separate chat per character.

Every job stores only its own ChatGPT conversation cursor under the character
job directory. This NEVER reads or modifies a global Story Face chat/history.
Related-age variants may use an explicitly named prior face as an image reference,
but still use a new independent conversation, not the relative's chat.
"""
import ast
import base64
import json
import os
from pathlib import Path
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

PROGRAM=Path(kit.PROGRAM)
sys.path[:0]=[str(PROGRAM),str(PROGRAM/'snapgen_modules')]
builder_source=(PROGRAM/'snapgen_gui_v2.py').read_text(encoding='utf-8')
builder_ast=ast.parse(builder_source)
builder_function=next(n for n in builder_ast.body if isinstance(n,ast.FunctionDef)
                      and n.name=='_build_story_face_prompt_from_character')
builder_ns={}
exec(ast.get_source_segment(builder_source,builder_function),builder_ns)
build=builder_ns[builder_function.name]
generate_image=kit.image_gen()

def png_valid(path):
    try:
        path=Path(path)
        if not path.is_file() or path.stat().st_size<1024:
            return False
        with path.open('rb') as f:
            header=f.read(24)
        return (header[:8]==bytes((137,80,78,71,13,10,26,10))
                and int.from_bytes(header[16:20],'big')>=128
                and int.from_bytes(header[20:24],'big')>=128)
    except (OSError,ValueError):
        return False

def separate_chat(job_dir,story_key,job_id):
    """Return per-character mutable context and its own persisted save callback."""
    path=Path(job_dir)/'face_chat_context.json'
    if path.exists():
        record=json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(record,dict) or record.get('owner_job')!=job_id or record.get('owner_story')!=story_key:
            raise RuntimeError('Refuse cross-character face-chat reuse: '+str(path))
    else:
        record={'owner_story':story_key,'owner_job':job_id}
    def save():
        tmp=path.with_suffix('.json.writing')
        tmp.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
        os.replace(tmp,path)
    return record,save

def run(story_ref,only=()):
    story=kit.load_story(story_ref)
    slug=str(story.get('slug') or Path(story_ref).stem)
    only=set(only)
    failures=[]
    for job,c in story['characters'].items():
        if (only and job not in only) or not isinstance(c.get('face'),dict):
            continue
        job_dir=Path(kit.JOBS)/job
        job_dir.mkdir(parents=True,exist_ok=True)
        face=job_dir/'face.png'
        if face.exists():
            if png_valid(face):
                print('EXISTING_VALID_FACE',job,flush=True)
                continue
            print('FAIL',job,'invalid existing face.png; refuse overwrite',flush=True)
            failures.append(job)
            continue
        try:
            state,save_chat=separate_chat(job_dir,slug,job)
            fields={k:v for k,v in c['face'].items() if k not in ('prompt_name','ref')}
            prompt=build(dict(fields,name=c['face'].get('prompt_name',c.get('name',job))))
            prompt=(
                'ภาพคนไทยจริงจากบทนี้ มีเอกลักษณ์เฉพาะตัว ไม่ใช้ใบหน้าตัวละครอื่น '
                'ไม่ยึดใบหน้าในแชทเก่า ไม่ใช้หน้าฝรั่งสำเร็จรูป ให้ยึดอายุ '
                'โครงหน้า สีผิว และบุคลิกจากรายละเอียดเฉพาะคนนี้เท่านั้น\n\n'
                +prompt
            )
            refs=None
            ref=c['face'].get('ref')
            if ref:
                if ref==job:
                    raise RuntimeError('A character cannot be its own reference')
                if ref not in story['characters']:
                    raise RuntimeError('Face reference is absent from story: '+str(ref))
                prior=Path(kit.JOBS)/ref/'face.png'
                if not png_valid(prior):
                    raise RuntimeError('Related character reference missing: '+str(prior))
                refs=[base64.b64encode(prior.read_bytes()).decode('ascii')]
                prompt='ตัวละครคนเดียวกันต่างวัย ใช้ภาพอ้างอิงเพื่อคงอัตลักษณ์ใบหน้า แต่สร้างในแชทแยกต่างหาก\n'+prompt
            print('FACE_CHAT_ISOLATED',slug,job,
                  'CURSOR_REUSED_FOR_SAME_JOB',bool(state.get('conversation_id')),
                  'REFERENCE_IMAGE',bool(refs),flush=True)
            generated=generate_image(
                prompt,output_dir=str(job_dir),name_hint='face_'+job,
                aspect_ratio='3:4',is_edit=bool(refs),ref_images=refs,
                use_story_history=False,use_ref_story_history=False,
                use_story_face_history=False,use_prop_history=False,
                conversation_state=state,conversation_save_fn=save_chat,
                temporary_chat=False
            )
            source=Path(generated)
            if not png_valid(source):
                raise RuntimeError('Tidmunz did not return a valid PNG portrait')
            if source.resolve()!=face.resolve():
                os.replace(source,face)
            print('OK',job,'FACE_BYTES',face.stat().st_size,
                  'CHAT_STATE',job_dir/'face_chat_context.json',flush=True)
        except Exception:
            print('FAIL',job,traceback.format_exc()[-1100:],flush=True)
            failures.append(job)
    if failures:
        print('FAILED_FACE_JOBS',','.join(failures),flush=True)
        return 1
    return 0

if __name__=='__main__':
    if len(sys.argv)<2:
        print('Usage: python tools/gen_faces.py <story_json_or_slug> [job ...]',file=sys.stderr)
        sys.exit(2)
    sys.exit(run(sys.argv[1],sys.argv[2:]))