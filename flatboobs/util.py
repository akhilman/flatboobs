# pylint: disable=missing-docstring


def apply(func, args):
    return func(*args)


def applykw(func, kwargs):
    return func(**kwargs)
