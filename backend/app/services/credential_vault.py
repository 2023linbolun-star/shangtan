"""
Credential vault — encrypts/decrypts platform credentials per store.
Uses Fernet symmetric encryption. Key from environment variable.
"""
import json
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger("shangtanai.credentials")

_KEY = os.getenv("CREDENTIAL_ENCRYPTION_KEY", "")


def _get_fernet() -> Fernet:
    if not _KEY:
        raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY not set in environment")
    return Fernet(_KEY.encode() if isinstance(_KEY, str) else _KEY)


class CredentialVault:
    """Encrypt/decrypt platform credentials."""

    @staticmethod
    def encrypt(data: dict) -> bytes:
        f = _get_fernet()
        return f.encrypt(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    @staticmethod
    def decrypt(encrypted: bytes) -> dict:
        f = _get_fernet()
        try:
            return json.loads(f.decrypt(encrypted).decode("utf-8"))
        except InvalidToken:
            logger.error("Failed to decrypt credential — key mismatch or corrupted data")
            raise

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key. Call once during initial setup."""
        return Fernet.generate_key().decode("utf-8")


credential_vault = CredentialVault()
