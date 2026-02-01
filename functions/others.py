import sys, subprocess
import os, platform
import getpass

def cli_clear():
    os.system("clear")

def check():
    if platform.system() == "Windows":
        print("Only for Unix")
        sys.exit()

def init():
    os.system("mkdir hosting && mkdir hosting/viewer")
    os.chdir("hosting/viewer")
    server = subprocess.Popen(["python3", "-m", "http.server"], stderr=open("../log.txt", "w")) #Start server and redirect stderr stream to log file
    return server

def clean(server):
    server.kill()
    os.chdir("../..")
    os.system("rm -rf hosting") #No logs!
    return 1

def create_passwd():
    paswd = getpass.getpass("Create password for server access: ")
    return paswd

def info(line):
    params = ""
    ip = line.split(" ")[0]
    if "200" not in line.split(" "): return ip, "" 
    page = line.split(" /")[1].split(" HTTP")[0]
    if len(page.split("?")) != 1: params = page.split("?")[1]
    return ip, params