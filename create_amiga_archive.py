import subprocess,zipfile,os

# JOTD path for cranker :)
os.environ["PATH"] += os.pathsep+r"K:\progs\cli"

cmd_prefix = ["make","-f","../makefile.am"]

subprocess.check_call(cmd_prefix+["clean"],cwd="src")
# RELEASE_BUILD=1 turns off all logs & screen flashes
subprocess.check_call(cmd_prefix+["RELEASE_BUILD=1"],cwd="src")
# create archive
with zipfile.ZipFile("Xevious1200_HD.zip","w",compression=zipfile.ZIP_DEFLATED) as zf:
    for file in ["readme.md","instructions.txt","xevious","xevious.slave","Xevious.info"]:
        zf.write(file)

subprocess.check_output(["cranker_windows.exe","-f","xevious","-o","xevious.rnc"])