import sys
import os, platform
import getpass

def quit():
    sys.exit() #Quit program

def quit_all():
    os._exit(0)

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
        
def delete_logs(room_name, client_ip, nickname, Addresses, ip_clients, client_queues, communicating_nickname, nickname_to_room, nickname_to_key, access_granted, rooms, rooms_waiting, nickname_to_id, room_leaders, nickname_room_attempts, last_time_online):
    if ip_clients[client_ip] == 1: #Only client of this ip? Remove access
        if client_ip in Addresses: Addresses.pop(client_ip)
        if client_ip in access_granted: access_granted.pop(access_granted.index(client_ip))
        ip_clients.pop(client_ip)
    elif ip_clients[client_ip] > 1:
        ip_clients[client_ip] -= 1
    for var in [communicating_nickname, nickname_to_room, nickname_to_key,client_queues, rooms_waiting, nickname_to_id, nickname_room_attempts, last_time_online]:
        while nickname in var:
            if type(var) == list:   var.pop(var.index(nickname))
            elif type(var) == dict: var.pop(nickname)
    if room_name != 0: 
        if rooms[room_name] > 1:
            if room_name in room_leaders:
                if room_leaders[room_name] == nickname: #Assign new room leader
                    for k, v in (nickname_to_room).items():
                        if v == room_name and k != nickname:
                            room_leaders[room_name] =  k
            rooms[room_name] -= 1
        else:
            room_leaders.pop(room_name)
            rooms.pop(room_name)

    return Addresses, ip_clients, client_queues, communicating_nickname, nickname_to_room, nickname_to_key, access_granted, rooms, rooms_waiting, nickname_to_id, room_leaders, nickname_room_attempts, last_time_online

def write_report(Addr, banned_ip):
    if banned_ip != []:
        lines = ["Logged IP addresses flagged as potential DDOS threat\n", "Integrate with fail2ban\n", "\n"]
        for ip in banned_ip:
            if ip in Addr:
                lines.append(f"{ip} -> {Addr[ip]}x packets\n")
        with open("../report.txt", "w") as f: f.writelines(lines)

def get_env():#Only for docker
    #_ at the end just in case 
    try: access_code = os.getenv("server_access_code_")
    except: access_code = None
    try: 
        ddos_protection = os.getenv("server_packet_limit")
        ddos_protection = int(ddos_protection)
        if ddos_protection > 30: ddos_protection = 30 #More than 30 packet limit is not the best practice
    except: ddos_protection = 10 #Not using docker? Edit this number to customize the packet limit
    return access_code, ddos_protection

