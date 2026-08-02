from functions import crypto, others
import os, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import queue, time

LOCK = threading.Lock()
message_queue = queue.Queue()

class ThreadedHandler(SimpleHTTPRequestHandler):
    #Creating needed files outside of current dir to avoid any files leakage
    os.system("mkdir hosting")
    os.chdir("hosting")
    rooms_value, access_code, ddos_protection = others.get_env()
    private_key, public_key = crypto.generate_keys()
    if access_code == None: access_code = others.get_safe_input("Create password for server access: ")
    crypto.save_pub_key(public_key, "key", access_code)
    if rooms_value == None: rooms_value = int(input("Enter how many chat rooms you'd like: "))
    rooms = []
    for i in range(rooms_value):
        rooms.append(0)
    client_queues = {}
    access_granted = []
    Addresses = {}
    banned_ip = [] 
    communicating_ip = []
    ip_to_room = {} #Which ip is in which room
    ip_to_key = {} # {127.0.0.1: True} means we have key for 127.0.0.1 ip
    keys = {} #Public keys of clients; {IP: key_loaded}
    waiting_for_start = {} #{IP: room}
    waiting_for_room = {} #{IP: room}
    waiting_for_key = [] #Private encrypted keys
    approved = {} #{IP: room}
    time_between_reports = 60 #How much seconds does the program wait till it writes report
    start_time = time.time()

    def _notify(self,client_id,body,mode):
        q = self._get_queue(client_id)
        if mode == 1: #Normal handshake mode
            if body in ["OK", "X", "AUTH OK"]:
                body = body.encode()
            else:
                body = crypto.base64_encode(body)
        q.put(body)

    def _get_queue(self, client_id):
        with LOCK:
            if client_id not in self.client_queues:
                self.client_queues[client_id] = queue.Queue()
            return self.client_queues[client_id]

    def _handle_wait(self, client_id):
        q = self._get_queue(client_id)
        try:
            data = q.get(timeout=60)
            self.respond(200, data,True)
        except queue.Empty:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            with LOCK: #Remove details about client
                if client_id in self.access_granted: #Not yet deleted
                    self.remove_logs(client_id)
            self.wfile.write(b"TIMEOUT")

    def respond(self, code, msg,handler):
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        if handler == False: #Not called through handler, parse normally
            if msg in ["OK", "X", "AUTH OK"]:
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

    def check_access(self, client_ip, data):
        if client_ip not in self.banned_ip:
            #Access solution
            #If the access_code+OriginIP hashed match the parameter given. The IP has access granted. Just prevention system
            access_code_for_this_ip = f"{self.access_code}{client_ip}"
            hashed_access_code_for_this_ip = crypto.hash_text(access_code_for_this_ip)
            user_time = data.split("\n")[1]
            if time.time() - float(user_time) > 5: #Max 5s. Time is set as unix timestamp, so timezones aren't a problem.
                self.respond(200, "X",False)
            else:
                if data.split("\n")[0].split(": ")[0] == "auth":
                    if data.split("\n")[0].split(": ")[1] == hashed_access_code_for_this_ip:
                        if client_ip in self.ip_to_room:
                            self.remove_logs(client_ip) #Restart variables for this IP.
                        (self.access_granted).append(client_ip)
                        (self.ip_to_room).update({client_ip: 0}) #Default room 0
                        (self.ip_to_key).update({client_ip: False}) #No key for this IP yet
                        self.respond(200, "AUTH OK",False)

    def remove_logs(self, client_ip): #Remove all logs and queues
        #Get needed info about both sides
        try:
            room_quit = self.ip_to_room[client_ip]
        except KeyError:
            room_quit = 0
        #Delete all logs about clients
        self.communicating_ip, self.ip_to_room, self.ip_to_key, self.keys, self.rooms, self.Addresses, self.access_granted, self.waiting_for_start, self.waiting_for_room, self.waiting_for_key, self.approved, self.client_queues = others.delete_logs(
            room_quit, client_ip, self.communicating_ip, self.ip_to_room, self.ip_to_key, self.keys, self.rooms, self.Addresses,
            self.access_granted, self.waiting_for_start, self.waiting_for_room, self.waiting_for_key, self.approved, self.client_queues
        )

    def logging(self):
        if (time.time() - self.start_time) > self.time_between_reports:
            self.start_time = time.time()
            others.write_report(self.Addresses, self.banned_ip)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        client_ip, client_port = self.client_address
        content_length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(content_length)
        with LOCK: 
            self.log_info(client_ip)
            self.logging()
        if client_ip in self.banned_ip: return
        if path == '/quit' and client_ip in self.communicating_ip:
            try:
                data_temp = crypto.decrypt(self.private_key, data)
                data_temp = data_temp.decode()
                if data_temp.split("\n")[0].split(": ")[0] == "quit" and f"{self.ip_to_room[client_ip]}" == data_temp.split("\n")[0].split(": ")[1]:
                    room_num = self.ip_to_room[client_ip]
                    with LOCK: self.remove_logs(client_ip) #Safely remove logs
                    self.respond(200, "OK", False)
            except:
                self.respond(200, "X", False)

        if path == '/key' and client_ip in self.access_granted:
            if client_ip in self.communicating_ip and client_ip in self.waiting_for_key: #Relay key, client will check
                with LOCK: #Safe key exchange process
                    (self.waiting_for_key).pop((self.waiting_for_key).index(client_ip))
                    room_num = self.ip_to_room[client_ip]
                    other_side = next(k for k, v in (self.ip_to_room).items() if v == room_num and k != client_ip)
                self._notify(other_side,data,0)
                if other_side in self.waiting_for_key:
                    self._handle_wait(client_ip) #Waiting for the key
                else:
                    self.respond(200, "OK", False)

            else:
                #Decode the key and make it usable
                try:
                    key = crypto.retrieve_key(data, self.access_code)
                    #If key for this ip was not saved, save it
                    with LOCK:
                        if self.keys == {}: (self.keys).update({client_ip: key}); self.ip_to_key[client_ip] = True
                        (self.keys).update({client_ip: key})
                        self.ip_to_key[client_ip] = True
                    self.respond(200, "OK",False)
                except: self.respond(200, "X",False)

        elif path == '/rooms' and client_ip in self.access_granted:
            #Decode the key and make it usable
            pub_key_client = self.keys[client_ip]
            lines = []
            for room in self.rooms:
                lines.append(f"{len(lines)+1} -> {room}/2")
            self.respond(200, crypto.encrypt(pub_key_client, "\n".join(lines)),False)

        elif path == '/data':
            if client_ip in self.communicating_ip:#Relay messagess
                try:
                    data_temp = crypto.decrypt(self.private_key, data)
                    data_temp = data_temp.decode()
                    room_num = self.ip_to_room[client_ip]
                    other_side = next(k for k, v in (self.ip_to_room).items() if v == room_num and k != client_ip)
                    if int(data_temp.split("\n")[0]) == self.ip_to_room[client_ip]: #Long poll the request, because this was message recieving request
                        self._handle_wait(client_ip)
                except Exception as e:
                    if e is not queue.Empty:
                        try:
                            room_num = self.ip_to_room[client_ip]
                            other_side = next(k for k, v in (self.ip_to_room).items() if v == room_num and k != client_ip)
                        except: other_side = "" #Other side has already quit.
                        if other_side not in self.waiting_for_key and client_ip not in self.waiting_for_key and other_side != "": #Chat is legit
                            self._notify(other_side, data, 0)
                            self.respond(200,"OK",False)
                    
            try: #Enable relogin after not fully closed session
                data_temp = data
                data_temp = crypto.decrypt(self.private_key, data_temp)
                data_temp = data_temp.decode()
                if data_temp.split("\n")[0].split(": ")[0] == "auth":
                    with LOCK: #Safe editing variables
                        self.check_access(client_ip, data_temp)
            except: 
                if client_ip not in self.communicating_ip:self.respond(200, "X",False)

            if client_ip in self.access_granted and data != data_temp: #Data was decrypted, meaning it was intended for server to see
                data_lines = data_temp.split("\n")
                try: data_line_1 = data_lines[1]    
                except: data_line_1 = "" 

                if data_lines[0].split(": ")[0] == "room" and client_ip not in self.communicating_ip:
                    try: room_num =  int(data_lines[0].split(": ")[1])
                    except ValueError: self.respond(200, "X",False); room_num = 0
                    if room_num != 0:
                        if self.rooms[room_num-1] == 0 and self.ip_to_room[client_ip] != room_num: #If the room is not full and current ip is not in this room
                            with LOCK:
                                if self.ip_to_room[client_ip] != 0: #Leave the previous room
                                    self.rooms[self.ip_to_room[client_ip]-1] = 0
                                self.rooms[room_num-1] += 1
                                self.ip_to_room[client_ip] = room_num
                                #Join new room
                                (self.waiting_for_room).update({client_ip: room_num})
                            self._handle_wait(client_ip) #Waiting for requests to join in

                        elif self.rooms[room_num-1] == 1 and self.ip_to_room[client_ip] != room_num and data_line_1 != "start": #Ask the other side for approval to join
                            with LOCK:
                                if self.ip_to_room[client_ip] != 0: #Leave the previous room
                                    self.rooms[self.ip_to_room[client_ip]-1] = 0
                                    self.ip_to_room[client_ip] = 0
                                other_side = next(k for k, v in (self.ip_to_room).items() if v == room_num)
                                pub_key_client = self.keys[other_side]
                                (self.waiting_for_room).update({client_ip: room_num})
                            self._notify(other_side,crypto.encrypt(pub_key_client, f"{client_ip}"),1)
                            self._handle_wait(client_ip) #Waiting for response to the request
                        
                        elif self.ip_to_room[client_ip] != 0 and self.rooms[self.ip_to_room[client_ip]-1] == 1 and data_line_1.split(": ")[1] in ["y", "n"]:#If the ip is in this room and is the only one
                            other_side = data_lines[1].split(": ")[0]
                            try: 
                                if self.waiting_for_room[other_side] == self.ip_to_room[client_ip]:
                                    if data_lines[1].split(": ")[1] == "y": #Approved
                                        pub_key_client = self.keys[other_side]
                                        self._notify(other_side,crypto.encrypt(pub_key_client, f"y,{client_ip}"),1)
                                        with LOCK:
                                            (self.waiting_for_start).update({other_side: self.ip_to_room[client_ip]})
                                            (self.approved).update({other_side: room_num})
                                        self._handle_wait(client_ip)
                                    else: #Rejected
                                        pub_key_client = self.keys[other_side]
                                        with LOCK:
                                            (self.waiting_for_room).pop(other_side)
                                        self._notify(other_side,crypto.encrypt(pub_key_client, f"n"),1)
                                        self._handle_wait(client_ip)
                            except KeyError: self.respond(200, "X",False)
                            
                        elif client_ip in self.waiting_for_start: #Last step of handshake
                            if room_num <= len(self.rooms) and room_num > 0: 
                                if data_line_1 == "start" and client_ip in self.waiting_for_start:
                                    other_side = next(k for k, v in (self.ip_to_room).items() if v == room_num)
                                    for ip in [client_ip, other_side]:
                                        (self.waiting_for_room).pop(ip)
                                    with LOCK:
                                        self.ip_to_room[client_ip] = room_num
                                    if self.rooms[room_num-1] == 1 and client_ip in self.approved and self.approved[client_ip] == room_num:
                                        pub_key_client = self.keys[other_side]
                                        #Update data
                                        with LOCK:
                                            (self.approved).pop(client_ip)
                                            self.rooms[room_num-1] = 2
                                            for ip in [client_ip, other_side]:
                                                (self.communicating_ip).append(ip)
                                                (self.waiting_for_key).append(ip)
                                            (self.waiting_for_start).pop(client_ip)
                                        self._notify(other_side,crypto.encrypt(pub_key_client, "start"),1)
                                        self._handle_wait(client_ip)
                                        
                        elif self.rooms[room_num-1] == 2: #If the request is nonsense
                            pub_key_client = self.keys[client_ip]
                            self.respond(200, crypto.encrypt(pub_key_client, "FULL"),False)



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