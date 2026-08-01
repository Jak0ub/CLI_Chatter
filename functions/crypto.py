from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from hashlib import sha256
import base64, sys
import requests as rq
from cryptography.fernet import Fernet

def key_from_password(password: str) -> bytes: #Convert access code into hash able to be than used as a Fernet key
    digest = sha256(password.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)

def encrypt_using_passwd(message: str, key: str) -> bytes: #Encrypt public key using access code hashed
    return Fernet(key_from_password(key)).encrypt(message.encode("utf-8"))

def decrypt_using_passwd(message: bytes, key: str) -> bytes: #Decrypt public key using access code hashed
    decrypted = Fernet(key_from_password(key)).decrypt(message)
    return decrypted.decode("utf-8")

def base64_encode(text): #Convert text to base64
    b64_bytes = base64.b64encode(text)
    return b64_bytes

def base64_decode(text): #Decode text from base64 string/bytes
    b64_bytes = base64.b64decode(text.encode())
    return b64_bytes

def retrieve_key(key, access_code):
    key = decrypt_using_passwd(key, access_code)
    key = key.split("\n")
    key.insert(0, "-----BEGIN PUBLIC KEY-----")
    key.append("-----END PUBLIC KEY-----")
    key = "\n".join(key)
    key = key.encode("ascii")
    return load_pub_key(key)

def generate_keys(): #Generate your own pub and priv keys
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key

def save_pub_key(public_key, name, access_code): #Save pub key to file (for server only)
    with open(f"{name}.pub", "wb") as f:
        public_key_bytes = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
        public_key_str = public_key_bytes.decode("ascii")
        public_key_lines = public_key_str.split("\n")
        for i in range(3):
            if i == 0: public_key_lines.pop(i)
            else: public_key_lines.pop(-1)
        key_str = "\n".join(public_key_lines)
        key_encrypted = encrypt_using_passwd(key_str, access_code)
        f.write(key_encrypted)

def key_to_bytes(public_key): #Return readable string of pub key
    return public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

def encrypt(public_key, msg): #Encrypt msg using public key (hybrid RSA+Fernet, no length limit)
    if type(msg) != bytes: msg = msg.encode("utf-8")
    session_key = Fernet.generate_key() #One-time key
    ciphertext = Fernet(session_key).encrypt(msg)
    encrypted_key = public_key.encrypt(session_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    return encrypted_key + ciphertext

def decrypt(private_key, msg): #Decrypt msg using priv key (hybrid RSA+Fernet)
    key_len = private_key.key_size // 8
    encrypted_key = msg[:key_len]
    ciphertext = msg[key_len:]
    session_key = private_key.decrypt(encrypted_key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    return Fernet(session_key).decrypt(ciphertext)

def hash_text(text=str): #Convert text to sha256 hash alg type
    return sha256(text.encode("utf-8")).hexdigest()

def load_pub_key(pub): #Load pub key from string for future encryption
    return serialization.load_pem_public_key(pub)

def send_key(url,public_key,access_code):
    public_key_bytes = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
    public_key_str = public_key_bytes.decode("ascii")
    public_key_lines = public_key_str.split("\n")
    for i in range(3):
        if i == 0: public_key_lines.pop(i)
        else: public_key_lines.pop(-1)
    key_str = "\n".join(public_key_lines)
    data = encrypt_using_passwd(key_str, access_code)
    x = rq.post(url, data=data) #Send key
    if (x.text).split("\n")[0] == "X": print("Key sending failed..."); sys.exit()
    return x

def get_room_info(server,private_key):
    r = rq.post(f"{server}/rooms", data="")
    room_details_decoded = base64_decode(r.text)
    room_details_decrypted = decrypt(private_key, room_details_decoded)
    rooms = room_details_decrypted.decode()
    rooms = rooms.split("\n")
    #Show all rooms
    count_of_rooms = 0
    for room in rooms:
        count_of_rooms += 1
        print(f"{count_of_rooms}. room -> {room.split('-> ')[1].split('/')[0]}/2 online")