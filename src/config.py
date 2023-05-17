import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    FLASK_DEBUG = bool(os.environ.get("DEBUG"))
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS").lower() in ("true", "1", "t")
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL").lower() in ("true", "1", "t")
    CLIENT_URL = os.getenv("CLIENT_URL")
    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("TIME_TOKEN"))
    JWT_ALGORITHM = (
        os.getenv("JWT_ALGORITHM") if os.getenv("JWT_ALGORITHM") else "HS256"
    )
    JSON_AS_ASCII = False
    LOG_TYPE = os.getenv("LOG_TYPE") if os.getenv("LOG_TYPE") else "stream"
    LOG_LEVEL = os.getenv("LOG_LEVEL") if os.getenv("LOG_LEVEL") else "INFO"
    LOG_DIR = os.getenv("LOG_DIR") if os.getenv("LOG_DIR") else ""
    APP_LOG_NAME = os.getenv("APP_LOG_NAME") if os.getenv(
        "APP_LOG_NAME") else "log.log"

    RAW_PATH = "./public/datasets/raw"
    LOCAL_STORAGE = "./public/datasets/raw"
    TRAIN_PATH = "./public/datasets/processed"
    HAARCASCADEPATH = "./public/static/haarcascade_frontalface_default.xml"
    PATH_MODEL_TRAIN = "./public/static/Trainner.yml"

    EXCELTEMPLATEPATH = '../public/templates/Excel'

    # region GG Drive Api
    CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH") if os.getenv(
        "CREDENTIALS_PATH") else "./public/gg_drive/credentials.json"
    TOKEN_PATH = os.getenv("TOKEN_PATH") if os.getenv(
        "TOKEN_PATH") else "./public/gg_drive/token.json"

    # endregion
