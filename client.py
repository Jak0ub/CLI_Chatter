import requests as rq
from functions import crypto, others
import threading, time
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

def send_msg(server,msg,pub_key_room,server_key, nickname_id, private_key):
    msg_enc = crypto.base64_encode(crypto.encrypt(pub_key_room, msg))
    lines = [f"{time.time()}", f"{nickname_id}", f"send_msg", msg_enc.decode()]
    x = send_data(server, server_key, lines)
    response = load_response(x, private_key, server_key, server, nickname_id)
    if response != "OK":
        print("Server-side error while sending message")
        others.quit_all()
    return True

def load_new_msg(server, public_key_room, private_key_room,private_key, server_key, nickname_id, room_password):
    while True:
        try:
            lines = [f"{time.time()}", f"{nickname_id}", "load_msg", "BLOB"]
            x = send_data(server, server_key, lines)
            check_timeout(x.text, server, server_key, nickname_id)
            response = load_response(x, private_key, server_key, server, nickname_id)
        except rq.exceptions.ConnectionError: others.quit_all() #Connection closed, quit
        if response == "X": others.quit_all() #Error msg recieved when data is being deleted. This ensures all threads shut off correctly
        elif response.split("\n")[0].split(": ")[0] == "new_client":
            print(f">> {response.split("\n")[0].split(": ")[1]} joined")
        elif response.split("\n")[0] == "REQ": #New client requested to key exchange
            try:
                other_side_nickname = response.split("\n")[1]
                other_side_key = crypto.retrieve_key((response.split("\n")[2]).encode(), room_password, 0) #Pub key = mode 0
                msg = [(crypto.prepare_key(public_key_room, room_password, 0)).decode(), (crypto.prepare_key(private_key_room, room_password, 1)).decode()]
                blob = crypto.base64_encode(crypto.encrypt(other_side_key, "|".join(msg)))
                lines = [f"{time.time()}", f"{nickname_id}", f"room_respond: {other_side_nickname}", blob.decode()]
                x = send_data(server, server_key, lines)
                print(f">> {other_side_nickname} joined")
                continue
            except: 
                lines = [f"{time.time()}", f"{nickname_id}", f"room_respond: WRONG,{other_side_nickname}", "BLOB"]
                x = send_data(server, server_key, lines)
                continue
        else:
            try:
                sender = response.split("\n")[0]
                x = crypto.base64_decode(response.split("\n")[1])
                response = crypto.decrypt(private_key_room, x)
                response = response.decode("utf-8")
                if response == "/quit":
                    print(f">> {sender} has left the chat")
                else:
                    print(f"{sender}> {response}")                
            except:
                print("WARN> Recieved message was tampered with, possible MITM!")

def mitm_possible(server, server_key, nickname_id):
    print("Server-side error or possible MITM!\nDeleting all logs")
    lines = [f"{time.time()}", f"{nickname_id}", f"QUIT", "BLOB"]
    #Delete all logs
    send_data(server, server_key, lines)
    others.quit()

def send_data(server, server_key, lines):
    if type(lines) == list: lines = "\n".join(lines)
    data_encrypted = crypto.encrypt(server_key, lines)
    return rq.post(f"{server}", data=data_encrypted)

def check_timeout(data, server, server_key, nickname_id):
    if data == "TIMEOUT":
        lines = [f"{time.time()}", f"{nickname_id}", f"QUIT", "BLOB"]
        #Delete all logs
        send_data(server, server_key, lines)
        print("Time exceeded\nLogs cleared")
        others.quit_all()

def load_response(x, private_key, server_key, server, nickname_id):
    try:
        x = crypto.base64_decode(x.text)
        response = crypto.decrypt(private_key, x)
        response = response.decode()
    except: mitm_possible(server, server_key, nickname_id)
    return response

def main():
    clear_cmd = others.os_def()
    private_key, public_key = crypto.generate_keys()
    server = input("Enter the server ip/domain w or w/o a port(ex. https://server.com): ")
    access_code = others.get_safe_input("Enter the server access code: ")
    
    r = rq.get(f"{server}/key.pub")
    server_key = crypto.retrieve_key((r.text), access_code, 0)
    access = False
    hashed_access_code = crypto.hash_text(access_code)

    nickname = input("Enter your desired nickname: ")
    while access == False:
        #Send Unix time, nickname, auth code and pub_key
        lines = [f"{time.time()}", f"{nickname}", f"auth: {hashed_access_code}", (crypto.base64_encode(crypto.key_to_bytes(public_key))).decode()]
        x = send_data(server, server_key, lines)
        response = load_response(x, private_key,server_key, server,0)
        if response == "TAKEN":
            others.clear(clear_cmd)
            nickname = input("Nickname is taken, enter another one: ")
        elif len(response) == 16: #Recieved the Private ID
            nickname_id = response
            access = True

    room_select = True
    private_key_room, public_key_room = crypto.generate_keys()
    others.clear(clear_cmd)
    while room_select:
        #Getting room info
        lines = [f"{time.time()}", f"{nickname_id}", "room_info", "BLOB"]
        x = send_data(server, server_key, lines)
        response = load_response(x, private_key, server_key, server, nickname_id)
        lines = response.split("\n")
        rooms = []
        print("Enter 0 to create a new room, to join in, enter just the room name\nPress Enter to reload all room data\n")
        print("="*len('Enter 0 to create a new room, to join in, enter just the room name'))
        if len(lines) == 0:
            print("No rooms yet...")
        else:
            for line in lines:
                rooms.append(line.split(":")[0])
                print(line)
            
        #Entering room     
        room = input("$~ ")
        if room == "0": #New room
            others.clear(clear_cmd)
            room_name = input("What do you want to name your room? ")
            x = send_data(server, server_key,[f"{time.time()}", f"{nickname_id}", f"room_create: {room_name}", "BLOB"])
            response = load_response(x, private_key, server_key, server, nickname_id)
            if response == "Taken":
                others.clear(clear_cmd)
                print(">> Room name is taken")
                continue
            elif response == "Success":
                room_password = others.get_safe_input("Create your room password: ")
                others.clear(clear_cmd)
                if len("After 120s of inactivity, the room will be closed") > len(f'Welcome to the room |{room_name}|'): num = len("After 120s of inactivity, the room will be closed")
                else: num = len(f'Welcome to the room |{room_name}|')
                print(f"Welcome to the room |{room_name}|\nAfter 120s of inactivity, the room will be closed\nTo quit, enter /quit\nPeers info, enter /details\n{"="*num}")
                room_select = False

        elif room == "": #Reload data
            others.clear(clear_cmd)
            continue

        else: #Room select
            others.clear(clear_cmd)
            room_password = others.get_safe_input("Enter the room password to ensure E2EE even the relay server cant see: ")
            print("waiting for room_owner to respond")
            x = send_data(server, server_key,[f"{time.time()}", f"{nickname_id}", f"room_join: {room}", (crypto.prepare_key(public_key_room, room_password, 0)).decode()])
            check_timeout(x.text, server, server_key, nickname_id)
            response = load_response(x, private_key, server_key, server, nickname_id)
            if response == "Unavailable":
                others.clear(clear_cmd)
                print(">> Selected room does not exist...")
                continue
            elif response == "Wrong":
                others.clear(clear_cmd)
                print(">> Entered room password was wrong")
                continue
            elif response == "BANNED":
                others.clear(clear_cmd)
                print(">> Too many wrong guesses, you were banned.")
                others.quit()
            else:
                try:
                    response = crypto.base64_decode(response)
                    response = crypto.decrypt(private_key_room, response)
                    response = response.decode()
                    public_key_room = response.split("|")[0]
                    private_key_room = response.split("|")[1]
                    public_key_room = crypto.retrieve_key(public_key_room.encode(), room_password, 0)
                    private_key_room = crypto.retrieve_key(private_key_room.encode(), room_password, 1)
                    others.clear(clear_cmd)
                    if len("After 120s of inactivity, the room will be closed") > len(f'Welcome to the room |{room}|'): num = len("After 120s of inactivity, the room will be closed")
                    else: num = len(f'Welcome to the room |{room}|')
                    print(f"Welcome to the room |{room}|\nAfter 120s of inactivity, the room will be closed\nTo quit, enter /quit\nPeers info, enter /details\n{"="*num}")
                    room_select = False
                except:
                    mitm_possible(server, server_key, nickname_id)
    
    session = PromptSession()
    t = threading.Thread(target=load_new_msg, args=(server, public_key_room, private_key_room,private_key, server_key, nickname_id, room_password))
    t.start()#Start recieving msg
    chatting = True
    with patch_stdout():
        while chatting:
            my_msg = session.prompt("> ")
            if my_msg == None: continue
            if my_msg.lower() == "/details":
                x = send_data(server, server_key,[f"{time.time()}", f"{nickname_id}", "room_details", "BLOB"])
                response = load_response(x, private_key, server_key, server, nickname_id)
                print(f">> {response} online")
            else:
                chatting = send_msg(server, my_msg, public_key_room, server_key, nickname_id, private_key)
                if my_msg.lower() == "/quit":
                    lines = [f"{time.time()}", f"{nickname_id}", "QUIT", "BLOB"]
                    x = send_data(server, server_key, lines)
                    response = load_response(x, private_key, server_key, server, nickname_id)
                    if response == "OK": 
                        print("logs deleted!")
                    others.quit_all()

                    
if __name__ == "__main__":
    try:
        main()
    except rq.exceptions.ConnectionError:
        print("Server offline or your IP is banned")