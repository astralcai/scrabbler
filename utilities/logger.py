import datetime


def info(message):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(now + " INFO: " + message)


def error(message):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(now + " ERROR: " + message)
