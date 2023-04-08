from logging.config import dictConfig
from flask import has_request_context, request, current_app as app
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

logger = logging.getLogger()


class LogFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None
        return super().format(record)


logFormatter = LogFormatter(
    "[%(asctime)s] %(remote_addr)s requested %(url)s\n"
    "%(levelname)s in %(module)s: %(message)s \n"
    "---------------------------------------------------------------\n\n",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# add file handler to the root logger
# fileHandler = RotatingFileHandler("log.log", backupCount=100, maxBytes=1024 * 1024, encoding="utf-8")
# fileHandler.setFormatter(logFormatter)

fileHandler = TimedRotatingFileHandler("log.log", when="D", backupCount=3,)
fileHandler.setFormatter(logFormatter)
fileHandler.suffix = "%Y-%m-%d"