import bcrypt

# bcrypt only considers the first 72 bytes of a password; truncating here is the
# documented way to avoid the "password cannot be longer than 72 bytes" error.
_MAX_BYTES = 72


def hash_password(password: str) -> str:
    pw = password.encode("utf-8")[:_MAX_BYTES]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pw = plain_password.encode("utf-8")[:_MAX_BYTES]
    return bcrypt.checkpw(pw, hashed_password.encode("utf-8"))
