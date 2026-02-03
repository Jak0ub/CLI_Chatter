from functions import crypto, others

def decode(params, query, key):
    answer = crypto.base64_decode(params.split(f"{query}=")[1].split(" ")[0]) #Get request from authorized client
    answer = crypto.str_to_bytes(answer)#Str to bytes
    return crypto.decrypt(key,answer) #Decrypt text from client using private key

def retrieve_key(params):
    key = params.split("key=")[1].split(" ")[0]
    key = crypto.base64_decode(key)
    key = crypto.str_to_bytes(key)
    return crypto.load_pub_key(key)

def main():
    others.check()
    server = others.init()
    others.wait(1) #Ensure clear terminal
    clear_cmd = others.os_def()
    others.clear(clear_cmd)
    private_key, public_key = crypto.generate_keys()
    crypto.save_pub_key(public_key, "key")
    access_code = others.get_safe_input("Create password for server access: ")
    rooms = others.create_rooms(int(input("Enter how many chat rooms you'd like: ")))
    others.clear(clear_cmd)
    print("Server is running")

    room_quit = 0
    ddos_protection = 30 #If one IP exceed this number of packets. The server shuts down this IP
    resolved = 0 #Number of requests resolved already
    access_granted = []
    Addresses = []
    banned_ip = [] 
    communicating_ip = []
    ip_to_room = {} #Which ip is in which room
    ip_to_key = {} # {127.0.0.1: True} means we have key for 127.0.0.1 ip
    keys = [] #Public keys of clients


    while True:
        others.wait(0.1)
        with open("../log.txt", "r") as f: lines = f.readlines()
        lines = lines[(resolved):]#exclude the lines already resolved
        if resolved > 100: #After 100 packets. Delete logs and write a report of banned IP addr. CHANGE THIS NUMBER IF NEEDED!
            others.write_report(Addresses, banned_ip) #Write a report of banned IP addr. if needed. 
            with open("../log.txt", "w") as f: f.write(""); resolved = 0#Clear logs

        for line in lines: #Resolving requests
            ip, params = others.info(line)
            #Packet counter. DDOS PROTECTION
            print(banned_ip)
            print(Addresses)
            if ip not in access_granted:
                if len(Addresses) == 0: Addresses.append([ip, 0])
                for adr in Addresses:
                    if adr[0] == ip: 
                        Addresses[Addresses.index(adr)][1] += 1
                        if Addresses[Addresses.index(adr)][1] >= ddos_protection and ip not in banned_ip: banned_ip.append(ip)
                        break
                    elif adr[0] != ip and Addresses.index(adr) == len(Addresses)-1: Addresses.append([ip, 0]) #Not logged yet
                if ip in banned_ip: continue
                #Access solution
                #If the access_code+OriginIP hashed match the parameter given. The IP has access granted. Just prevention system
                access_code_for_this_ip = f"{access_code}{ip}"
                hashed_access_code_for_this_ip = crypto.hash_text(access_code_for_this_ip)
                if params != "":
                    if params.split("=")[0].lower() == "code" and params.split("code=")[1].split(" ")[0] == hashed_access_code_for_this_ip:
                        access_granted.append(ip)
                        others.save_authorized_ip(crypto.hash_text(str(ip)))
                        ip_to_room.update({ip: 0}) #Default room 0
                        ip_to_key.update({ip: False}) #No key for this IP yet

            else:
                if params != "":
                    if params.split("=")[0].lower() == "room":
                        try: room_num =  decode(params, "room", private_key)
                        except: continue 
                        #Convert to int to ensure the decryption was errorless
                        try: room_num = int(room_num)
                        except ValueError: pass
                        if type(room_num) == int:
                            #Ensure no IndexError occurs
                            if room_num <= len(rooms) and room_num > 0:
                                if rooms[room_num-1] == 0 and ip_to_room[ip] != room_num: #If the room is not full and current ip is not in this room
                                    if ip_to_room[ip] != 0:
                                        rooms[ip_to_room[ip]-1] -= 1
                                        with open(f"{ip_to_room[ip]}.txt", "w") as f: f.write(f"{rooms[ip_to_room[ip]-1]}\n")#Leave the previous room
                                    rooms[room_num-1] += 1
                                    ip_to_room[ip] = room_num
                                    #Join new room
                                    with open(f"{room_num}.txt", "w") as f: f.write(f"{rooms[room_num-1]}\n") #Write status to the file
                                elif rooms[room_num-1] == 1 and ip_to_room[ip] != room_num: #Ask the other side for approval to join
                                    other_side = next(k for k, v in ip_to_room.items() if v == room_num)
                                    if ip_to_key[other_side] == True: #Key obtained. E2EE available
                                        for value in keys: 
                                            if value[0] == other_side: pub_key_client = value[1]
                                        with open(f"{room_num}.txt", "w") as f: f.writelines(["1\n", f"{crypto.encrypt(pub_key_client, f"{ip}")}"])
  
                    elif params.split("=")[0].lower() == "key":
                        #Decode the key and make it usable
                        try: key = retrieve_key(params)
                        except: continue
                        #If key for this ip was not saved, save it
                        if keys == []: keys.append([ip, key]); ip_to_key[ip] = True
                        for values in keys:
                            if values[0] == ip: values[1] = key
                            if values[0] != ip and keys.index(values) == len(keys)-1: keys.append([ip, key]); ip_to_key[ip] = True

                    elif params.split("=")[0].lower() == "respond":
                        #Get respond msg from client 1 and acknowledge the other side with specific IP specified by responder side
                        if ip_to_room[ip] == 0: continue #Prevent errors if the respond msg was sent by unauthorized person
                        if rooms[ip_to_room[ip]-1] == 1:
                            try: 
                                msg = decode(params, "respond", private_key)
                                ip_to_room[msg.decode("utf-8")] = ip_to_room[ip] #Convert reciever to specific room
                            except: continue
                            for value in keys: 
                                if value[0] == msg.decode("utf-8"): pub_key_client = value[1]  
                            with open(f"{ip_to_room[ip]}.txt", "w") as f: f.writelines(["1\n", f"{crypto.encrypt(pub_key_client, f"{msg.decode("utf-8")}")}"])
                    
                    elif params.split("=")[0].lower() == "start":
                        try:
                            for val in ip_to_room:
                                if ip_to_room[val] == ip_to_room[ip] and rooms[ip_to_room[ip]-1] == 1 and val != ip: #Room was not yet updated and this is valid response to start chatting
                                    rooms[ip_to_room[ip]-1] += 1
                                    other_side = val
                                    with open(f"{ip_to_room[ip]}.txt", "w") as f: f.writelines(["2\n", "\n", "\n"]) #Prepare file for two way communication
                                    #Append both IP for future communication
                                    communicating_ip.append(ip)  #The requester IP is 1st
                                    communicating_ip.append(val) #Origin IP is 2nd
                                    break
                        except: continue #Not valid request? Skip this packet
                        #Save client-side pub keys
                        for key in keys:
                            if key[0] == ip:
                                side1_key = key[1]
                            elif key[0] == val:
                                side2_key = key[1]
                        others.create_room_share(ip_to_room[ip], side1_key, side2_key)
                        

                    elif params.split("=")[0].lower() == "msg":
                        if ip in communicating_ip:
                            try:
                                msg = crypto.base64_decode(params.split(f"msg=")[1].split(" ")[0]) #Base64 decode encrypted msg
                                msg = crypto.str_to_bytes(msg)#Str to bytes
                                with open(f"{ip_to_room[ip]}.txt", "r") as f: l = f.readlines() #Load room data to change only specific line
                                other_side = others.get_other_side(ip_to_room, ip)
                                l[(communicating_ip.index(ip)%2)+1] = f"{msg}\n" #Save msg
                                with open(f"{ip_to_room[ip]}.txt", "w")as f: f.writelines(l) #Save changes
                            except: continue #Not valid request? Skip
                    
                    elif params.split("=")[0].lower() == "quit":
                        try:
                            #Get needed info about both sides
                            if ip in communicating_ip:
                                other_side = others.get_other_side(ip_to_room, ip)
                                room_quit = ip_to_room[ip]
                            #Delete all logs about clients
                            communicating_ip, ip_to_room, ip_to_key, keys, rooms, Addresses, access_granted = others.clean_room(room_quit, ip, other_side, communicating_ip, ip_to_room, ip_to_key, keys, rooms, Addresses, access_granted)
                        except: continue
        resolved += len(lines)

    #todo
    if others.clean(server) == 1:
        print("server stopped successfully")
    else:
        print("error occured")

if __name__ == "__main__":
    main()