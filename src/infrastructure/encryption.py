"""Encryption service for sensitive data using AES-256."""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os


class EncryptionService:
    """AES-256 encryption for sensitive data using Fernet."""
    
    def __init__(self, master_key: str):
        """
        Initialize encryption service.
        
        Args:
            master_key: Master encryption key from environment
        """
        # Derive encryption key from master key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'dekids_salt_2024',  # Use unique salt per installation
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        encrypted = self.cipher.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string.
        
        Args:
            ciphertext: Base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            InvalidToken: If decryption fails
        """
        encrypted = base64.urlsafe_b64decode(ciphertext.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()
    
    @staticmethod
    def generate_master_key() -> str:
        """
        Generate a new master key for encryption.
        
        Returns:
            Base64-encoded random key suitable for use as master key
        """
        return base64.urlsafe_b64encode(os.urandom(32)).decode()
