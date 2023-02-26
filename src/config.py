import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DEBUG = bool(os.environ.get("DEBUG"))
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS").lower() in ('true', '1', 't')
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL").lower() in ('true', '1', 't')
    CLIENT_URL = os.getenv("CLIENT_URL")
    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    TIME_TOKEN = int(os.getenv("TIME_TOKEN"))