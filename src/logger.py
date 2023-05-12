from logging.config import dictConfig
from flask import has_request_context, request, current_app as app
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import time
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


class EnhancedRotatingFileHandler(TimedRotatingFileHandler, RotatingFileHandler):

    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None,
                 delay=0, when='h', interval=1, utc=False):
        logging.handlers.TimedRotatingFileHandler.__init__(
            self, filename=filename, when=when, interval=interval,
            backupCount=backupCount, encoding=encoding, delay=delay, utc=utc)

        logging.handlers.RotatingFileHandler.__init__(self, filename=filename, mode=mode, maxBytes=maxBytes,
                                                      backupCount=backupCount, encoding=encoding, delay=delay)

    def computeRollover(self, current_time):
        return logging.handlers.TimedRotatingFileHandler.computeRollover(self, current_time)

    def doRollover(self):
        # get from logging.handlers.TimedRotatingFileHandler.doRollover()
        current_time = int(time.time())
        dst_now = time.localtime(current_time)[-1]
        new_rollover_at = self.computeRollover(current_time)

        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval

        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dst_at_rollover = time.localtime(new_rollover_at)[-1]
            if dst_now != dst_at_rollover:
                if not dst_now:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                new_rollover_at += addend
        self.rolloverAt = new_rollover_at

        return logging.handlers.RotatingFileHandler.doRollover(self)

    def shouldRollover(self, record):
        return logging.handlers.TimedRotatingFileHandler.shouldRollover(self, record) or logging.handlers.RotatingFileHandler.shouldRollover(self, record)


logFormatter = LogFormatter(
    "[%(asctime)s] %(remote_addr)s requested %(url)s\n"
    "%(levelname)s in %(module)s: %(message)s \n"
    "---------------------------------------------------------------\n\n".encode(
        "utf-8"
    ).decode("utf-8"),
    datefmt="%Y-%m-%d %H:%M:%S",
)

# add file handler to the root logger
# fileHandler = RotatingFileHandler("log.log", backupCount=100, maxBytes=1024 * 1024, encoding="utf-8")
# fileHandler.setFormatter(logFormatter)

# fileHandler = TimedRotatingFileHandler(
#     "log.log", when="D", backupCount=3, encoding="utf-8"
# )
fileHandler = EnhancedRotatingFileHandler(
    filename="log.log", when="D", encoding="utf-8", backupCount=100, maxBytes=1024 * 1024,
)
fileHandler.setFormatter(logFormatter)
fileHandler.suffix = "%Y-%m-%d"
