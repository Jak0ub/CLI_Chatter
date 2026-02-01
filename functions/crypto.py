from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from hashlib import sha256


def generate_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key

def save_pub_key(public_key):
    with open("key.pub", "wb") as f:
        f.write(public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo))

def encrypt(public_key, msg=str):
    msg = msg.encode("utf-8")
    encrypted = public_key.encrypt(msg, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    return encrypted

def decrypt(private_key, msg):
    decrypted = private_key.decrypt(msg,padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    return decrypted

def hash_text(text=str):
    return sha256(text.encode("utf-8")).hexdigest()