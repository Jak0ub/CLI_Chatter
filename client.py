import requests as rq
import getpass
from hashlib import sha256

server = input("Enter the server ip with port(default port 80): ")
access_code = getpass.getpass("Enter the server access code: ")
hashed_access_code = sha256(access_code.encode("utf-8")).hexdigest()
r = rq.get(f"http://{server}/?code={hashed_access_code}")
