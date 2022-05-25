# addon version 2.0.0 +
import debugpy

debugpy.listen(("0.0.0.0", 5678))
print("debugpy version is: " + debugpy.__version__)
print("Waiting")
debugpy.wait_for_client()
print("Connected")
input('Press Enter to Exit')
