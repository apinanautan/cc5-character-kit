"""A validated, per-story asset lock for CC5; no random replacement."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def locked_look(story,job,actor):
    slug=story.get('slug')
    if not isinstance(slug,str) or not slug:
        raise RuntimeError('WARDROBE_MISSING_STORY_SLUG')
    p=ROOT/'runs'/slug/'wardrobe_design.json'
    if not p.is_file():
        raise RuntimeError('WARDROBE_NOT_PLANNED: '+str(p))
    plan=json.loads(p.read_text(encoding='utf-8-sig'))
    if plan.get('story_slug')!=slug or plan.get('era_profile')!=story.get('era_profile'):
        raise RuntimeError('WARDROBE_STORY_OR_ERA_MISMATCH')
    record=plan.get('looks',{}).get(job)
    if not isinstance(record,dict) or record.get('character_name')!=actor.get('name'):
        raise RuntimeError('WARDROBE_ACTOR_NOT_PLANNED: '+job)
    if record.get('selection_status')!='script_grounded_locked_pending_visual_qa':
        raise RuntimeError('WARDROBE_SELECTION_NOT_LOCKED: '+job)
    items=record.get('outfit',[])
    slots=[x.get('slot') for x in items]
    if actor.get('age_group')=='baby':
        # A one-year-old can wear either a one-piece or a properly reviewed top + shorts.
        # Bare feet are normal for a toddler; do not force adult shoes.
        if slots not in (['full'], ['upper','lower']):
            raise RuntimeError('BABY_AGE_APPROPRIATE_OUTFIT_REQUIRED: '+job)
    elif sorted(slots)!=sorted(['upper','lower','shoes']):
        raise RuntimeError('REQUIRED_WARDROBE_SLOTS_MISSING: '+job)
    if len(set(slots))!=len(slots):raise RuntimeError('DUPLICATE_WARDROBE_SLOT: '+job)
    outfit=[]
    for x in items:
        source=x.get('resolved_source_path')
        if not isinstance(source,str) or not Path(source).is_file():
            raise RuntimeError('SOURCE_ASSET_NOT_FOUND: '+str(source))
        if Path(source).suffix.lower() not in ('.cccloth','.ccshoes','.ccaccessory'):
            raise RuntimeError('INVALID_GARMENT_TYPE: '+source)
        lower=Path(source).stem.lower()
        forbidden=('pyjamas','pajamas','underwear','lingerie','bikini')
        if any(word in lower for word in forbidden):
            raise RuntimeError('INAPPROPRIATE_ITEM_BLOCKED: '+job+' '+lower)
        if 'school_blouse' in lower and actor.get('occasion')!='school':
            raise RuntimeError('UNJUSTIFIED_SCHOOL_UNIFORM: '+job)
        if 'scrub' in lower and actor.get('occasion')=='hospital_patient':
            raise RuntimeError('SCRUB_NOT_PATIENT_GOWN: '+job)
        if x.get('available') is not True or not x.get('brief_reason'):
            raise RuntimeError('WARDROBE_REASON_OR_AVAILABILITY_MISSING: '+job)
        fabric=x.get('fabric_id')
        if fabric is not None and not isinstance(fabric,str):
            raise RuntimeError('INVALID_FABRIC: '+job)
        outfit.append((source,fabric))
    hair=record.get('hair_source_path')
    if hair:
        if not Path(hair).is_file() or Path(hair).suffix.lower()!='.rlhair':
            raise RuntimeError('HAIR_NOT_AVAILABLE: '+job)
        # Only block *proven* runtime asset failures. Old absolute paths alone
        # are not proof a hair is unusable; successful hairs may embed them.
        import os
        issues=ROOT/"data"/"cc5_hair_runtime_failures.json"
        if issues.is_file():
            records=json.loads(issues.read_text(encoding="utf-8-sig"))
            current=os.path.normcase(os.path.normpath(str(hair))).casefold()
            meta=Path(hair).stat()
            for bad in records.get("asset_failures",[]):
                path=os.path.normcase(os.path.normpath(bad.get("asset_path",""))).casefold()
                if path==current and meta.st_size==bad.get("asset_size_bytes") and meta.st_mtime_ns==bad.get("asset_mtime_ns"):
                    raise RuntimeError("HAIR_CONFIRMED_MISSING_TEXTURES: "+Path(hair).name)
    elif actor.get('age_group')!='baby' and not actor.get('head_from'):
        raise RuntimeError('NO_HAIR_PLAN: '+job)
    return record,outfit,hair

def build_load_order(locked_record,planned_outfit):
    """Order lower first, upper last among cloth to make CC5 upper.txt accurate.

    CC5 build.py updates upper.txt for every cloth that is loaded, and
    layer_fix.py interprets that last-cloth name as the upper garment.
    Shoes may load after upper because they do not update upper.txt.
    """
    items=locked_record.get("outfit",[])
    if len(items)!=len(planned_outfit):
        raise RuntimeError("WARDROBE_PLAN_ITEM_COUNT_MISMATCH")
    rank={"lower":0,"full":1,"upper":1,"shoes":2}
    paired=[]
    for locked,chosen in zip(items,planned_outfit):
        slot=locked.get("slot")
        if slot not in rank:
            raise RuntimeError("WARDROBE_UNKNOWN_SLOT: "+str(slot))
        if str(locked.get("resolved_source_path"))!=str(chosen[0]):
            raise RuntimeError("WARDROBE_LOCK_SOURCE_MISMATCH")
        paired.append((locked,chosen))
    return sorted(paired,key=lambda item:rank[item[0]["slot"]])
