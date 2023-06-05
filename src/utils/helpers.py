from datetime import date, timedelta, datetime
import time
import os

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def subtractTime(start_time, end_time) -> float: # số phút
    delta = (datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)).total_seconds() / 60
    return delta

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