"""
Cryptographic utilities for the secure email system
"""
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
import os
import base64


class CryptoUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def generate_rsa_key_pair():
        """Generate RSA key pair (2048 bits)"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    @staticmethod
    def serialize_public_key(public_key) -> str:
        """Serialize public key to PEM format string"""
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
    
    @staticmethod
    def serialize_private_key(private_key) -> str:
        """Serialize private key to PEM format string"""
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return pem.decode('utf-8')
    
    @staticmethod
    def deserialize_public_key(public_key_str: str):
        """Deserialize public key from PEM format string"""
        return serialization.load_pem_public_key(
            public_key_str.encode('utf-8'),
            backend=default_backend()
        )
    
    @staticmethod
    def deserialize_private_key(private_key_str: str):
        """Deserialize private key from PEM format string"""
        return serialization.load_pem_private_key(
            private_key_str.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
    
    @staticmethod
    def generate_symmetric_key() -> bytes:
        """Generate 256-bit symmetric key for AES"""
        return os.urandom(32)  # 32 bytes = 256 bits
    
    @staticmethod
    def encrypt_symmetric(message: str, key: bytes) -> tuple:
        """Encrypt message using AES-256-CBC"""
        # Generate random IV
        iv = os.urandom(16)  # 16 bytes for AES block size
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Pad message to block size
        message_bytes = message.encode('utf-8')
        pad_length = 16 - (len(message_bytes) % 16)
        padded_message = message_bytes + bytes([pad_length] * pad_length)
        
        # Encrypt
        ciphertext = encryptor.update(padded_message) + encryptor.finalize()
        
        # Return base64 encoded ciphertext and IV
        return base64.b64encode(ciphertext).decode('utf-8'), base64.b64encode(iv).decode('utf-8')
    
    @staticmethod
    def decrypt_symmetric(encrypted_message: str, iv_str: str, key: bytes) -> str:
        """Decrypt message using AES-256-CBC"""
        ciphertext = base64.b64decode(encrypted_message)
        iv = base64.b64decode(iv_str)
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        padded_message = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove padding
        pad_length = padded_message[-1]
        message = padded_message[:-pad_length]
        
        return message.decode('utf-8')
    
    @staticmethod
    def encrypt_with_public_key(data: bytes, public_key) -> str:
        """Encrypt data using RSA public key"""
        encrypted = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode('utf-8')
    
    @staticmethod
    def decrypt_with_private_key(encrypted_data: str, private_key) -> bytes:
        """Decrypt data using RSA private key"""
        encrypted_bytes = base64.b64decode(encrypted_data)
        decrypted = private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted
    
    @staticmethod
    def hash_message(message: str) -> str:
        """Generate SHA-256 hash of message"""
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(message.encode('utf-8'))
        message_hash = digest.finalize()
        return base64.b64encode(message_hash).decode('utf-8')
    
    @staticmethod
    def sign_message(message_hash: str, private_key) -> str:
        """Sign message hash using RSA private key"""
        signature = private_key.sign(
            message_hash.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')
    
    @staticmethod
    def verify_signature(message_hash: str, signature: str, public_key) -> bool:
        """Verify digital signature"""
        try:
            signature_bytes = base64.b64decode(signature)
            public_key.verify(
                signature_bytes,
                message_hash.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

