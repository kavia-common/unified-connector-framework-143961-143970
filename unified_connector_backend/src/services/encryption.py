"""
Encryption utilities for secrets and tokens using Fernet (AES128 in CBC + HMAC).
"""

from typing import Optional

from cryptography.fernet import Fernet, MultiFernet
from src.core.config import get_settings
from src.core.logging_config import get_logger

_logger = get_logger(__name__)


class EncryptionService:
    """Provides encryption/decryption for stored secrets and tokens."""

    def __init__(self, key: Optional[str] = None) -> None:
        settings = get_settings()
        fernet_key = key or settings.ENCRYPTION_KEY
        if not fernet_key:
            # Generate ephemeral key for dev to avoid hard failure; log a warning.
            generated = Fernet.generate_key()
            _logger.warning("ENCRYPTION_KEY not set; using ephemeral key (non-persistent).")
            self._fernet = MultiFernet([Fernet(generated)])
        else:
            try:
                k = fernet_key.encode("utf-8")
                # Validate key shape by instantiating Fernet
                self._fernet = MultiFernet([Fernet(k)])
            except Exception as exc:
                raise ValueError("Invalid ENCRYPTION_KEY configured") from exc
        self._aad = (settings.TOKEN_ENCRYPTION_ADDITIONAL_DATA or "").encode("utf-8")

    # PUBLIC_INTERFACE
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext into a URL-safe token."""
        token = self._fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    # PUBLIC_INTERFACE
    def decrypt(self, token: str) -> str:
        """Decrypt token back to plaintext."""
        data = self._fernet.decrypt(token.encode("utf-8"))
        return data.decode("utf-8")


_encryption_singleton: Optional[EncryptionService] = None


# PUBLIC_INTERFACE
def get_encryption_service() -> EncryptionService:
    """Get the application-wide encryption service."""
    global _encryption_singleton
    if _encryption_singleton is None:
        _encryption_singleton = EncryptionService()
    return _encryption_singleton
