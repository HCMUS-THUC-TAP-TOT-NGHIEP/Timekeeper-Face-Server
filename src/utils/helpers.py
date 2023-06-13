from datetime import date, timedelta, datetime
import time
import os
from mimetypes import MimeTypes
import urllib


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def subtractTime(start_time, end_time) -> float:  # số phút
    delta = (datetime.combine(date.today(), end_time) -
             datetime.combine(date.today(), start_time)).total_seconds() / 60
    return delta


def GetDayOfWeek(date: datetime.date) -> str:
    try:
        number = date.isoweekday()
        if number == 1:
            return 'Thứ hai'
        if number == 2:
            return 'Thứ ba'
        if number == 3:
            return 'Thứ tư'
        if number == 4:
            return 'Thứ năm'
        if number == 5:
            return 'Thứ sáu'
        if number == 6:
            return 'Thứ bảy'
        if number == 7:
            return "Chủ nhật"
        return ""
    except Exception as ex:
        raise Exception(f"GetDayOfWeek({str(date)}) có exception.")


def DeleteFile(path: str, expire: datetime = None) -> True:
    try:
        delay = 1
        if not expire:
            os.remove(path)
        else:
            while datetime.now() < expire:
                time.sleep(delay)
            os.remove(path)
        return True
    except Exception as ex:
        print(f"DeleteFile exception: %s" % ex)
        return False


def get_mine_type(filename: str):
    mime = MimeTypes()
    try:
        url = urllib.pathname2url(filename)
        mime_type = mime.guess_type(url)
        return mime_type
    except Exception as ex:
        raise Exception("get_mine_type failed: %s" % ex)
