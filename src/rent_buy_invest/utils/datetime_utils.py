import datetime


def get_time() -> str:
    return datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
