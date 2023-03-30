import subprocess

cmd_prefix = ["make","-f","../makefile.am"]

subprocess.check_call(cmd_prefix+["clean"],cwd="src")
subprocess.check_call(cmd_prefix+["RELEASE_BUILD=1"],cwd="src")
