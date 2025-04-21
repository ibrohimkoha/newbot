from pydantic import BaseModel

class LoginAdminSchema(BaseModel):
    telegram_id: int
    password: str

class AdminResponseSchema(BaseModel):
    full_name: str
    telegram_id: int