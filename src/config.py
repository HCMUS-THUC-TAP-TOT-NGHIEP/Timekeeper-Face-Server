import os
class Config:
    SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://ntkhanh:NguyenTuanKhanh#1011@hcmus.postgres.database.azure.com/hcmus?sslmode=require'
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USERNAME = "nguyentuankhanhcqt@gmail.com"
    MAIL_PASSWORD = "kklbaxxqdhhoxgld"
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    FE_URL = "http://localhost:8080"
