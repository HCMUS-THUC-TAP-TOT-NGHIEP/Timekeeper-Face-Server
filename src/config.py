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
    FE_URL = os.getenv("FE_URL")