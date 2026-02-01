import requests as rq
from functions import crypto, others
import re as r #RegEx lib
from urllib.request import urlopen

def get_public_ip():
    data = str(urlopen('http://checkip.dyndns.com/').read())
    ip = r.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(data).group(1)
    return "127.0.0.1"
    #return ip

def main():
    server = input("Enter the server ip with port(default port 80): ")
    access_code = others.get_safe_input("Enter the server access code: ")
    access = False
    #Send the server Access_code+YourPublicIP hashed so noone can replicate your request with sucess
    access_code = f"{access_code}{get_public_ip()}"
    hashed_access_code = crypto.hash_text(access_code)
    rq.get(f"http://{server}/?code={hashed_access_code}")
    others.wait(1)
    #Check if access was granted
    r = rq.get(f"http://{server}/auth.txt")
    for line in (r.text).splitlines():
        if line.strip() == crypto.hash_text(get_public_ip()): access = True
    if access == True: print("Access granted")

if __name__ == "__main__":
    main()