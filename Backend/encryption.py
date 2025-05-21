import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from db import get_encryption_key_from_db, store_encryption_key_to_db

def generate_aes_key():
    return os.urandom(32)  # AES-256

def get_encryption_key():
    key = get_encryption_key_from_db()
    if key:
        return base64.b64decode(key)  # decode from base64 string
    else:
        key = generate_aes_key()
        store_encryption_key_to_db(base64.b64encode(key).decode())  # encode to base64 string
        return key

encryption_key = generate_aes_key()

def encrypt_file(file_path):
    key = encryption_key  # Consider calling get_encryption_key() here
    nonce = os.urandom(12)  # GCM nonce
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()

    with open(file_path, "rb") as f:
        data = f.read()

    encrypted = encryptor.update(data) + encryptor.finalize()

    with open(file_path + ".enc", "wb") as f:
        f.write(nonce + encryptor.tag + encrypted)  # prepend nonce + tag

    return file_path + ".enc"
