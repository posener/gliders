import re
from datetime import datetime


regex = re.compile(r'(\d\d)-(\d\d)-(\d{4}) (\d\d):00')
regex_month = re.compile(r'(\d\d)-(\d\d)-(\d{4})')


class InvalidDateFormatException(Exception):
    pass


def format(date):
    return format_month(date) + ' {date.hour:02d}:00'.format(date=date)


def parse(s):
    groups = regex.findall(s)
    if len(groups) == 0:
        raise InvalidDateFormatException()
    groups = groups[0]
    return datetime(day=int(groups[0]), month=int(groups[1]), year=int(groups[2]), hour=int(groups[3]))


def format_month(date):
    return '{date.day:02d}-{date.month:02d}-{date.year:04d}'.format(date=date)


def parse_month(s):
    groups = regex_month.findall(s)
    if len(groups) == 0:
        raise InvalidDateFormatException()
    groups = groups[0]
    return datetime(day=int(groups[0]), month=int(groups[1]), year=int(groups[2]), hour=12)
