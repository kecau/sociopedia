import datetime
from datetimerange import DateTimeRange


def correct_time(time_str):
    if len(time_str) == 7:
        time_str += '-01 00:00'
    elif len(time_str) == 10:
        time_str += ' 00:00'
    elif len(time_str) == 13:
        time_str += ':00'

    return time_str


def get_time_range(start_time, end_time):
    time_range = DateTimeRange(start_time, end_time)
    count = 0
    for value in time_range.range(datetime.timedelta(hours=1)):
        count += 1
    return count - 1
