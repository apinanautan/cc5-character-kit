"""Executable era/social tier policy before clothing or face generation.

Not a substitute for visual QA: only grounded role/period signals and obvious
royal/commoner costume errors can be checked deterministically.
"""
import json
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
PROFILES=ROOT/'docs'/'production'/'ERA_PROFILES.json'
HISTORIC=('ayutthaya','sukhothai','rattanakosin','ancient_thai')
def era_name(story):
    x=str(story.get('era_profile','')).strip()
    if x:return x,'explicit'
    s=str(story.get('era','')).lower()
    if any(w in s for w in ('ปกรณัม','ตำนานเทพ','สวรรค์','เทพนิยาย','mytholog','fantasy')):
        return 'thai_mythic_royal_fantasy','inferred_from_era'
    if any(w in s for w in ('อยุธยา','ayutthaya')):
        return 'ayutthaya_royal' if any(w in s for w in ('ราชสำนัก','พระราชวัง','royal','กษัตริย์')) else 'ayutthaya_commoner','inferred_from_era'
    if any(w in s for w in ('สุโขทัย','sukhothai')):
        return 'sukhothai_royal' if any(w in s for w in ('ราชสำนัก','royal','กษัตริย์')) else 'sukhothai_commoner','inferred_from_era'
    if any(w in s for w in ('รัตนโกสินทร์','rattanakosin')):
        return 'early_rattanakosin_royal' if any(w in s for w in ('ราชสำนัก','royal','กษัตริย์')) else 'early_rattanakosin_commoner','inferred_from_era'
    if any(w in s for w in ('ไทยโบราณ','โบราณ','ancient')):
        return 'ancient_thai_unspecified','inferred_from_era'
    if any(w in s for w in ('ปัจจุบัน','ร่วมสมัย','contemporary','modern')):
        if any(w in s for w in ('ชนบท','ต่างจังหวัด','หมู่บ้าน','rural')):
            return 'modern_rural','inferred_from_era'
        if any(w in s for w in ('กรุงเทพ','มหานคร','ในเมือง','urban','city')):
            return 'modern_urban','inferred_from_era'
    return None,'not_grounded'
def social_tier(actor,era):
    explicit=actor.get('social_tier')
    if explicit:return explicit,'explicit'
    face=actor.get('face') if isinstance(actor.get('face'),dict) else {}
    text=' '.join(str(v) for v in (actor.get('name',''),face.get('บทบาท',''),actor.get('notes',''),actor.get('style',''))).lower()
    for words,tier in [
        (('พระราชา','พระมหากษัตริย์','กษัตริย์','ราชินี','ราชาธิราช','พระมเหสี','เจ้าชาย','เจ้าหญิง'),'royalty'),
        (('อสูร','ยักษ์','asura'),'mythic_asura'),
        (('เทวดา','เทพเจ้า','ท้าวสักกะ','deity'),'mythic_deity'),
        (('พระภิกษุ','พระสงฆ์','หลวงพ่อ','เจ้าอาวาส','สามเณร'),'clergy'),
        (('เสนาบดี','ขุนนาง','อำมาตย์','ราชสำนัก'),'court_official'),
        (('ข้าราชการ','ตำรวจ','ผู้ว่าราชการ','ครู','เจ้าหน้าที่รัฐ'),'civil_servant'),
        (('ชาวนา','ชาวสวน','ชาวบ้าน','เกษตรกร','ทำนา'),'rural_commoner'),
        (('กรรมกร','คนงาน','แรงงาน','ช่างก่อสร้าง'),'laborer'),
        (('พ่อค้า','แม่ค้า','นักธุรกิจ','เจ้าของกิจการ','ผู้บริหาร'),'merchant'),
        (('เด็ก','ลูกชาย','ลูกสาว','ทารก','เด็กหญิง','เด็กชาย'),'child')
    ]:
        if any(w in text for w in words):return tier,'inferred_from_explicit_role'
    if era=='modern_rural':return 'rural_commoner','assumed_from_story_setting_REVIEW'
    if era=='modern_urban':return 'urban_middle_class','assumed_from_story_setting_REVIEW'
    return None,'needs_character_tier'
def inspect_culture(story,jobs):
    errors=[];warnings=[];classified={}
    try:
        cfg=json.loads(PROFILES.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError):
        return ['Cannot read ERA_PROFILES.json'],warnings,classified
    known=cfg.get('profiles',{})
    era,origin=era_name(story)
    if era not in known:
        return ['era_profile missing or unknown; choose one of '+', '.join(sorted(known))],warnings,classified
    if origin!='explicit':
        warnings.append('Era inferred from story era; confirm '+era+' before approving visually')
    for j in jobs:
        c=story.get('characters',{}).get(j)
        if not isinstance(c,dict):continue
        tier,reason=social_tier(c,era)
        if tier not in set(cfg.get('tiers',[])):
            errors.append(j+': social_tier unknown; set a valid social_tier according to role')
            continue
        classified[j]={'era_profile':era,'era_source':origin,'social_tier':tier,'tier_source':reason}
        if reason.startswith('assumed'):
            warnings.append(j+': social tier tentatively assumed; user/visual review required')
        if era in ('modern_urban','modern_rural') and tier in ('mythic_deity','mythic_asura','royalty'):
            warnings.append(j+': modern setting with royal/mythic tier; verify story premise')
        costume=c.get('outfit',[])
        for item in costume if isinstance(costume,list) else []:
            if not isinstance(item,(list,tuple)) or not item:continue
            name=os.path.basename(str(item[0])).lower()
            royal=('crown','coronet','diadem','royal','ราชาภิเษก','ชฎา','มงกุฎ')
            western=('business suit','tuxedo','blazer','formal jacket','western suit')
            if tier in ('rural_commoner','laborer','child','urban_middle_class') and any(t in name for t in royal):
                errors.append(j+': royal regalia asset unsuitable for nonroyal role: '+name)
            if era.startswith(HISTORIC) and any(t in name for t in western):
                errors.append(j+': obviously modern business clothing in historical era: '+name)
    return errors,warnings,classified
def selftest():
    def actor(name,social=None):
        x={'name':name,'face':{'บทบาท':name},'outfit':[['Ordinary Shirt.ccCloth',None]]}
        if social:x['social_tier']=social
        return x
    data={'era':'คนไทยต่างจังหวัด ยุคปัจจุบัน','characters':{'a':actor('ชาวบ้าน'),'b':actor('พ่อค้า')}}
    e,w,meta=inspect_culture(data,['a','b'])
    assert not e and meta['a']['era_profile']=='modern_rural' and meta['b']['social_tier']=='merchant'
    data['characters']['a']['outfit']=[['Royal Crown.ccCloth',None]]
    e,w,meta=inspect_culture(data,['a','b'])
    assert e and 'royal regalia' in e[0]
    assert inspect_culture({'characters':{'x':actor('ชาวบ้าน')}},['x'])[0]
    print('SELFTEST_PASS era inference, Thai role classification, nonroyal regalia hard block, ambiguous era hard block')
if __name__=='__main__':selftest()