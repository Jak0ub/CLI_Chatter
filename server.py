import sys, subprocess
from hashlib import sha256
import os, platform, time


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
    os.chdir("..")
    os.system("rm -rf hosting") #No logs!
    return 1

def create_passwd():
    paswd = input("Create password for server access: ")
    return sha256(paswd.encode('utf-8')).hexdigest()

def info(line):
    params = ""
    ip = line.split(" ")[0]
    if "200" not in line.split(" "): return ip, "" 
    page = line.split(" /")[1].split(" HTTP")[0]
    if len(page.split("?")) != 1: params = page.split("?")[1]
    return ip, params


def main():
    check()
    server = init()
    time.sleep(1) #Ensure clear terminal
    cli_clear()
    access_code = create_passwd()
    os.chdir("..")

    ddos_protection = 30 #If one IP exceed this number of packets. The server shuts down this IP
    resolved = 0 #Number of requests resolved already
    access_granted = []
    Addresses = []
    banned_ip = []
    while True:
        time.sleep(0.1)
        with open("log.txt", "r") as f: lines = f.readlines()
        lines = lines[(resolved):]#exclude the lines already resolved
        for line in lines:
            ip, params = info(line)
            if ip in banned_ip: continue
            #Packet counter. DDOS PROTECTION
            if ip not in access_granted:
                if len(Addresses) == 0: Addresses.append([ip, 0])
                for adr in Addresses:
                    if adr[0] == ip: 
                        Addresses[Addresses.index(adr)][1] += 1
                        if Addresses[Addresses.index(adr)][1] >= ddos_protection: banned_ip.append(ip)
                        break
                    elif adr[0] != ip and Addresses.index(adr) == len(Addresses): Addresses.append([ip, 0]) 
            #Access solution
            if params != "":
                if params.split("=")[0].lower() == "code" and params.split("=")[1] == access_code: access_granted.append(ip)

        resolved += len(lines)




        if len(banned_ip) != 0 or len(access_granted) != 0: break #For testing ONLY

    if clean(server) == 1:
        print("server stopped successfully")
    else:
        print("error occured")

if __name__ == "__main__":
    main()

