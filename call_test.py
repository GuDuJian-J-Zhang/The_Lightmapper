import subprocess

if __name__=="__main__":
   baking = True

   pipe = subprocess.Popen([
    "C:/Program Files/Blender Foundation/Blender 3.3/blender.exe", 
    "--background",
    "--python", 'C:/BlenderStuff/addons/The_Lightmapper/test.py'
    ], 
    shell=True, 
    stdout=subprocess.PIPE)

   stdout = pipe.communicate()[0]

   print(stdout)

   print("Baking finished...")

   active = False
