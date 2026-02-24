# src/checks/check.py
# Decorators for marking check functions

import inspect
from .raised import RaisedError

def check(func):
    """Decorator to mark a function as a check function."""
    if inspect.iscoroutinefunction(func):
        async def async_wrapper():
            try:
                await func()
                return True
            except RaisedError as e:
                return e
            except Exception as e:
                return RaisedError(str(e), hint="An unexpected exception occurred during the check.")
        async_wrapper.is_check = True
        async_wrapper.__name__ = func.__name__
        return async_wrapper
    else:
        def wrapper():
            try:
                func()
                return True
            except RaisedError as e:
                return e
            except Exception as e:
                return RaisedError(str(e), hint="An unexpected exception occurred during the check.")
        wrapper.is_check = True
        wrapper.__name__ = func.__name__
        return wrapper

