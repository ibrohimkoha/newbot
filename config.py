from dotenv import load_dotenv
import os

load_dotenv()
image_for_bot = "https://ibb.co/1YMH3PjL"
API_KEY = os.getenv("API_KEY")
TOKEN = os.getenv("TOKEN")
DOMEN = os.getenv("DOMEN")
PORT = int(os.getenv("PORT", 8000))

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
