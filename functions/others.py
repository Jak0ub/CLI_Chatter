import sys, subprocess
import os, platform
import getpass, time

def os_def():
    platform_system = platform.system()
    if platform_system == "Windows":
        return "cls"
    else:
        return "clear"

def clear(cmd):
    os.system(cmd)

def wait(sec):
    time.sleep(sec)

def cli_clear():
    os.system("clear")

def check():
    if platform.system() == "Windows":
        print("Only for Unix")
        sys.exit()

def init():
    os.system("mkdir hosting && mkdir hosting/viewer")
    os.chdir("hosting/viewer")
    with open("auth.txt", "w") as f: pass
    server = subprocess.Popen(["python3", "-m", "http.server"], stderr=open("../log.txt", "w")) #Start server and redirect stderr stream to log file
    return server

def clean(server):
    server.kill()
    os.chdir("../..")
    os.system("rm -rf hosting") #No logs!
    return 1

def get_safe_input(text):
    paswd = getpass.getpass(text)
    return paswd

def info(line):
    params = ""
    ip = line.split(" ")[0]
    if len(ip.split(":")) != 1: ip = ip.split(":")[-1]
    if "200" not in line.split(" "): return ip, "" 
    page = line.split(" /")[1].split(" HTTP")[0]
    if len(page.split("?")) != 1: params = page.split("?")[1]
    return ip, params


def save_authorized_ip(ip):
    with open("auth.txt", "r") as f:
        l = f.readlines()
    l.append(f"{ip}\n")
    with open("auth.txt", "w") as f:
        f.writelines(l)


def create_rooms(num_of_rooms):
    rooms = []
    for i in range(num_of_rooms):
        rooms.append(0)
        with open(f"{i+1}.txt", "w") as f: f.write("0")
    return rooms
