"""
OAuth2 utilities: CSRF state and PKCE code verifier/challenge helpers.
"""

import base64
import hashlib
import os
from typing import Tuple


# PUBLIC_INTERFACE
def generate_csrf_state(len_bytes: int = 16) -> str:
    """Generate a URL-safe CSRF state string."""
    return base64.urlsafe_b64encode(os.urandom(len_bytes)).decode("utf-8").rstrip("=")


# PUBLIC_INTERFACE
def generate_pkce_pair() -> Tuple[str, str]:
    """Return (code_verifier, code_challenge) per PKCE S256."""
    verifier = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").rstrip("=")
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return verifier, challenge
