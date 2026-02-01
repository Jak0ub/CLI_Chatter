from functions import crypto, others

def main():
    #others.check()
    server = others.init()
    others.wait(1) #Ensure clear terminal
    others.cli_clear()
    private_key, public_key = crypto.generate_keys()
    crypto.save_pub_key(public_key)
    access_code = others.get_safe_input("Create password for server access: ")
    rooms = others.create_rooms(int(input("Enter how many chat rooms you'd like: ")))
    others.cli_clear()
    print("Server is running")


    ddos_protection = 30 #If one IP exceed this number of packets. The server shuts down this IP
    resolved = 0 #Number of requests resolved already
    access_granted = []
    Addresses = []
    banned_ip = [] 
    ip_to_room = {} #Which ip is in which room
    ip_to_key = {} # {127.0.0.1: True} means we have key for 127.0.0.1 ip
    keys = [] #Public keys of clients


    while True:
        others.wait(0.1)
        with open("../log.txt", "r") as f: lines = f.readlines()
        lines = lines[(resolved):]#exclude the lines already resolved
        for line in lines:
            ip, params = others.info(line)
            if ip in banned_ip: continue
            #Packet counter. DDOS PROTECTION
            if ip not in access_granted:
                if len(Addresses) == 0: Addresses.append([ip, 0])
                for adr in Addresses:
                    if adr[0] == ip: 
                        Addresses[Addresses.index(adr)][1] += 1
                        if Addresses[Addresses.index(adr)][1] >= ddos_protection: banned_ip.append(ip)
                        break
                    elif adr[0] != ip and Addresses.index(adr) == len(Addresses): Addresses.append([ip, 0]) 
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
                        room_num = crypto.base64_decode(params.split("room=")[1].split(" ")[0]) #Get request from authorized client
                        room_num = crypto.str_to_bytes(room_num)#Str to bytes
                        room_num = crypto.decrypt(private_key,room_num) #Decrypt text from client using private key
                        #Convert to int to ensure the decryption was errorless
                        try: room_num = int(room_num)
                        except ValueError: pass
                        if type(room_num) == int:
                            #Ensure no IndexError occurs
                            if room_num <= len(rooms) and room_num > 0:
                                if rooms[room_num-1] == 0 and ip_to_room[ip] != room_num: #If the room is not full and current ip is not in this room
                                    if ip_to_room[ip] != 0:
                                        with open(f"{ip_to_room[ip]}.txt", "w") as f: f.write(f"{rooms[room_num-1]}\n")#Leave the previous room
                                    ip_to_room[ip] = room_num
                                    #Join new room
                                    with open(f"{room_num}.txt", "w") as f: f.write(f"{rooms[room_num-1]+1}\n") #Write status to the file
                                elif rooms[room_num-1] == 1 and ip_to_room[ip] != room_num: #Ask the other side for approval to join
                                    if ip_to_key[ip] == True: #Key obtained. E2EE available
                                        for value in keys: 
                                            if value[0] == ip: pub_key_client = value[1]
                                        with open(f"{ip_to_room[ip]}.txt", "w") as f: f.writelines(["1\n", f"{crypto.encrypt(pub_key_client, f"{ip}")}"])

                    elif params.split("=")[0].lower() == "key":
                        #Decode the key and make it usable
                        key = params.split("key=")[1].split(" ")[0]
                        key = crypto.base64_decode(key)
                        key = crypto.str_to_bytes(key)
                        key = crypto.load_pub_key(key)
                        #If key for this ip was not saved, save it
                        if keys == []: keys.append([ip, key]); ip_to_key[ip] = {ip: True}
                        for values in keys:
                            if values[0] == ip: break
                            if values[0] != ip and keys.index(values) == len(keys)-1: keys.append([ip, key]); ip_to_key[ip] = {ip: True}
            
        resolved += len(lines)

    if others.clean(server) == 1:
        print("server stopped successfully")
    else:
        print("error occured")

if __name__ == "__main__":
    main()

