import datetime as dt
from contextlib import contextmanager


@contextmanager
def slow_lock(lock, loop, delta):
    """
    Async lock context which releases the lock
    'delta' seconds after exiting the block.
    """
    try:
        yield lock
    finally:
        loop.call_later(delta, lock.release)


def utc_now():
    """
    Return the current datetime localised to utc.
    """
    ts = dt.datetime.utcnow()
    ts.replace(tzinfo=dt.timezone.utc)
    return ts
