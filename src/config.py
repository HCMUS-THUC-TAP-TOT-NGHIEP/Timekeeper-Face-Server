import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URI')
    MAIL_PORT = int(os.getenv('MAIL_PORT'))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS =bool(os.getenv('MAIL_USE_TLS'))
    MAIL_USE_SSL = bool(os.getenv('MAIL_USE_SSL'))
    FE_URL = os.getenv('FE_URL')
