"""Testing the obiwan module.

https://github.com/williame/obiwan

"""

from obiwan import *
install_obiwan_runtime_check()

def id1(x: int) -> int:
    """Identity

    >>> id1(2)
    Traceback (most recent call last):
        ...
    obiwan.ObiwanError: id1()-> is <class 'NoneType'> but should be <class 'int'>

    """
    return

def id2(x: int) -> int:
    """Identity

    >>> id2(2)
    2
    >>> id2(2.0)
    Traceback (most recent call last):
        ...
    obiwan.ObiwanError: id2(x) is <class 'float'> but should be <class 'int'>

    """
    return x

def sum1(a: int, b: int) -> int:
    """Sum

    >>> sum1(2, 2)
    4
    >>> sum1(2, 2.0)
    Traceback (most recent call last):
        ...
    obiwan.ObiwanError: sum1(b) is <class 'float'> but should be <class 'int'>

    """
    return a + b

def sum2(a: int, b: float) -> number:
    """Sum

    >>> sum2(2, 2)
    Traceback (most recent call last):
        ...
    obiwan.ObiwanError: sum2(b) is <class 'int'> but should be <class 'float'>

    """
    return a + b

import doctest
doctest.testmod()
