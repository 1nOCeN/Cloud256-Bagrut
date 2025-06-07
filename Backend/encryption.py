import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from db import get_encryption_key_from_db, store_encryption_key_to_db


class EncryptionManager:
    """מחלקה לניהול הצפנה וחתימה דיגיטלית"""

    def __init__(self):
        self.rsa_private_key = None
        self.rsa_public_key = None
        self.encryption_key = None
        self._load_or_generate_keys()

    def generate_aes_key(self):
        """יצירת מפתח AES חדש"""
        return os.urandom(32)

    def generate_rsa_keys(self):
        """יצירת מפתחות RSA חדשים"""
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        # שמירת מפתח פרטי
        with open("private_key.pem", "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        # שמירת מפתח ציבורי
        with open("public_key.pem", "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

    def load_rsa_keys(self):
        """טעינת מפתחות RSA מקבצים"""
        try:
            with open("private_key.pem", "rb") as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)

            with open("public_key.pem", "rb") as f:
                public_key = serialization.load_pem_public_key(f.read())

            return private_key, public_key
        except FileNotFoundError:
            # אם הקבצים לא נמצאו, צור מפתחות חדשים
            self.generate_rsa_keys()
            return self.load_rsa_keys()

    def _load_or_generate_keys(self):
        """טעינה או יצירת מפתחות"""
        self.rsa_private_key, self.rsa_public_key = self.load_rsa_keys()
        self.encryption_key = self.get_encryption_key()

    def get_encryption_key(self):
        """קבלת מפתח הצפנה - טעינה מהDB או יצירת חדש"""
        key = get_encryption_key_from_db()
        if key:
            # פענוח מפתח AES באמצעות RSA
            encrypted_key = base64.b64decode(key)
            aes_key = self.rsa_private_key.decrypt(
                encrypted_key,
                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                             algorithm=hashes.SHA256(), label=None)
            )
            return aes_key
        else:
            # יצירת מפתח AES חדש
            aes_key = self.generate_aes_key()

            # הצפנת מפתח AES עם RSA לפני שמירה
            encrypted_key = self.rsa_public_key.encrypt(
                aes_key,
                padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                             algorithm=hashes.SHA256(), label=None)
            )
            store_encryption_key_to_db(base64.b64encode(encrypted_key).decode())
            return aes_key

    def encrypt_file(self, file_path):
        """הצפנת קובץ באמצעות AES-GCM"""
        nonce = os.urandom(12)
        cipher = Cipher(algorithms.AES(self.encryption_key), modes.GCM(nonce),
                        backend=default_backend())
        encryptor = cipher.encryptor()

        with open(file_path, "rb") as f:
            data = f.read()

        encrypted = encryptor.update(data) + encryptor.finalize()

        encrypted_file_path = file_path + ".enc"
        with open(encrypted_file_path, "wb") as f:
            f.write(nonce + encryptor.tag + encrypted)

        return encrypted_file_path

    def decrypt_file_data(self, encrypted_data):
        """פענוח נתוני קובץ מוצפן"""
        # חילוץ nonce (12 bytes), tag (16 bytes), ו-ciphertext
        nonce = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext = encrypted_data[28:]

        # יצירת cipher AES-GCM
        cipher = Cipher(algorithms.AES(self.encryption_key), modes.GCM(nonce, tag),
                        backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

        return decrypted_data