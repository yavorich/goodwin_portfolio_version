from copy import copy
from inspect import currentframe


def f(s: str) -> str:
    # на другом проекте работал, здесь выдаёт ошибку
    frame = currentframe().f_back
    return eval(f"{s}", copy(frame.f_globals) | frame.f_locals)
