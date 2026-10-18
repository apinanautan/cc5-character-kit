# CC5 > Script > Load Python: shirt TUCKED INTO the trousers/skirt for the current job (first line of batch.txt).
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, layer_fix
importlib.reload(layer_fix)
layer_fix.main("in")
