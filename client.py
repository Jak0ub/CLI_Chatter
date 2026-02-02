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
    clear_cmd = others.os_def()
    msg_mode = 0
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

    others.clear(clear_cmd)
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

        #Entering room     
        room = input("Enter chat room number: ")
        room_enc = crypto.encrypt(server_key, room)
        before = rq.get(f"http://{server}/{room}.txt") 
        rq.get(f"http://{server}/?key={crypto.base64_encode(str(crypto.key_to_bytes(public_key)))}") #Send the pub key
        others.wait(1)
        rq.get(f"http://{server}/?room={crypto.base64_encode(str(room_enc))}") #Send room info
        others.wait(1)
        after = rq.get(f"http://{server}/{room}.txt") 
        if (before.text).splitlines()[0] == "0" or len((after.text).splitlines()) == 1: #If the room is empty
            msg_mode = 1 
            others.clear(clear_cmd)
            print(f"Welcome to chat room {room}\nwaiting for reuqests")
            only_one_in_room = True
            while only_one_in_room:
                others.wait(10)
                r = rq.get(f"http://{server}/{room}.txt")
                if len((r.text).splitlines()) != 1:
                    msg = (r.text).splitlines()[msg_mode]
                    msg = crypto.decrypt(private_key, crypto.str_to_bytes(msg))
                    request = input(f"{msg.decode("utf-8")} is trying to join. Let them in? y/n: ")
                    if request.lower() == "y": only_one_in_room = False
            rq.get(f"http://{server}/?respond={crypto.base64_encode(str(crypto.encrypt(server_key, msg.decode("utf-8"))))}") 
            input()

        elif (before.text).splitlines()[0] == "1":
            before = rq.get(f"http://{server}/{room}.txt") 
            msg_mode = 2
            waiting = True
            others.clear(clear_cmd)
            print("waiting for response")
            while waiting:
                others.wait(10)
                r = rq.get(f"http://{server}/{room}.txt")
                if (r.text).splitlines()[1] != (before.text).splitlines()[1]:
                    try:
                        msg = (r.text).splitlines()[1]
                        msg = crypto.decrypt(private_key, crypto.str_to_bytes(msg))
                    except:
                        print("Rejected")
                        others.quit()
                    if msg.decode("utf-8") == get_public_ip():
                        print(f"Welcome to chat room {room}")
                        waiting = False
        else:
            print("room is full")
            others.quit()




if __name__ == "__main__":
    main()