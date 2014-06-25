"""
Useful, general functions and constants used in various places throughout
SmallWM.
"""

from Xlib import X

# These are the minimum and maximum layers which are made available to users
MIN_LAYER = 1
MAX_LAYER = 9

# The default layer for clients to appear at
DEFAULT_LAYER = 5

def positive_int(text):
    """
    Converts a str into a positive int - if the str is not a valid number, or
    the int is not positive, this raises a ValueError.
    """
    value = int(text, 0)
    if value <= 0:
        raise ValueError
    return value
