import sys, subprocess
import os, platform
import getpass, time

def quit():
    sys.exit() #Quit program

def os_def(): #Get cli clear cmd for specific system
    platform_system = platform.system()
    if platform_system == "Windows":
        return "cls"
    else:
        return "clear"

def clear(cmd): #clear terminal
    os.system(cmd)

def wait(sec): #wait specified amount of time
    time.sleep(sec)


def check(): #Ensure the server is ran only on Unix systems
    if platform.system() == "Windows":
        print("Only for Unix")
        sys.exit()

def init(): #Prepare the server files&folders + start the server 
    os.system("mkdir hosting && mkdir hosting/viewer")
    os.chdir("hosting/viewer")
    with open("auth.txt", "w") as f: pass
    server = subprocess.Popen(["python3", "-m", "http.server"], stderr=open("../log.txt", "w")) #Start server and redirect stderr stream to log file
    return server

def clean(server): #Clear logs and stop the server
    server.kill()
    os.chdir("../..")
    os.system("rm -rf hosting") #No logs!
    return 1

def get_safe_input(text): #Get safe input from user (input w/o output)
    paswd = getpass.getpass(text)
    return paswd

def info(line): #Get server info about client 
    params = ""
    ip = line.split(" ")[0]
    if len(ip.split(":")) != 1: ip = ip.split(":")[-1]
    if "200" not in line.split(" "): return ip, "" 
    page = line.split(" /")[1].split(" HTTP")[0]
    if len(page.split("?")) != 1: params = page.split("?")[1]
    return ip, params


def save_authorized_ip(ip): #Save specific hashed IP to authorized file available to clients
    with open("auth.txt", "r") as f:
        l = f.readlines()
    l.append(f"{ip}\n")
    with open("auth.txt", "w") as f:
        f.writelines(l)

 
def create_rooms(num_of_rooms): #Create rooms for clients
    rooms = []
    for i in range(num_of_rooms):
        rooms.append(0)
        with open(f"{i+1}.txt", "w") as f: f.write("0")
    return rooms
