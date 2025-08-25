"""Encryption utilities for sensitive data."""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..config import settings


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize the encryption service.
        
        Args:
            master_key: Master key for encryption. If None, uses config.
        """
        if master_key is None:
            master_key = settings.encryption_master_key
            
        if not master_key:
            raise ValueError("Encryption master key not provided")
        
        # Derive encryption key from master key using PBKDF2
        # In production, use a random salt per encrypted item
        salt = b"vils_salt_change_in_production"  # Use random salt per item in prod
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string value.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            The encrypted string (base64 encoded)
        """
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a string value.
        
        Args:
            ciphertext: The encrypted string to decrypt
            
        Returns:
            The decrypted string
        """
        return self.cipher.decrypt(ciphertext.encode()).decode()
    
    def encrypt_dict(self, data: dict) -> str:
        """Encrypt a dictionary as JSON.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Encrypted JSON string
        """
        import json
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, ciphertext: str) -> dict:
        """Decrypt a JSON dictionary.
        
        Args:
            ciphertext: Encrypted JSON string
            
        Returns:
            Decrypted dictionary
        """
        import json
        json_str = self.decrypt(ciphertext)
        return json.loads(json_str)


# Global encryption service instance
encryption_service = EncryptionService()


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key.
    
    Args:
        api_key: The API key to encrypt
        
    Returns:
        Encrypted API key
    """
    return encryption_service.encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key.
    
    Args:
        encrypted_key: The encrypted API key
        
    Returns:
        Decrypted API key
    """
    return encryption_service.decrypt(encrypted_key)


def encrypt_service_config(config_data: dict) -> str:
    """Encrypt service configuration data.
    
    Args:
        config_data: Configuration dictionary
        
    Returns:
        Encrypted configuration
    """
    return encryption_service.encrypt_dict(config_data)


def decrypt_service_config(encrypted_config: str) -> dict:
    """Decrypt service configuration data.
    
    Args:
        encrypted_config: Encrypted configuration
        
    Returns:
        Decrypted configuration dictionary
    """
    return encryption_service.decrypt_dict(encrypted_config)