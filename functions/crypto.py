from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from hashlib import sha256
import base64, ast
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

def str_to_bytes(text): #Convert string b"text" to bytes
    return ast.literal_eval(text)

def base64_encode(text): #Convert text to base64
    bytes_text =  text.encode("ascii")
    b64_bytes = base64.b64encode(bytes_text)
    b64_str = b64_bytes.decode("ascii")
    return b64_str


def base64_decode(text): #Decode text from base64 string/bytes
    b64_text =  text.encode("ascii")
    b64_bytes = base64.b64decode(b64_text)
    text = b64_bytes.decode("ascii")
    return text


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


def encrypt(public_key, msg=str): #Encrypt msg using public key
    msg = msg.encode("utf-8")
    encrypted = public_key.encrypt(msg, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    return encrypted

def decrypt(private_key, msg): #Decrypt msg using priv key
    decrypted = private_key.decrypt(msg,padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    return decrypted

def hash_text(text=str): #Convert text to sha256 hash alg type
    return sha256(text.encode("utf-8")).hexdigest()

def load_pub_key(pub): #Load pub key from string for future encryption
    return serialization.load_pem_public_key(pub)

def send_key(server,public_key,access_code):
    public_key_bytes = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
    public_key_str = public_key_bytes.decode("ascii")
    public_key_lines = public_key_str.split("\n")
    for i in range(3):
        if i == 0: public_key_lines.pop(i)
        else: public_key_lines.pop(-1)
    key_str = "\n".join(public_key_lines)
    key_encrypted = encrypt_using_passwd(key_str, access_code)
    rq.get(f"http://{server}/?key={key_encrypted}") #Send the pub key encrypted to avoid Mitm