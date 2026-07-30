import sys
import os, platform
import getpass

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

def check(): #Ensure the server is ran only on Unix systems
    if platform.system() == "Windows":
        print("Only for Unix")
        sys.exit()

def get_safe_input(text): #Get safe input from user (input w/o output)
    paswd = getpass.getpass(text)
    return paswd
        
def clean_room(room_num, ip1, ip2, communicating_ip, ip_to_room, ip_to_key, keys, rooms, Addresses, access_granted, waiting_for_start, waiting_for_room, waiting_for_key, approved): #Remove all logs about clients
    #Delete all logs in RAM
    for remove_ip in [ip1, ip2]:
        if remove_ip in Addresses: Addresses.pop(remove_ip)
        for var in [communicating_ip, ip_to_room, ip_to_key, access_granted, waiting_for_start, waiting_for_room, waiting_for_key,approved,keys]:
            if remove_ip in var:
                if type(var) == list:   var.pop(var.index(remove_ip))
                elif type(var) == dict: var.pop(remove_ip)
        if remove_ip == ip2: break #Possible for removing details only for one ip in a room
    if room_num > 0: rooms[room_num-1] = 0
    return communicating_ip, ip_to_room, ip_to_key, keys, rooms, Addresses, access_granted, waiting_for_start, waiting_for_room, waiting_for_key, approved

def quit_all():
    os._exit(0)

def write_report(Addr, banned_ip):
    if banned_ip != []:
        lines = ["Logged IP addresses flagged as potential DDOS threat\n", "Integrate with fail2ban\n", "\n"]
        for ip in banned_ip:
            if ip in Addr:
                lines.append(f"{ip} -> {Addr[ip]}x packets\n")
        with open("../report.txt", "w") as f: f.writelines(lines)

def get_env():#Only for docker
    #_ at the end just in case 
    try: 
        rooms_count = os.getenv("server_rooms_")
        rooms_count = int(rooms_count)
        if rooms_count > 100: rooms_count = None #More than 100 rooms for docker is overkill
    except: rooms_count = None
    try: access_code = os.getenv("server_access_code_")
    except: access_code = None
    try: 
        ddos_protection = os.getenv("server_packet_limit")
        ddos_protection = int(ddos_protection)
        if ddos_protection > 30: ddos_protection = 30 #More than 30 packet limit is not the best practice
    except: ddos_protection = 10 #Not using docker? Edit this number to customize the packet limit
    return rooms_count, access_code, ddos_protection

