import bcrypt

def hash_password(plain_password: str) -> str:
    """Parolni bcrypt bilan hash qilish."""
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode('utf-8')

def check_password(plain_password: str, hashed_password: str) -> bool:
    """Hashlangan parolni tekshirish."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
