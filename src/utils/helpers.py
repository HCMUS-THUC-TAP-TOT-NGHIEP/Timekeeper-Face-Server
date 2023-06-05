from datetime import date, timedelta, datetime
import time
import os

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def subtractTime(start_time, end_time) -> float: # số phút
    delta = (datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)).total_seconds() / 60
    return delta

def GetDayOfWeek(date: datetime.date) -> str:
    try:
        number = date.isoweekday()
        if date == 1:
            return 'Thứ hai'
        if date == 2:
            return 'Thứ ba'
        if date == 3:
            return 'Thứ tư'
        if date == 4:
            return 'Thứ năm'
        if date == 5:
            return 'Thứ sáu'
        if date == 6:
            return 'Thứ bảy'
        if date == 7:
            return 'Thứ hai'
    except Exception as ex:
        raise Exception(f"GetDayOfWeek({str(date)}) có exception.")

def DeleteFile(path: str, expire: datetime=None) -> True:
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