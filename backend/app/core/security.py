import base64
import hashlib
import hmac
import secrets

from app.core.config import settings

_PBKDF2_ALGORITHM = "sha256"
_PBKDF2_ITERATIONS = 600_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return (
        f"pbkdf2_{_PBKDF2_ALGORITHM}${_PBKDF2_ITERATIONS}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(digest).decode('ascii')}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iterations, salt_b64, digest_b64 = password_hash.split("$", 3)
    except ValueError:
        return False

    if scheme != f"pbkdf2_{_PBKDF2_ALGORITHM}":
        return False

    salt = base64.b64decode(salt_b64.encode("ascii"))
    expected_digest = base64.b64decode(digest_b64.encode("ascii"))
    candidate_digest = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        int(iterations),
    )
    return hmac.compare_digest(candidate_digest, expected_digest)


def generate_mcp_token(prefix: str | None = None) -> str:
    token_prefix = prefix if prefix is not None else settings.mcp_token_prefix
    return f"{token_prefix}{secrets.token_urlsafe(24)}"
