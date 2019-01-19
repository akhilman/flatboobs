
def unpack_kwargs(func):
    def wrapped(kwargs):
        return func(**kwargs)
    return wrapped
