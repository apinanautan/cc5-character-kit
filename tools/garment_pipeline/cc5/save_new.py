# Inside CC5 via bridge: save the current character to a NEW .ccProject (refuses to overwrite). args: save=<path>
import os, sys, RLPy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc5util import save_character
save_character(RLPy.RScene.GetAvatars()[0], BRIDGE_ARGS["save"])  # noqa
BRIDGE_RESULT = "saved " + BRIDGE_ARGS["save"]  # noqa
