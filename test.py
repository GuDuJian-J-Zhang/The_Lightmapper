import bpy
from bpy import context
import The_Lightmapper
import The_Lightmapper.addon.operators.tlm as tlm
from The_Lightmapper.addon.utility import build as utility_build
#from C:/BlenderStuff/addons/The_Lightmapper/addon/utility import build
# Reload the current file and select all.

def bake():
   bpy.ops.wm.open_mainfile(filepath="C:/SourceModels/GIDemoScenes/Room/Blender/Room.blend")
   object_id = 0
   objectids_to_process = []
   for obj in bpy.context.scene.objects:
       if obj.type == 'MESH' and obj.name in bpy.context.view_layer.objects:
           hidden = False
           #We check if the object is hidden
           if obj.hide_get():
              hidden = True
           if obj.hide_viewport:
              hidden = True
           if obj.hide_render:
              hidden = True
           #We check if the object's collection is hidden
           collections = obj.users_collection
           for collection in collections:
               if collection.hide_viewport:
                  hidden = True
               if collection.hide_render:
                  hidden = True
                  
               try:
                  if collection.name in bpy.context.scene.view_layers[0].layer_collection.children:
                      if bpy.context.scene.view_layers[0].layer_collection.children[collection.name].hide_viewport:
                          hidden = True
               except:
                  print("Error: Could not find collection: " + collection.name)
           #Additional check for zero poly meshes
           mesh = obj.data
           if (len(mesh.polygons)) < 1:
               print("Found an object with zero polygons. Skipping object: " + obj.name)
               obj.TLM_ObjectProperties.tlm_mesh_lightmap_use = False
           if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use and not hidden:
               objectids_to_process.append(object_id)
       object_id = object_id + 1
   
   
   print(objectids_to_process)
   
   utility_build.prepare_build(objectids_to_process, background_mode = True)
   utility_build.write_light_map_to_object()

if __name__=="__main__":

    if bpy.app.background:
        bpy.ops.debug.connect_debugger_vscode(waitForClient=True)
    bake()