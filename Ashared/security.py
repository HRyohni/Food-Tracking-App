from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings

# bcrypt only considers the first 72 bytes of a password; truncating here is the
# documented way to avoid the "password cannot be longer than 72 bytes" error.
_MAX_BYTES = 72


def hash_password(password: str) -> str:
    pw = password.encode("utf-8")[:_MAX_BYTES]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pw = plain_password.encode("utf-8")[:_MAX_BYTES]
    return bcrypt.checkpw(pw, hashed_password.encode("utf-8"))


def create_access_token(subject: int | str, token_type: str) -> str:
    """Issue a signed JWT.

    subject    -> the user's id (stored as the "sub" claim)
    token_type -> "customer" | "partner" | "worker"; each service only accepts
                  tokens whose type matches, so tokens aren't cross-usable.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(subject), "type": token_type, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode/verify a JWT. Raises jwt.PyJWTError (incl. expiry) on failure."""
    return jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
