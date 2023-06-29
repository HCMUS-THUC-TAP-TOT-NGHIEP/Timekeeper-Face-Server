import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
load_dotenv()


isProduction = os.environ['MODE'] == 'production' if 'MODE' in os.environ else False


class Config:

    FLASK_APP = "app.py"
    FLASK_DEBUG = bool(os.environ.get("DEBUG"))
    SQLALCHEMY_DATABASE_URI = os.environ(
        "DATABASE_URI") if isProduction else os.getenv("DATABASE_URI")
    MAIL_SERVER = os.environ(
        "MAIL_SERVER") if isProduction else os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.environ("MAIL_PORT")) if isProduction else int(
        os.getenv("MAIL_PORT"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS").lower() in ("true", "1", "t")
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL").lower() in ("true", "1", "t")
    CLIENT_URL = os.getenv("CLIENT_URL")
    SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=(int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES")) if os.getenv("JWT_ACCESS_TOKEN_EXPIRES") else 60))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=(int(os.getenv(
        "REFRESH_TOKEN_EXPIRES")) if os.getenv("REFRESH_TOKEN_EXPIRES") else 24))
    REFRESH_TOKEN_BEFORE = timedelta(minutes=int(
        os.getenv("REFRESH_TOKEN_BEFORE"))if os.getenv("REFRESH_TOKEN_BEFORE") else 10)
    JWT_ALGORITHM = (
        os.getenv("JWT_ALGORITHM") if os.getenv("JWT_ALGORITHM") else "HS256"
    )
    JSON_AS_ASCII = False
    LOG_TYPE = os.getenv("LOG_TYPE") if os.getenv("LOG_TYPE") else "stream"
    LOG_LEVEL = os.getenv("LOG_LEVEL") if os.getenv("LOG_LEVEL") else "INFO"
    LOG_DIR = os.getenv("LOG_DIR") if os.getenv("LOG_DIR") else ""
    APP_LOG_NAME = os.getenv("APP_LOG_NAME") if os.getenv(
        "APP_LOG_NAME") else "log.log"

    LOCAL_STORAGE = "./public/datasets"
    # HAARCASCADEPATH = "./public/static/haarcascade_frontalface_default.xml"
    # PATH_MODEL_TRAIN = "./public/static/Trainner.yml"
    # PATH_MODEL_FACENET = "./public/static/facenet_keras_weights.h5"
    PATH_ENCODE = "./public/static/faces_embeddings.npz"
    PATH_MODEL = "./public/static/svm_model.pkl"

    EXCELTEMPLATEPATH = '../public/templates/Excel'

    # region GG Drive Api
    CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH") if os.getenv(
        "CREDENTIALS_PATH") else "../public/gg_drive/credentials.json"
    TOKEN_PATH = os.getenv("TOKEN_PATH") if os.getenv(
        "TOKEN_PATH") else "../public/gg_drive/token.json"

    DRIVE_FOLDER_ID = os.getenv("CHECKIN_LOG_IMAGES_FOLDER") if os.getenv(
        "CHECKIN_LOG_IMAGES_FOLDER") else '1fusOVodaDiSZ0UtwXn_v251gG8oMwCln'
    # endregion
