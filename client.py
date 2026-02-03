import requests as rq
from functions import crypto, others
import re as r #RegEx lib
from urllib.request import urlopen
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

def get_public_ip():
    data = str(urlopen('http://checkip.dyndns.com/').read())
    ip = r.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(data).group(1)
    return ip

def check_access(server):
    #Check if access was granted
    r = rq.get(f"http://{server}/auth.txt")
    for line in (r.text).splitlines():
        if line.strip() == crypto.hash_text(get_public_ip()): return True
    return False

def animate_text(msg, clear_cmd, state):
    others.clear(clear_cmd)
    print(f"{msg}{state*"."}")
    if state==3: state=0
    else: state += 1
    return state

def send_msg(server,msg,server_key):
    rq.get(f"http://{server}/?msg={crypto.base64_encode(str(crypto.encrypt(server_key, msg)))}") #Send message

def load_new_msg(server, room, msg_mode, other_side_ip, private_key, clear_cmd):
    last_msg = ""
    msg = ""
    while True:
        others.wait(1)
        r = rq.get(f"http://{server}/{room}.txt")
        if len((r.text).splitlines()) != 3: continue #Aviod errors
        if (r.text).splitlines()[msg_mode] != last_msg: #New msg at my line
            try:
                msg = (r.text).splitlines()[msg_mode]
                if msg == last_msg: continue #Double check
                last_msg = msg
                msg = crypto.decrypt(private_key, crypto.str_to_bytes(msg))
                print(f"{other_side_ip}> {msg.decode("utf-8")}")
            except: print(f" >>Error decrypting msg from {other_side_ip}"); continue
            if msg.decode("utf-8").lower() == "/quit": #Recieved /quit
                print("Other side has left the chat. Use /quit to delete all logs")
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

        #Show all rooms
        for room in rooms:
            count_of_rooms += 1
            print(f"{count_of_rooms}. room -> {room.splitlines()[0]}/2 online")

        #Entering room     
        room = input("Enter chat room number: ")
        room_enc = crypto.encrypt(server_key, room)
        before = rq.get(f"http://{server}/{room}.txt") #Get room details
        rq.get(f"http://{server}/?key={crypto.base64_encode(str(crypto.key_to_bytes(public_key)))}") #Send the pub key
        others.wait(1)
        rq.get(f"http://{server}/?room={crypto.base64_encode(str(room_enc))}") #Send room info
        others.wait(1)
        after = rq.get(f"http://{server}/{room}.txt") #Get room details

        #Empty room
        if (before.text).splitlines()[0] == "0" or len((after.text).splitlines()) == 1:
            msg_mode = 1 
            only_one_in_room = True
            state = 0
            others.clear(clear_cmd)
            ip_asked = []
            while only_one_in_room:
                state = animate_text("Waiting for requests", clear_cmd, state)
                others.wait(2)
                r = rq.get(f"http://{server}/{room}.txt")
                if len((r.text).splitlines()) != 1:
                    msg = (r.text).splitlines()[msg_mode]
                    msg = crypto.decrypt(private_key, crypto.str_to_bytes(msg))
                    other_side_ip = msg.decode("utf-8")
                    if other_side_ip in ip_asked: continue #We've denied this IP
                    ip_asked.append(other_side_ip)
                    request = input(f"{other_side_ip} is trying to join. Let them in? y/n: ")
                    if request.lower() == "y": only_one_in_room = False
            waiting = True
            rq.get(f"http://{server}/?respond={crypto.base64_encode(str(crypto.encrypt(server_key, other_side_ip)))}")  #Accept the ip
            while waiting:
                others.wait(10)
                state = animate_text("Waiting for response", clear_cmd, state)
                r = rq.get(f"http://{server}/{room}.txt")
                if (r.text).splitlines()[0] == "2":
                    waiting = False
                    others.clear(clear_cmd)
                    print(f"{msg.decode("utf-8")} joined\ntype /quit to quit w/o errors\n\n")
        #Someone is already in the room. Ask them for approval
        elif (before.text).splitlines()[0] == "1":
            before = rq.get(f"http://{server}/{room}.txt") 
            msg_mode = 2
            waiting = True
            state = 0
            other_side_ip = "Unknown ip"
            others.clear(clear_cmd)
            while waiting:
                state = animate_text("Waiting for response", clear_cmd, state)
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
                        r = rq.get(f"http://{server}/?start=blank")
                        others.clear(clear_cmd)
                        print(f"Welcome to chat room {room}\ntype /quit to quit w/o errors\n\n")
                        waiting = False
        #Room is full
        else:
            print("room is full")
            others.quit()
        others.wait(1)#Wait for server to save pub keys
        r = rq.get(f"http://{server}/{room}/{msg_mode}.pub")
        other_side_key = crypto.load_pub_key((r.text).encode("utf-8"))
        #Start threading
        session = PromptSession()
        t = threading.Thread(target=load_new_msg, args=(server, room, msg_mode, other_side_ip, private_key, clear_cmd))
        t.start()#Start recieving msg
        #Joined chat room, the communication begins
        chatting = True
        with patch_stdout():
            while chatting:
                my_msg = session.prompt("> ")
                if my_msg == None: continue
                send_msg(server,my_msg,other_side_key)
                if my_msg.lower() == "/quit":
                    others.wait(3)#Wait few seconds to ensure other side got our /quit msg
                    r = rq.get(f"http://{server}/?quit=blank")
                    others.quitting(clear_cmd) #Notify users about /quit command usage. Log off everyone to ensure new key generation for future chatting

if __name__ == "__main__":
    main()