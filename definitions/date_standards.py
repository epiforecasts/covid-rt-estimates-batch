import datetime

dt = datetime.datetime.today()
DAY_OF_MONTH = dt.day
DAY_OF_WEEK = dt.strftime('%A')
DATETIME_NOWISH = datetime.datetime.now().strftime("%Y%m%dT%H%M")
DAILY = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
         21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
EVEN_DAYS = list(filter(lambda x: x % 2 == 0, DAILY))
ODD_DAYS = list(filter(lambda x: x % 2 == 1, DAILY))
MONTHLY = [1]
BI_MONTHLY = [2, 16]  # offset by +1 to avoid conflict
QUAD_MONTHlY = [3, 10, 17, 25]  # offset by +2
