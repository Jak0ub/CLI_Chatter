from functions import crypto, others
import os, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import queue, time, random

LOCK = threading.Lock()
message_queue = queue.Queue()

class ThreadedHandler(SimpleHTTPRequestHandler):
    #Creating needed files outside of current dir to avoid any files leakage
    os.system("mkdir hosting")
    os.chdir("hosting")
    access_code, ddos_protection = others.get_env()
    private_key, public_key = crypto.generate_keys()
    if access_code == None: access_code = others.get_safe_input("Create password for server access: ")
    crypto.save_pub_key(public_key, "key", access_code)
    rooms = {} # room_name: num_of_clients
    room_leaders = {} #room_name: nickname
    client_queues = {} ###
    access_granted = [] ###
    Addresses = {} ###
    banned_ip = [] ###
    nickname_to_id = {} #admin: a3d3....
    ip_clients = {} #127.0.0.1: 1
    communicating_nickname = []
    nickname_to_room = {} #Which ip is in which room
    nickname_to_key = {} # {admin: key} means we have key for admin username
    rooms_waiting = {} #{nickname: room}
    nickname_room_attempts = {} #NICKNAME: ATT
    last_time_online = {} #nickname: TIMESTAMP

    time_between_reports = 60 #How much seconds does the program wait till it writes report
    start_time = time.time()
    TTL_value = 5 #5seconds by default to let the packet live
    timeout_val = 120
    TTL_nickname = timeout_val*2 #Time after which the nickname is marked as free again, if the original owner didnt make a request in TLL_nickname amount of time

    def _notify(self,client_id,body,mode):
        q = self._get_queue(client_id)
        if mode == 1: #Normal handshake mode
            body = crypto.base64_encode(body)
        q.put(body)

    def _get_queue(self, client_id):
        if client_id not in self.client_queues:
            self.client_queues[client_id] = queue.Queue()
        return self.client_queues[client_id]

    def _handle_wait(self, client_id):
        with LOCK:
            q = self._get_queue(client_id)
        try:
            data = q.get(timeout=self.timeout_val)
            self.respond(200, data,True)
        except queue.Empty:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"TIMEOUT")

    def respond(self, code, msg,handler):
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        if handler == False: #Not called through handler, parse normally
            if msg == "X":
                msg = msg.encode()
            else:
                msg = crypto.base64_encode(msg)
                
        self.wfile.write(msg)

    def log_info(self, client_ip):
        if client_ip not in self.Addresses and client_ip not in self.access_granted: (self.Addresses).update({client_ip: 1}) #First ever request
        elif client_ip not in self.access_granted:
            self.Addresses[client_ip] += 1
            if self.Addresses[client_ip] >= self.ddos_protection and client_ip not in self.banned_ip:
                (self.banned_ip).append(client_ip)

    def generate_id(self, nickname):
        characters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        numbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
        while True:
            client_generated_id = []
            for i in range(16):
                if random.choice([0,1]) == 0: #Character
                    if random.choice([0,1]) == 0: #Upper
                        client_generated_id.append((random.choice(characters)).upper())
                    else:#Lower
                        client_generated_id.append(random.choice(characters))
                else:
                    client_generated_id.append(random.choice(numbers))
            client_id = "".join(client_generated_id)
            if self.id_to_nickname(client_id) == False:
                (self.nickname_to_id).update({nickname: client_id})
                return client_id

    def check_time(self, user_time):
        if time.time() - float(user_time) > self.TTL_value: #Max 5s. Time is set as unix timestamp, so timezones aren't a problem.
            return False
        return True

    def check_nickname(self, nickname):
        if nickname not in self.nickname_to_id: #Nickname was not yet assigned
            return True
        return False

    def id_to_nickname(self,client_id):
        reverse = {v: k for k, v in (self.nickname_to_id).items()}
        if client_id in reverse:
            return reverse[client_id]
        return False

    def check_access(self, client_ip, data, nickname):
        if client_ip not in self.banned_ip:
            #Access solution
            hashed_access_code = crypto.hash_text(self.access_code)
            if data.split(": ")[0] == "auth":
                if data.split(": ")[1] == hashed_access_code:
                    if nickname in self.nickname_to_room: #Nickname is free, but it has logged data
                        self.remove_logs(client_ip, nickname) #Restart variables for this nickname
                    if client_ip not in self.access_granted: (self.access_granted).append(client_ip)
                    (self.nickname_to_room).update({nickname: 0}) #Default room 0
                    return True
        return False

    def remove_logs(self, client_ip, nickname): #Remove all logs and queues
        #Get needed info about both sides
        try:
            room_name = self.nickname_to_room[nickname]
        except KeyError:
            room_name = 0
        #Delete all logs about clients
        self.Addresses, self.ip_clients, self.client_queues, self.communicating_nickname, self.nickname_to_room, self.nickname_to_key, self.access_granted, self.rooms, self.rooms_waiting, self.nickname_to_id, self.room_leaders, self.nickname_room_attempts, self.last_time_online = others.delete_logs(
            room_name, client_ip, nickname, self.Addresses, self.ip_clients, self.client_queues, self.communicating_nickname,
            self.nickname_to_room, self.nickname_to_key, self.access_granted, self.rooms, self.rooms_waiting, self.nickname_to_id,
            self.room_leaders, self.nickname_room_attempts, self.last_time_online
            )

    def logging(self):
        if (time.time() - self.start_time) > self.time_between_reports:
            self.start_time = time.time()
            others.write_report(self.Addresses, self.banned_ip)

    def do_POST(self):
        client_ip, client_port = self.client_address
        content_length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(content_length)
        with LOCK: 
            self.log_info(client_ip)
            self.logging()
        if client_ip in self.banned_ip: return
        #Main code
        try: #Try decrypting the data
            wait = False
            data_temp = data
            data_temp = crypto.decrypt(self.private_key, data_temp)
            data_temp = data_temp.decode()
            #Payload
            client_time = data_temp.split("\n")[0] #First line of payload
            client_id = data_temp.split("\n")[1]
            client_action = data_temp.split("\n")[2]
            client_blob = data_temp.split("\n")[3]
            with LOCK: #Avoid race conditions
                #Checks
                if self.check_time(client_time): #TTL hasnt expired
                    if client_action.split(":")[0] == "auth": #Auth packet, which contains nickname not ID
                        offline_nickname = time.time() - float(client_time) > self.TTL_nickname #Nickname owner went offline for a certain amount of time? Rewrite data
                        if offline_nickname: self.remove_logs(client_ip, client_id) # Remove logs of the last client
                        if self.check_nickname(client_id) or offline_nickname: #Nickname is free
                            if self.check_access(client_ip, client_action, client_id): #Access_code is right, which should be atp by just decrypting the key.
                                #Stage 1
                                client_key = crypto.load_pub_key(crypto.base64_decode(client_blob))
                                (self.nickname_to_key).update({client_id: client_key})
                                client_generated_id = self.generate_id(client_id)
                                if client_ip in self.ip_clients: 
                                    clients = self.ip_clients[client_ip] + 1
                                else: 
                                    clients = 1
                                (self.ip_clients).update({client_ip: clients})
                                (self.nickname_room_attempts).update({client_id: 0})
                                (self.last_time_online).update({client_id: client_time}) #Log last time online
                                self.respond(200, crypto.encrypt(client_key, f"{client_generated_id}"),False)
                        else:
                            if self.check_access(client_ip, client_action, client_id): #Access_code is right
                                client_key = crypto.load_pub_key(crypto.base64_decode(client_blob))
                                self.respond(200, crypto.encrypt(client_key, "TAKEN"),False)
                    elif client_ip in self.access_granted:
                        nickname = self.id_to_nickname(client_id) #Id is valid? Extract the nickname
                        (self.last_time_online).update({nickname: client_time}) #Log last time online
                        client_key = self.nickname_to_key[nickname]
                        if self.nickname_room_attempts[nickname] > 3: #3 wrong room passwords guesses? Ignore nickname to avoid bruteforcing
                           self.respond(200, crypto.encrypt(client_key, "BANNED"),False)
                        elif nickname != False:
                            if client_action == "room_info":
                                lines = []
                                for k, v in (self.rooms).items():
                                    lines.append(f"{k}: {v} online")
                                data = '\n'.join(lines)
                                self.respond(200, crypto.encrypt(client_key, data),False)


                            elif client_action.split(":")[0] == "room_join":
                                selected_room = client_action.split(": ")[1]
                                if selected_room in self.rooms:
                                    (self.rooms_waiting).update({nickname: selected_room})
                                    wait = True
                                    other_side = self.room_leaders[selected_room]
                                    other_side_key = self.nickname_to_key[other_side]
                                    self._notify(other_side, crypto.encrypt(other_side_key, "\n".join(["REQ", nickname, client_blob])), 1)
                                else:
                                    self.respond(200, crypto.encrypt(client_key, "Unavailable"),False)


                            elif client_action.split(":")[0] == "room_create":
                                selected_room = client_action.split(": ")[1]
                                if selected_room in self.rooms:
                                    self.respond(200, crypto.encrypt(client_key, "Taken"),False)
                                else:
                                    (self.rooms).update({selected_room: 1})
                                    (self.room_leaders).update({selected_room: nickname})
                                    (self.communicating_nickname).append(nickname)
                                    (self.nickname_to_room).update({nickname: selected_room})
                                    self.respond(200, crypto.encrypt(client_key, "Success"),False)


                            elif client_action.split(":")[0] == "room_respond":
                                selected_room = self.nickname_to_room[nickname]
                                if nickname == self.room_leaders[selected_room]: #Does responder have the privileges?
                                    other_side_nickname = client_action.split(": ")[1]
                                    if other_side_nickname.split(",")[0] == "WRONG":
                                        other_side_nickname = other_side_nickname.split(",")[1]
                                        self.nickname_room_attempts[other_side_nickname] += 1
                                        other_side_key = self.nickname_to_key[other_side_nickname]
                                        self._notify(other_side_nickname, crypto.encrypt(other_side_key, "Wrong"), 1)

                                    elif other_side_nickname in self.rooms_waiting: #Is the other side really waiting for key?
                                        if self.rooms_waiting[other_side_nickname] == self.nickname_to_room[nickname]: #Is the other side waiting for this room key?
                                            self.rooms[selected_room] += 1
                                            other_side_key = self.nickname_to_key[other_side_nickname]
                                            self.nickname_to_room[other_side_nickname] = selected_room
                                            (self.communicating_nickname).append(other_side_nickname)
                                            (self.rooms_waiting).pop(other_side_nickname)
                                            self.nickname_room_attempts[other_side_nickname] = 0 #Reset ATT
                                            self._notify(other_side_nickname, crypto.encrypt(other_side_key, client_blob), 1)
                                            #Notify clients about new occupant
                                            room = self.nickname_to_room[nickname]
                                            for k, v in (self.nickname_to_room).items():
                                                if v == room and k != nickname and k != other_side_nickname:
                                                    other_side_key = self.nickname_to_key[k]
                                                    self._notify(k, crypto.encrypt(other_side_key, f"new_client: {other_side_nickname}"), 1)

                                    self.respond(200, crypto.encrypt(client_key, "OK"),False)

                            elif client_action == "room_details":
                                self.respond(200, crypto.encrypt(client_key, f"{self.rooms[self.nickname_to_room[nickname]]}"),False)


                            elif client_action == "load_msg" and nickname in self.communicating_nickname:
                                wait = True

                            elif client_action == "send_msg" and nickname in self.communicating_nickname:
                                room = self.nickname_to_room[nickname]
                                for k, v in (self.nickname_to_room).items():
                                    if v == room and k != nickname:
                                        other_side_key = self.nickname_to_key[k]
                                        msg = "\n".join([f"{nickname}", client_blob])
                                        self._notify(k, crypto.encrypt(other_side_key, msg), 1)
                                self.respond(200, crypto.encrypt(client_key, "OK"),False)

                            elif client_action == "QUIT":
                                self.remove_logs(client_ip, nickname)
                                self.respond(200, crypto.encrypt(client_key, "OK"),False)

            if wait == True: #Long poll outside of LOCK
                self._handle_wait(nickname)
        except:
            try:
                self.respond(200, "X",False)
            except BrokenPipeError:
                return

                    
    def do_GET(self):
        client_ip, client_port = self.client_address
        with LOCK: 
            self.log_info(client_ip)
            self.logging()
        if client_ip not in self.banned_ip:
            super().do_GET()

def main():
    others.check() #Check supported OS
    #Ensure clear terminal
    time.sleep(1)
    clear_cmd = others.os_def()
    others.clear(clear_cmd)
    #Start server
    port = 9001
    server = ThreadingHTTPServer(('', port), ThreadedHandler)
    print("server is running...")
    server.serve_forever()                

if __name__ == "__main__":
    main()