import inspect
import traceback

from asgiref.sync import sync_to_async
from django.core.exceptions import SynchronousOnlyOperation
from django.utils import timezone


def log_params(*args, separator):
    stack = traceback.extract_stack()[:-2]
    caller_frame = stack[-1]
    caller_filename = caller_frame.filename
    caller_lineno = caller_frame.lineno

    _now = timezone.localtime(timezone.now()).strftime("%H:%M %d.%m.%y")

    args_str = separator.join(str(arg) for arg in args)
    location_str = f"[{_now}:{caller_filename}:{caller_lineno}]"

    print(f"{args_str} {location_str}")


def printl(*args, separator=", "):
    log_params(*args, separator=separator)


async def async_str(obj):
    try:
        return str(obj)
    except SynchronousOnlyOperation:
        return await sync_to_async(obj.__str__)()


async def get_coroutine_caller_location():
    frame = inspect.currentframe().f_back.f_back
    return frame.f_code.co_filename, frame.f_lineno


async def alog_params(*args, location, separator):
    _now = timezone.localtime(timezone.now()).strftime("%H:%M %d.%m.%y")
    caller_filename, caller_lineno = location
    location_str = f"[{_now}:{caller_filename}:{caller_lineno}]"

    args_str = ""
    for arg in args:
        args_str = f"{args_str}{await async_str(arg)}{separator}"

    print(f"{args_str[:-len(separator)]} {location_str}")


async def aprintl(*args, separator=", "):
    location = await get_coroutine_caller_location()
    await alog_params(*args, location=location, separator=separator)
