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

def send_msg(server,msg,other_side_key):
    msg_enc = crypto.base64_encode(crypto.encrypt(other_side_key, msg))
    x = rq.post(f"{server}/data", data=msg_enc) #Send message
    if (x.text).split("\n")[0] != "OK":
        print("Server-side error while sending message")
        others.quit_all()
    return True

def load_new_msg(server, room, other_side_ip, private_key,server_key,data_deleted):
    while True:
        data_encrypted = crypto.encrypt(server_key, room)
        try:
            x = rq.post(f"{server}/data", data=data_encrypted)
        except rq.exceptions.ConnectionError: others.quit_all() #Connection closed, quit
        if x.text == "X": others.quit_all() #Error msg recieved when data is being deleted. This ensures all threads shut off correctly
        check_timeout(x)
        try:
            msg = crypto.decrypt(private_key, crypto.base64_decode(x.text))
            print(f"{other_side_ip}> {msg.decode("utf-8")}")
            if msg.decode("utf-8").lower() == "/quit": #Recieved /quit
                data_encrypted = crypto.encrypt(server_key, f"quit: {room}")
                if data_deleted == False: #Request data deletion once
                    data_deleted = True
                    x = rq.post(f"{server}/quit", data=data_encrypted)
                others.quit_all()
        except:
            print("WARN> Recieved message was tampered with, possible MITM!")

def mitm_possible(room, server, server_key):
    print("Wrong room password, or possible MITM!\nDeleting all logs")
    lines = f"quit: {room}"
    #Delete all logs
    data_encrypted = crypto.encrypt(server_key, lines)
    rq.post(f"{server}/quit", data=data_encrypted)
    others.quit()

def send_data(server, server_key, lines):
    if type(lines) == list: lines = "\n".join(lines)
    data_encrypted = crypto.encrypt(server_key, lines)
    return rq.post(f"{server}/data", data=data_encrypted)

def check_timeout(x):
    if (x.text) == "TIMEOUT":
        print("Time exceeded\nLogs cleared")
        others.quit()

def main():
    key_room_sent = False
    clear_cmd = others.os_def()
    protocol = "http://" #Change if server is https
    server = input("Enter the server ip with port(default port 80): ")
    server = f"{protocol}{server}"
    access_code = others.get_safe_input("Enter the server access code: ")

    r = rq.get(f"{server}/key.pub")
    server_key = crypto.retrieve_key((r.text), access_code)
    access = False

    access_code_secure = f"{access_code}{get_public_ip()}"
    hashed_access_code = crypto.hash_text(access_code_secure)
    lines = [f"auth: {hashed_access_code}"]
    x = send_data(server, server_key, lines)
    if (x.text).split("\n")[0] == "AUTH OK": 
        access = True
        
    others.clear(clear_cmd)
    if access == True:
        #Generating own keys and getting server public key for E2EE
        private_key, public_key = crypto.generate_keys()
        x = crypto.send_key(f"{server}/key", public_key,access_code)
        other_side_response = ""
        while other_side_response != "y" or other_side_response != "start"  or key_room_sent == False:
            if key_room_sent == True: break
            #Getting room info
            others.clear(clear_cmd)
            crypto.get_room_info(server,private_key) #Crypto function too

            #Entering room     
            room = input("Enter chat room number: ")

            others.clear(clear_cmd)
            print("waiting for response(max 1min.)\nThis includes other clients, may take longer...")
            x = send_data(server, server_key, [f"room: {room}"])
            check_timeout(x)
            x_temp = crypto.base64_decode(x.text)
            other_side_response = crypto.decrypt(private_key, x_temp)
            other_side_response = other_side_response.decode()
            if other_side_response.split(",")[0] == "y":
                other_side_ip = other_side_response.split(",")[1]
                others.clear(clear_cmd)
                print(f"{other_side_ip} accepted!\ntype /quit to quit w/o errors\n\nwaiting for host to enter room password...")
                x = send_data(server, server_key, [f"room: {room}", "start"])
                others.clear(clear_cmd)
                print(f"{other_side_ip} joined!\ntype /quit to quit w/o errors\n\n")
                check_timeout(x)
                break
            elif other_side_response == "n":
                input("rejected")
                continue
            other_side_response = ""
            while other_side_response != "start":
                if key_room_sent == True: break
                x = crypto.base64_decode(x.text)
                other_side_ip = crypto.decrypt(private_key, x)
                other_side_ip = other_side_ip.decode()
                request = input(f"{other_side_ip} is trying to join. Let them in? y/n: ")
                if request.lower() == "y":
                    x = send_data(server, server_key, [f"room: {room}", f"{other_side_ip}: y"])
                    check_timeout(x)
                    x_temp = crypto.base64_decode(x.text)
                    other_side_response = crypto.decrypt(private_key, x_temp)
                    other_side_response = other_side_response.decode()
                    if other_side_response == "start":
                        others.clear(clear_cmd)
                        print(f"{other_side_ip} joined!\ntype /quit to quit w/o errors\n\n")
                        room_password = others.get_safe_input("Enter the room password which is used to E2EE(even untrusted server cant do anything): ")
                        private_key_room, public_key_room = crypto.generate_keys()
                        x = crypto.send_key(f"{server}/key", public_key_room,room_password)
                        check_timeout(x)
                        others.clear(clear_cmd)
                        try:
                            other_side_key = crypto.retrieve_key((x.text), room_password)
                        except:
                            mitm_possible(room, server, server_key)
                        key_room_sent = True
                        continue
                else:
                    others.clear(clear_cmd)
                    print("waiting for someone else")
                    x = send_data(server, server_key, [f"room: {room}", f"{other_side_ip}: n"])
                    check_timeout(x)

        if key_room_sent == False:
            room_password = others.get_safe_input("Enter the room password which is used to E2EE(even untrusted server cant do nothing): ")
            private_key_room, public_key_room = crypto.generate_keys()
            try:
                other_side_key = crypto.retrieve_key((x.text), room_password)
            except:
                x = crypto.send_key(f"{server}/key", public_key_room,room_password)
                mitm_possible(room, server, server_key)
            x = crypto.send_key(f"{server}/key", public_key_room,room_password)
            check_timeout(x)

        others.clear(clear_cmd)
        print(f"{other_side_ip} joined!\ntype /quit to quit w/o errors\nAfter 1min of inactivity, the chat is automatically closed\n")
        #Start threading
        session = PromptSession()
        t = threading.Thread(target=load_new_msg, args=(server, room, other_side_ip, private_key_room,server_key,False))
        t.start()#Start recieving msg
        #Joined chat room, the communication begins
        chatting = True
        with patch_stdout():
            while chatting:
                my_msg = session.prompt("> ")
                if my_msg == None: continue
                chatting = send_msg(server,my_msg,other_side_key)
                if my_msg.lower() == "/quit":
                    lines = f"quit: {room}"
                    data_encrypted = crypto.encrypt(server_key, lines)
                    rq.post(f"{server}/quit", data=data_encrypted)
                    if (x.text).split("\n")[0] == "OK": 
                        print("logs deleted!")
                    others.quit_all()
                    
if __name__ == "__main__":
    try:
        main()
    except rq.exceptions.ConnectionError:
        print("Server offline or your IP is banned")