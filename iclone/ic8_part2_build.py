# Part 2 (มหาอกหัก): villagers seated in a circle under the thatched pavilion (model_1) + monk standing at the temple.
# Loads characters, sit/stand body clip, Look-front face clip, auto blink, lip sync segments, a soft face light each.
# Re-runnable (reuses loaded avatars). Log: ic8_jobs\p2_log.txt, overview still: p2_top.png
import math, os, traceback
import RLPy

J = os.path.join(os.environ["LOCALAPPDATA"], "Tidmunz Studio", "snapgen_data", "ic8_jobs")
CH = r"G:\ไดรฟ์ของฉัน\มหาอกหัก (นิทาน)\มหาอกหัก"
MO = r"G:\คอมพิวเตอร์เครื่องอื่นๆ\คอมพิวเตอร์ของฉัน\โมชั่น"
FACE = MO + r"\Digital Soul 100+\1.Watch\Look front.iTalk"
L = 81.5 + 5.0                      # audio + 300-frame tail
C = (33.0, 566.0)                    # circle centre in the hall (scene ภายในโบสถ์ของวัดอีกวัด)
Z0 = 25774.0                        # hall floor height
R = 130.0
log = []
USE_BODY_MOTION = False  # body pose comes from AccuPOSE (applied by hand per character); motions only for face

# name: (file, (x,y) or angle on circle, body motion, female?, lip-sync [(wav, start)])
CAST = {
    "monk":  (r"1. พระมหาสมชาติ\พระมหาสมชาติ เจ้าอาวาส วัย 48.iAvatar", ("xy", 33, 966, 0), r"โมชั่น\03_CC MixMove_Male\SitG03.iMotion", False, []),
    "im":    (r"3. นายอิ่ม มัคนายก\นายอิ่ม มัคนายกวัด วัย 55.iAvatar", ("ang", 90), r"โมชั่น\03_CC MixMove_Male\SitG03.iMotion", False, [("p2_im.wav", 13.4)]),
    "old":   (r"2. ชาวบ้าน\ชาวบ้าน ชายแก่ วัย 68.iAvatar", ("ang", 162), r"โมชั่น\03_CC MixMove_Male\SitG03.iMotion", False, [("p2_old.wav", 1.4)]),
    "woman": (r"2. ชาวบ้าน\ชาวบ้าน หญิงวัยกลางคน วัย 45.iAvatar", ("ang", 18), r"โมชั่น\04_CC MixMove_Female\SitG04.iMotion", True, [("p2_woman.wav", 31.7)]),
    "young": (r"2. ชาวบ้าน\ชาวบ้าน ชายหนุ่ม วัย 25.iAvatar", ("ang", 234), r"โมชั่น\03_CC MixMove_Male\SitG03.iMotion", False, [("p2_young.wav", 40.8)]),
    "commf": (r"4. กรรมการวัด + ลูกศิษย์วัด\กรรมการวัด หญิง วัย 52.iAvatar", ("ang", 306), r"โมชั่น\04_CC MixMove_Female\SitG04.iMotion", True, []),
}


def T(s):
    return RLPy.RTime.FromValue(int(round(s * 6000)))


def zq(d):
    h = math.radians(d) / 2
    return (0.0, 0.0, math.sin(h), math.cos(h))


def qm(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw*bx+ax*bw+ay*bz-az*by, aw*by-ax*bz+ay*bw+az*bx, aw*bz+ax*by-ay*bx+az*bw, aw*bw-ax*bx-ay*by-az*bz)


def look(cp, tg):
    dx, dy, dz = tg[0]-cp[0], tg[1]-cp[1], tg[2]-cp[2]
    p = math.atan2(dz, math.hypot(dx, dy))
    return qm(zq(math.degrees(math.atan2(-dx, dy))), qm((math.sin(p/2), 0, 0, math.cos(p/2)), (math.sin(math.radians(45)), 0, 0, math.cos(math.radians(45)))))


def setT(obj, s, pos, q):
    c = obj.GetControl("Transform"); t = RLPy.RTransform(); c.GetValue(T(s), t)
    t.T().x, t.T().y, t.T().z = pos
    t.R().x, t.R().y, t.R().z, t.R().w = q
    c.SetValue(T(s), t)


def fill(clip):
    """user rule: slow as much as possible to span L; if that would go below 0.5, use 0.5 (caller chains copies).
    returns (scene length of the clip, speed)"""
    clip.SetSpeed(1.0)
    raw = clip.GetClipLength().ToFloat() / 6000
    sp = max(0.5, raw / L)
    clip.SetSpeed(sp)
    return raw / sp, sp


try:
    RLPy.RGlobal.SetProjectLength(T(L))  # SetEndTime alone does not lengthen the timeline
    RLPy.RGlobal.SetEndTime(T(L))
    for a in RLPy.RScene.GetAvatars():
        if a.GetName() == "Sunee":  # extra avatar from another story
            RLPy.RScene.RemoveObject(a)
    box = RLPy.RScene.FindObject(RLPy.EObjectType_Prop, "Box_001")
    if box: RLPy.RScene.Hide(box)  # user's placement marker
    spot = [l for l in RLPy.RScene.FindObjects(RLPy.EObjectType_Light) if l.GetName() == "Spotlight"]
    lights = {l.GetName(): l for l in RLPy.RScene.FindObjects(RLPy.EObjectType_Light)}

    for key, (f, place, mot, fem, lips) in CAST.items():
        name = "p2_" + key
        av = next((a for a in RLPy.RScene.GetAvatars() if a.GetName() == name), None)
        if not av:
            before = set(a.GetID() for a in RLPy.RScene.GetAvatars())
            RLPy.RScene.ClearSelectObjects()
            RLPy.RFileIO.LoadFile(os.path.join(CH, f))
            av = [a for a in RLPy.RScene.GetAvatars() if a.GetID() not in before][0]
            av.SetName(name)
        RLPy.RGlobal.RemoveAllAnimations(av)
        if place[0] == "xy":
            x, y, yaw = place[1], place[2], place[3]
        else:
            ang = math.radians(place[1])
            x, y = C[0] + R * math.cos(ang), C[1] + R * math.sin(ang)
            yaw = math.degrees(math.atan2(C[0] - x, -(C[1] - y)))  # face the centre (yaw 0 = -Y)
        setT(av, 0, (x, y, Z0), zq(yaw))

        # body: one clip slowed to fill, chained if needed
        sk = av.GetSkeletonComponent()
        cur = 0.0
        while USE_BODY_MOTION and cur < L - 0.05:
            RLPy.RFileIO.LoadMotion(os.path.join(MO, mot), T(cur), av)
            cl = sk.GetClip(sk.GetClipCount() - 1)
            d, sp = fill(cl)
            if cur + d > L:
                cl.SetLength(T((L - cur) * sp))  # SetLength is in clip time
            cur += d
        # face: Look front, same rule
        fc = av.GetFaceComponent()
        RLPy.RScene.ClearSelectObjects(); RLPy.RScene.SelectObject(av)
        cur = 0.0
        while cur < L - 0.05:
            RLPy.RGlobal.SetTime(T(cur))
            RLPy.RFileIO.LoadFile(FACE)
            cl = fc.GetClip(fc.GetClipCount() - 1)
            d, sp = fill(cl)
            cur += d
        fc.SetAutoBlinkName("Normal")
        for wav, st in lips:
            RLPy.RAudio.LoadAudioToObject(av, os.path.join(J, wav), T(st))
        # soft face light
        lname = "FaceLight_" + key
        lt = lights.get(lname)
        if not lt and spot:
            lt = spot[0] if not lights.get("FaceLight_used") and spot[0].GetName() == "Spotlight" else spot[0].Clone()
            if lt.GetName() == "Spotlight":
                lights["FaceLight_used"] = True
            lt.SetName(lname)
        if lt:
            fz = Z0 + 95          # face height standing / sitting on the floor
            fdir = (math.sin(math.radians(yaw)), -math.cos(math.radians(yaw)))   # facing vector
            side = (-fdir[1], fdir[0])
            face = (x, y, fz)
            lp = (x + fdir[0] * 220 + side[0] * 120, y + fdir[1] * 220 + side[1] * 120, fz + 55)
            setT(lt, 0, lp, look(lp, face))
            lt.SetColor(T(0), RLPy.RRgb(255, 236, 214))
            lt.SetMultiplier(T(0), 0.04)
            lt.SetRange(T(0), 700)
            lt.SetCastShadow(False)
        log.append("%s at (%.0f,%.0f) yaw %.0f body %d clips face %d clips lips %d" % (
            name, x, y, yaw, sk.GetClipCount(), fc.GetClipCount(), len(lips)))

    # overview still from Camera_0 (temporary framing; real shots are keyed later)
    cam = [c for c in RLPy.RScene.FindObjects(RLPy.EObjectType_Camera) if c.GetName() != "Preview Camera"][0]
    RLPy.RGlobal.RemoveAllAnimations(cam)
    cam.SetFocalLength(T(0), 35)
    cp = (C[0] - 700, C[1] - 500, 260)
    setT(cam, 0, cp, look(cp, (C[0], C[1], 60)))
    RLPy.RScene.SetCurrentCamera(cam)
    RLPy.RGlobal.SetTime(T(3))
    RLPy.RGlobal.RenderImage(os.path.join(J, "p2_top.png"))
except Exception:
    log.append(traceback.format_exc())
open(os.path.join(J, "p2_log.txt"), "w", encoding="utf-8").write("\n".join(log))





