import hashlib

def hash_password(password: str) -> str:
    """Hash a password using SHA-256 and return the hexadecimal digest."""
    return hashlib.sha256(password.encode()).hexdigest()
