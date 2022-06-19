'''
Copyright (C) 2018 Alan North
alannorth@gmail.com

Created by Alan North

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
   'name': 'Debugger for VS Code',
   'author': 'Alan North',
   'version': (2, 2, 0),
   'blender': (2, 80, 0), # supports 2.8+
   "description": "Starts debugging server for VS Code.",
   'location': 'In search (Edit > Operator Search) type "Debug"',
   "warning": "",
   "wiki_url": "https://github.com/AlansCodeLog/blender-debugger-for-vscode",
   "tracker_url": "https://github.com/AlansCodeLog/blender-debugger-for-vscode/issues",
   'category': 'Development',
}

import os
import re
import subprocess
import sys

import bpy


# finds path to debugpy if it exists
def check_for_debugpy():
   pip_info = None
   try:
      pip_info = subprocess.Popen(
          "pip show debugpy",
          shell=True,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE
      )
   except Exception as e:
      print(e)
      pass
   if pip_info is not None:
      pip_info = str(pip_info.communicate()[0], "utf-8")
      pip_info = re.sub("\\\\", "/", pip_info)
      #extract path up to last slash
      match = re.search("Location: (.*)", pip_info)
      #normalize slashes
      if match is not None:
         match = match.group(1)
         if os.path.exists(match+"/debugpy"):
            return match

  # commands to check
   checks = [
       ["where", "python"],
       ["whereis", "python"],
       ["which", "python"],
   ]
   location = None
   for command in checks:
      try:
         location = subprocess.Popen(
             command,
             shell=True,
             stdout=subprocess.PIPE,
             stderr=subprocess.PIPE
         )
      except Exception:
         continue
      if location is not None:
         location = str(location.communicate()[0], "utf-8")
         #normalize slashes
         location = re.sub("\\\\", "/", location)
         #extract path up to last slash
         match = re.search(".*(/)", location)
         if match is not None:
            match = match.group(1)
            if os.path.exists(match+"lib/site-packages/debugpy"):
               match = match+"lib/site-packages"
               return match

   # check in path just in case PYTHONPATH happens to be set
   # this is not going to work because Blender's sys.path is different
   for path in sys.path:
      path = path.rstrip("/")
      if os.path.exists(path+"/debugpy"):
         return path
      if os.path.exists(path+"/site-packages/debugpy"):
         return path+"/site-packages"
      if os.path.exists(path+"/lib/site-packages/debugpy"):
         return path+"lib/site-packages"
   return "debugpy not Found"

# Preferences
class DebuggerPreferences(bpy.types.AddonPreferences):
   bl_idname = __name__

   path: bpy.props.StringProperty(
      name="Location of debugpy (site-packages folder)",
      subtype="DIR_PATH",
      default=check_for_debugpy()
   )

   timeout: bpy.props.IntProperty(
      name="Timeout",
      default=20
   )

   port: bpy.props.IntProperty(
      name="Port",
      min=0,
      max=65535,
      default=5678
   )
   def draw(self, context):
      layout = self.layout
      row_path = layout
      row_path.label(text="The addon will try to auto-find the location of debugpy, if no path is found, or you would like to use a different path, set it here.")
      row_path.prop(self, "path")

      row_timeout = layout.split()
      row_timeout.prop(self, "timeout")
      row_timeout.label(text="Timeout in seconds for the attach confirmation listener.")

      row_port = layout.split()
      row_port.prop(self, "port")
      row_port.label(text="Port to use. Should match port in VS Code's launch.json.")


# check if debugger has attached
def check_done(i, modal_limit, prefs):
   if i == 0 or i % 60 == 0:
      print("Waiting... (on port "+str(prefs.port)+")")
   if i > modal_limit:
      print("Attach Confirmation Listener Timed Out")
      return {"CANCELLED"}
   if not debugpy.is_client_connected():
      return {"PASS_THROUGH"}
   print('Debugger is Attached')
   return {"FINISHED"}

class DebuggerCheck(bpy.types.Operator):
   bl_idname = "debug.check_for_debugger"
   bl_label = "Debug: Check if VS Code is Attached"
   bl_description = "Starts modal timer that checks if debugger attached until attached or until timeout"

   _timer = None
   count = 0
   modal_limit = 20*60

   # call check_done
   def modal(self, context, event):
      self.count = self.count + 1
      if event.type == "TIMER":
         prefs = bpy.context.preferences.addons[__name__].preferences
         return check_done(self.count, self.modal_limit, prefs)
      return {"PASS_THROUGH"}

   def execute(self, context):
      # set initial variables
      self.count = 0
      prefs = bpy.context.preferences.addons[__name__].preferences
      self.modal_limit = prefs.timeout*60

      wm = context.window_manager
      self._timer = wm.event_timer_add(0.1, window=context.window)
      wm.modal_handler_add(self)
      return {"RUNNING_MODAL"}

   def cancel(self, context):
      print("Debugger Confirmation Cancelled")
      wm = context.window_manager
      wm.event_timer_remove(self._timer)

class DebugServerStart(bpy.types.Operator):
   bl_idname = "debug.connect_debugger_vscode"
   bl_label = "Debug: Start Debug Server for VS Code"
   bl_description = "Starts debugpy server for debugger to attach to"

   waitForClient: bpy.props.BoolProperty(default=False)

   def execute(self, context):
      #get debugpy and import if exists
      prefs = bpy.context.preferences.addons[__name__].preferences
      debugpy_path = prefs.path.rstrip("/")
      debugpy_port = prefs.port

      #actually check debugpy is still available
      if debugpy_path == "debugpy not found":
         self.report({"ERROR"}, "Couldn't detect debugpy, please specify the path manually in the addon preferences or reload the addon if you installed debugpy after enabling it.")
         return {"CANCELLED"}

      if not os.path.exists(os.path.abspath(debugpy_path+"/debugpy")):
         self.report({"ERROR"}, "Can't find debugpy at: %r/debugpy." % debugpy_path)
         return {"CANCELLED"}

      if not any(debugpy_path in p for p in sys.path):
         sys.path.append(debugpy_path)

      global debugpy #so we can do check later
      import debugpy

      # can only be attached once, no way to detach (at least not that I understand?)
      try:
         debugpy.listen(("localhost", debugpy_port))
      except:
         print("Server already running.")

      if (self.waitForClient):
         self.report({"INFO"}, "Blender Debugger for VSCode: Awaiting Connection")
         debugpy.wait_for_client()

      # call our confirmation listener
      bpy.ops.debug.check_for_debugger()
      return {"FINISHED"}

classes = (
   DebuggerPreferences,
   DebuggerCheck,
   DebugServerStart,
)
register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
   register()
