bl_info = {
   'name': 'Debugger for VS Code',
   'author': 'Alan North',
   'version': (0, 1, 0),
   'blender': (2, 79, 0),
   "description": "Starts debugging server for VS Code.",
   'location': 'In search (default shortcut:space) type "Debug"',
   "warning": "",
   "wiki_url": "https://github.com/AlansCodeLog/blender-debugger-for-vscode",
   "tracker_url": "https://github.com/AlansCodeLog/blender-debugger-for-vscode/issues",
   'category': 'Development',
}

import bpy
import sys
import os
import subprocess
import re

# check path for ptvsd
def check_for_ptvsd():
   #check for python with where/whereis
   python_exe = None
   try:
      python_exe = subprocess.Popen(
         ["whereis", "python"],
         shell=False,
         stdout=subprocess.PIPE,
         stderr=subprocess.PIPE
      )
   except Exception: 
      pass
   if python_exe is None:
      try: 
         python_exe = subprocess.Popen(
               ["where", "python"],
               shell=False,
               stdout=subprocess.PIPE,
               stderr=subprocess.PIPE
            )
      except Exception: 
         pass
   if python_exe is None:
      try: 
         python_exe = subprocess.Popen(
               ["which", "python"],
               shell=False,
               stdout=subprocess.PIPE,
               stderr=subprocess.PIPE
            )
      except Exception: 
         pass
   if python_exe is not None:
      python_exe = str(python_exe.communicate()[0], "utf-8")
      match = re.search(".*(\\\\|/)", python_exe).group() 
      if os.path.exists(match+"lib\site-packages\ptvsd"):
         return match+"lib\site-packages"

   #check in our path
   for path in sys.path:
      if os.path.exists(path+"\ptvsd"):
         return path
      if os.path.exists(path+"\site-packages\ptvsd"):
         return path+"\site-packages"
      if os.path.exists(path+"\lib\site-packages\ptvsd"):
         return path+"lib\site-packages"
   return "PTVSD not Found"

# Preferences
class DebuggerPreferences(bpy.types.AddonPreferences):
   bl_idname = __name__

   path = bpy.props.StringProperty(
      name="Location of PTVSD",
      subtype="DIR_PATH",
      default=check_for_ptvsd()
   )

   timeout = bpy.props.IntProperty(
      name="Timeout",
      default=20
   )
   def draw(self, context):
      layout = self.layout
      layout.prop(self, "path")
      layout.label(text="Pluging will try to auto-find it, if no path found, or you would like to use a different path, set it here.")
      row = layout.split()
      row.label(text="Timeout in seconds for attach confirmation listener.")
      row.prop(self, "timeout")

# check if debugger has attached
def check_done(i, modal_limit):
   if i == 0 or i % 60 == 0:
      print("Waiting...")
   if i > modal_limit:
      print("Attach Confirmation Listener Timed Out")
      return {"CANCELLED"}
   if not ptvsd.is_attached():
      return {"PASS_THROUGH"}
   print('Debugger is Attached')
   return {"FINISHED"}
   
class DebuggerCheck(bpy.types.Operator):
   bl_idname = "debug.check_for_debugger"
   bl_label = "Debug: Check if VS Code is Attached"
   bl_description = "Starts modal timer that checks if debugger attached until attached or until timeout."

   _timer = None
   count = 0
   modal_limit = 20*60

   # call check_done
   def modal(self, context, event):
      self.count = self.count + 1
      if event.type == "TIMER":
         return check_done(self.count, self.modal_limit)
      return {"PASS_THROUGH"} 

   def execute(self, context):
      # set initial variables
      self.count = 0
      prefs = bpy.context.user_preferences.addons[__name__].preferences
      self.modal_limit = prefs.timeout*60

      wm = context.window_manager
      self._timer = wm.event_timer_add(0.1, context.window)
      wm.modal_handler_add(self)
      return {"RUNNING_MODAL"}

   def cancel(self, context):
      print("Debugger Confirmation Cancelled")
      wm = context.window_manager
      wm.event_timer_remove(self._timer)

class DebugServerStart(bpy.types.Operator): 
   bl_idname = "debug.connect_debugger_vscode"
   bl_label = "Debug: Start Debug Server for VS Code"
   bl_description = "Starts ptvsd server for debugger to attach to."
   
   def execute(self, context):
      #get ptvsd and import if exists
      prefs = bpy.context.user_preferences.addons[__name__].preferences
      ptvsd_path = prefs.path

      #actually check ptvsd is still available
      if ptvsd_path == "PTVSD not Found":
         self.report({"ERROR"}, "Couldn't detect ptvsd, please specify the path manually in the addon preferences or reload the addon if you installed ptvsd after enabling it.")
         return {"CANCELLED"}
      
      if not os.path.exists(os.path.abspath(ptvsd_path+"/ptvsd")):
         self.report({"ERROR"}, "Can't find ptvsd at: %r/ptvsd." % ptvsd_path)
         return {"CANCELLED"}

      if not any(ptvsd_path in p for p in sys.path):
         sys.path.append(ptvsd_path)

      global ptvsd #so we can do check later
      import ptvsd

      version = re.sub("\.", "", ptvsd.__version__)
      if int(version) > 3000: 
         print("Warning: PTVSD version " + ptvsd.__version__ + " is greater than 3.0.0, it will not work with VS Code.")

      # can only be attached once, no way to detach (at least not that I understand?)
      try:
         ptvsd.enable_attach("my_secret", address = ("0.0.0.0", 3000))
      except:
         print("Server already running.")

      # call our confirmation listener
      bpy.ops.debug.check_for_debugger()
      return {"FINISHED"}
   
def register():
   bpy.utils.register_module(__name__)

def unregister():
   bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
   register()
