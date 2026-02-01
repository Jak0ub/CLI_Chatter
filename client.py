import requests as rq
import re as r #RegEx lib
from urllib.request import urlopen
import getpass
from hashlib import sha256

def get_public_ip():
    data = str(urlopen('http://checkip.dyndns.com/').read())
    ip = r.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(data).group(1)
    return "127.0.0.1"
    #return ip

def main():
    server = input("Enter the server ip with port(default port 80): ")
    access_code = getpass.getpass("Enter the server access code: ")

    #Send the server Access_code+YourPublicIP hashed so noone can replicate your request with sucess
    access_code = f"{access_code}{get_public_ip()}"
    hashed_access_code = sha256(access_code.encode("utf-8")).hexdigest()
    rq.get(f"http://{server}/?code={hashed_access_code}")


if __name__ == "__main__":
    main()