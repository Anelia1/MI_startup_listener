import subprocess



directory = 'C:\MI_app'
cmdline = "MI_app.exe"
subprocess.call("start cmd /C " + cmdline, cwd=directory, shell=True)


