import sys, subprocess
import os, platform
import getpass, time
from functions import crypto

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

def init(port): #Prepare the server files&folders + start the server 
    os.system("mkdir hosting && mkdir hosting/viewer")
    os.chdir("hosting/viewer")
    with open("auth.txt", "w") as f: pass
    server = subprocess.Popen(["python3", "-m", "http.server", str(port)], stderr=open("../log.txt", "w")) #Start server and redirect stderr stream to log file
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

def remove_ip_from_authorized(ip): #Remove ip from auth logs
    with open("auth.txt", "r") as f:
        l = f.readlines()
    for line in l:
        if crypto.hash_text(ip) == line.strip():
            l.pop(l.index(line))
    with open("auth.txt", "w") as f:
        f.writelines(l)

 
def create_rooms(num_of_rooms): #Create rooms for clients
    rooms = []
    for i in range(num_of_rooms):
        rooms.append(0)
        with open(f"{i+1}.txt", "w") as f: f.write("0")
    return rooms

def create_room_share(room_num,key1,key2): #Create dir for pub key exchange
    os.system(f"mkdir {room_num}")
    wait(0.1)
    os.chdir(f"{room_num}")
    crypto.save_pub_key(key1,"1")
    crypto.save_pub_key(key2,"2")
    wait(0.1)
    os.chdir("..")

def get_other_side(ip_to_room, ip):
     for val in ip_to_room:
        if ip_to_room[val] == ip_to_room[ip] and val != ip: #In same chat room but not the same IP
            return val
        
def clean_room(room_num, ip1, ip2, communicating_ip, ip_to_room, ip_to_key, keys, rooms, Addresses, access_granted): #Remove all logs about clients
    #Remove room details
    os.chdir(f"{room_num}") #Do it safely. No need for rm -rf
    for i in range(2):
        os.remove(f"{i+1}.pub")
    os.chdir("..")
    wait(0.1)
    os.system(f"rmdir {room_num}")
    with open(f"{room_num}.txt", "w") as f: f.write("0")
    #Delete all logs in RAM
    for i in range(2):
        if i == 0: remove_ip = ip1
        else: remove_ip = ip2
        communicating_ip.pop(communicating_ip.index(remove_ip))
        ip_to_room.pop(remove_ip)
        ip_to_key.pop(remove_ip)
        access_granted.pop(access_granted.index(remove_ip))
        remove_ip_from_authorized(remove_ip)
    for val in keys:
        if val[0] == ip1 or val[0] == ip2:
            keys.pop(keys.index(val))
    for val in Addresses:
        if val[0] == ip1 or val[0] == ip2:
            Addresses.pop(Addresses.index(val))
    rooms[room_num-1] = 0
    return communicating_ip, ip_to_room, ip_to_key, keys, rooms, Addresses, access_granted

def quitting(clear_cmd):
    clear(clear_cmd)
    print("This chat room is closing after /quit usage.")
    wait(3)
    print("All logs will be deleted and your program will be stopped in few seconds.")
    wait(5)
    quit_all()

def quit_all():
    os._exit(0)

def write_report(Addr, banned_ip):
    if banned_ip != []:
        lines = ["Logged IP addresses flagged as potential DDOS threat\n", "If needed, use ufw to block them for good\n", "\n"]
        for ip in banned_ip:
            for address in Addr:
                if address[0] == ip:
                    lines.append(f"{address[0]} -> {address[1]}x packets\n")
        with open("../../report.txt", "w") as f: f.writelines(lines)
    