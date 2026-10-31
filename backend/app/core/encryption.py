import base64
import hashlib
import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings

logger = logging.getLogger("omnipulse.security.encryption")


class TokenEncryptionService:
    """
    Authenticated encryption service (Fernet / AES-128-CBC + HMAC-SHA256)
    used to securely encrypt OAuth access tokens and secrets at rest.
    """

    def __init__(self, key: Optional[str] = None):
        self._fernet: Optional[Fernet] = None
        self._init_cipher(key)

    def _init_cipher(self, explicit_key: Optional[str] = None):
        raw_key = (explicit_key or settings.TOKEN_ENCRYPTION_KEY or "").strip()
        
        if not raw_key:
            # Fallback deterministic key derivation for local development and testing
            seed = (settings.SUPABASE_ANON_KEY or "omnipulse-dev-secret-salt-key-32b").encode("utf-8")
            derived = base64.urlsafe_b64encode(hashlib.sha256(seed).digest())
            self._fernet = Fernet(derived)
            logger.debug("Initialized TokenEncryptionService with fallback derived key.")
        else:
            try:
                # Check if raw_key is already a valid 32-byte urlsafe base64 Fernet key
                self._fernet = Fernet(raw_key.encode("utf-8"))
            except Exception:
                # Derive a valid 32-byte urlsafe base64 key using SHA-256
                derived = base64.urlsafe_b64encode(hashlib.sha256(raw_key.encode("utf-8")).digest())
                self._fernet = Fernet(derived)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string using authenticated encryption."""
        if not plaintext:
            return ""
        try:
            return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to encrypt token: {e}")
            raise

    def decrypt(self, ciphertext: str) -> Optional[str]:
        """Decrypt ciphertext string. Returns None if invalid or corrupted."""
        if not ciphertext:
            return None
        try:
            return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            logger.warning("Token decryption failed: Invalid token or mismatched encryption key.")
            return None
        except Exception as e:
            logger.error(f"Error decrypting token: {e}")
            return None


encryption_service = TokenEncryptionService()
token_encryption_service = encryption_service
