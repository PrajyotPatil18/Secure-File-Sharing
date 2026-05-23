import os
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

class AESCrypto:
    def __init__(self):
        self.key_size = 32  # 256 bits
        self.block_size = AES.block_size
    
    def generate_key(self):
        """Generate a random 256-bit AES key"""
        return get_random_bytes(self.key_size)
    
    def derive_key(self, password: str, salt: bytes = None) -> tuple:
        """Derive key from password using PBKDF2"""
        if salt is None:
            salt = get_random_bytes(16)
        
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return key, salt
    
    def encrypt_file(self, file_data: bytes, key: bytes) -> tuple:
        """Encrypt file data with AES-256-CBC"""
        iv = get_random_bytes(self.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        padded_data = pad(file_data, self.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        
        return iv + encrypted_data
    
    def decrypt_file(self, encrypted_data: bytes, key: bytes) -> bytes:
        """Decrypt file data with AES-256-CBC"""
        iv = encrypted_data[:self.block_size]
        cipher_text = encrypted_data[self.block_size:]
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = cipher.decrypt(cipher_text)
        
        return unpad(padded_data, self.block_size)
    
    def encrypt_with_password(self, file_data: bytes, password: str) -> tuple:
        """Encrypt file data with password-derived key"""
        key, salt = self.derive_key(password)
        encrypted_data = self.encrypt_file(file_data, key)
        return encrypted_data, salt
    
    def decrypt_with_password(self, encrypted_data: bytes, password: str, salt: bytes) -> bytes:
        """Decrypt file data with password-derived key"""
        key, _ = self.derive_key(password, salt)
        return self.decrypt_file(encrypted_data, key)

crypto = AESCrypto()