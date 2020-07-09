from functools import wraps


def tag(t: list):
    def _tag(func):
        func.tags = t
        return func
    return _tag


def level(l: int):
    def _level(func):
        func.level = l
        return func
    return _level


def order(o: int):
    def _order(func):
        func.order = o
        return func
    return _order


def rerun():
    pass


def times():
    pass


def datafile():
    pass


def csv():
    pass


def data():
    pass