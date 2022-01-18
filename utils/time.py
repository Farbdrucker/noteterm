import time


def format_time(formatting: str, t_epoch: float = None) -> str:
    return time.strftime(formatting, time.localtime(t_epoch))


def readable_time(t_epoch: float = None) -> str:
    return format_time("%y-%m-%dT%H-%M", t_epoch or time.time())


def hhmm(t_epoch: float = None) -> str:
    return format_time("%y-%m-%dT%H-%M", t_epoch or time.time())

