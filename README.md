# Blender Debugger for VS Code

Inspired by [Blender-VScode-Debugger](https://github.com/Barbarbarbarian/Blender-VScode-Debugger) which was itself inspired by this [remote_debugger](https://github.com/sybrenstuvel/random-blender-addons/blob/master/remote_debugger.py) for pycharm as explained in this [Blender Developer's Blog post](https://code.blender.org/2015/10/debugging-python-code-with-pycharm/). 


Since the VS Code one wasn't really well documented and it looked kind of dead, once I figured it out, I was just going to add the documentation, but then I ended up rewriting the whole thing.

Now it can:

- Auto-detect where python is and auto set the path to ptvsd if installed.
- Tell you when the debugger has actually attached.

![Image Showing VS Code side by side with Blender paused at a breakpoint. In the console, a "Debugger is Attached" Statement is printed.](./Example.png)

# How to Use

I have made a video (click the image below) for those who just started messing with python in Blender or programming in general, but if you're semi-familiar with Python, VS Code, and the command line the following should make sense. If you have any questions or suggestions, don't hesitate to file an issue.

<p align="center" style="position:relative;">
   <a href="https://www.youtube.com/watch?v=UVDf2VSmRvk" title="Click to go to Video">
      <img alt="youtube video" src="https://img.youtube.com/vi/UVDf2VSmRvk/maxresdefault.jpg" height="300" style="margin:0 auto;" />
   </a>
</p>


## Installing Python and Getting PTVSD

Install Python 3 with pip and check add to PATH.
   - If you already have python installed and you can run it from the command line (aka PATH is set), the addon should find it. It uses `where python` or `whereis python` or `which python` depending on the OS to determine where python is. I only have windows at the moment, so only that is tested, but it should work. On macOS this is `/usr/local/lib/python3.6/site-packages/` if you use the command below.

`pip install ptvsd==3.0.0`
   - Newer versions do not work, you will just get an error in VS Code trying to connect. later versions aren't supported yet see [Debugging Python with VS Code](https://code.visualstudio.com/docs/python/debugging#_remote-debugging) and [#514](/Microsoft/vscode-python/issues/514).

## Setting up your Addon

This is the most important part. Otherwise it won't work. I thought it was my VS Code config but no, it was this.

In Blender go to: `User Preferences > File` and set the path to `Scripts` to the folder you're developing your addon in (e.g: "C:\Code\Blender Stuff") BUT the folder must look like this:

```
Blender Stuff
└── addons
   ├── your-addon-folder
      ├── __init__.py
      ├── ...etc
   ├── another-addon
   ├── ...
```

Now remove your addon from Blender if it was installed, save settings, and when you restart your addon should be installed automatically.

## Setting up this Addon

Install the addon.

If it did not find the path it'll say "PTVSD not Found", you'll have to set it manually. It's wherever python is + "\lib\site-packages". NO trailing backslash.

If you want, increase the timeout for the confirmation. It'll print "Waiting..." in the console every second until it prints it's timedout. This does not mean the server has timedout *just* the confirmation listener.

Open up Blender's search (default shortcut: space), type "Debug".

Click `Debug: Start Debug Server for VS Code`. Note: you can only start the server once. You cannot stop it, at least from what I understand. If you run it again it'll just tell you it's already running and start the timer again to check for a confirmation.

## Connecting VS Code

Open your addon folder (e.g. "C:\Code\Blender Stuff\addons\myaddon").

Install the Python extension for VS Code if you haven't already.

Go to the Debugging tab and add a configuration. Pick Python. You'll want the configuration that looks like this, you can delete the rest. There's no need to change the defaults. 

```JSON
   {
      "name": "Python: Attach",
      "type": "python",
      "request": "attach",
      "localRoot": "${workspaceFolder}",
      "remoteRoot": "${workspaceFolder}",
      "port": 3000,
      "secret": "my_secret",
      "host": "localhost"
   },
```

Now when you run the debugger with this config in Blender and VS Code the console should print "Debugger is Attached" if it was still waiting (it should still attach even if it wasn't, it just won't tell you).

## How to Use

At this point you should be able to add a breakpoint and when you trigger it in Blender, Blender should freeze and VS Code should pause on the breakpoint.

Note though that if you make changes to the file, Blender will not detect them. Have open `User Preferences > Addons` so you can toggle your addon on and off when you make changes. If anyone knows any way to improve this I'd love to know.

### Editing Source Code

It is possible to edit the Blender source code but it can be a bit tricky to get it to detect changes (nevermind live editing is buggy anyways).

From blender you can right click just about anything and click "Edit Source" to get it in the text editor. Then to find the path of the file, go to `Text > Save As` and copy it from there.

Open the file in VS Code, connect to the debugging server, make a change and save it.

Now in Blender the text editor will show this little red button in the top left. Click that and reload the file. Then in `Text Editor > Properties` turn on `Live Edit` if you haven't already. Now to actually get Blender to detect any changes you made just type a single character (like add a space anywhere) and *then* it will detect your changes.

# Notes

The addon also detects python if PYTHONPATH is set (because Blender will add it to sys.path) or if you used the Python bundled with Blender to install ptvsd (but that's a bit of a pain because it doesn't have pip installed unless you want to install it manually).
