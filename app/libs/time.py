from datetime import datetime, timezone, timedelta


def get_now_datetime():
  return datetime.now(timezone(timedelta(hours=8)))


def strf_datetime(time: datetime = get_now_datetime()):
  return datetime.strftime(time, "%y/%m/%d %H:%M:%S")


def strp_datetime(time_str: str):
  return datetime.strptime(
      time_str,
      "%y/%m/%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=8)))


def strf_time(time: datetime = get_now_datetime()):
  return datetime.strftime(time, "%H%M%S")


def strf_date(time: datetime = get_now_datetime()):
  return datetime.strftime(time, "%y%m%d")


def sleep(min=1, max=3):
  import time
  from random import randint

  time.sleep(randint(min, max))
