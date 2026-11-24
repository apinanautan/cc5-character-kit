import RLPy
avs=RLPy.RScene.GetAvatars()
BRIDGE_RESULT='avatars='+repr([(a.GetName(),str(a.GetType())) for a in avs])