import bpy
name="bl_ext.user_default.hairmesh"
print("FOUND_FOLDER",__import__("os").path.isfile(__import__("os").path.join(next(r.directory for r in bpy.context.preferences.extensions.repos if r.module=="user_default"),"hairmesh","__init__.py")))
print("BEFORE",name in bpy.context.preferences.addons)
try:
    result=bpy.ops.preferences.addon_enable(module=name)
    print("ENABLE_OP",str(result))
    print("AFTER",name in bpy.context.preferences.addons)
    print("ADDON_MODULE",__import__("importlib").import_module(name).__file__)
    bpy.ops.wm.save_userpref()
    print("SAVED_USERPREF",True)
except Exception as e:
    import traceback
    traceback.print_exc()
    raise
