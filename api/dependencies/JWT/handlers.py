from datetime import datetime, timedelta
from jose import jwt, JWTError

from config import JWT_SECRET_KEY, JWT_ALGORITHM


class JWTHandler:
    def __init__(self, data: dict = None):
        self.data = data

    def create_token(self, telegram_id: int, user_id: int):
        encode = {"sub": str(telegram_id), "id": user_id}
        expires = datetime.utcnow() + timedelta(hours=12)
        encode["exp"] = expires
        return jwt.encode(claims=encode, key=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


    def decode_jwt(self, token: str):
        try:
            # Decode and verify the token
            payload = jwt.decode(token, key=JWT_SECRET_KEY, algorithms=JWT_ALGORITHM)
            payload["sub"] = int(payload["sub"])  # <-- qayta int qilib olayapmiz
            return payload
        except JWTError as e:
            # Handle JWT decoding errors
            print(f"Error decoding token: {e}")
            return None
        except Exception as e:
            # Handle other exceptions
            print(f"Unexpected error: {e}")
            return None