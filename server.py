from functions import crypto, others


def main():
    others.check()
    server = others.init()
    others.wait(1) #Ensure clear terminal
    others.cli_clear()
    private_key, public_key = crypto.generate_keys()
    crypto.save_pub_key(public_key)
    access_code = others.get_safe_input("Create password for server access: ")

    ddos_protection = 30 #If one IP exceed this number of packets. The server shuts down this IP
    resolved = 0 #Number of requests resolved already
    access_granted = []
    Addresses = []
    banned_ip = []
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
                if params.split("=")[0].lower() == "code" and params.split("=")[1] == hashed_access_code_for_this_ip:
                    access_granted.append(ip)
                    others.save_authorized_ip(crypto.hash_text(str(ip)))

            
        resolved += len(lines)




        if len(banned_ip) != 0 or len(access_granted) != 0: others.wait(10);break #For testing ONLY

    if others.clean(server) == 1:
        print("server stopped successfully")
    else:
        print("error occured")

if __name__ == "__main__":
    main()

