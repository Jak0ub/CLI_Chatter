import requests as rq
from functions import crypto, others
import re as r #RegEx lib
from urllib.request import urlopen

def get_public_ip():
    data = str(urlopen('http://checkip.dyndns.com/').read())
    ip = r.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(data).group(1)
    return "127.0.0.1"
    #return ip

def check_access(server):
    #Check if access was granted
    r = rq.get(f"http://{server}/auth.txt")
    for line in (r.text).splitlines():
        if line.strip() == crypto.hash_text(get_public_ip()): return True
    return False

def main():
    server = input("Enter the server ip with port(default port 80): ")
    access = check_access(server) #If access granted, than skip following if statement
    if access != True: 
        access_code = others.get_safe_input("Enter the server access code: ")
        #Send the server Access_code+YourPublicIP hashed so noone can replicate your request with sucess
        access_code = f"{access_code}{get_public_ip()}"
        hashed_access_code = crypto.hash_text(access_code)
        rq.get(f"http://{server}/?code={hashed_access_code}")
        others.wait(1)
        access = check_access(server)
    if access == True:
        #Generating own keys and getting server public key for E2EE
        private_key, public_key = crypto.generate_keys()
        r = rq.get(f"http://{server}/key.pub")
        server_key = crypto.load_pub_key((r.text).encode("utf-8"))
        #Getting room info
        rooms = []
        while r.status_code == 200:
            r = rq.get(f"http://{server}/{len(rooms)+1}.txt")
            rooms.append(r.text)
        rooms.pop(-1)#Delete the 404 page
        count_of_rooms = 0
        for room in rooms:
            count_of_rooms += 1
            if room == "":
                print(f"{count_of_rooms}. room -> 0/2 online")
            else:
                print(f"{count_of_rooms}. room -> {room.splitlines()[0]}/2 online")
        room = input("Enter chat room number: ")
        room_enc = crypto.encrypt(server_key, room)
        rq.get(f"http://{server}/?room={crypto.base64_encode(str(room_enc))}")



if __name__ == "__main__":
    main()