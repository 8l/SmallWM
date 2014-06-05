"""
Useful, general functions and constants used in various places throughout
SmallWM.
"""

# Values about how layers are managed
#    User windows are [1, 109]
#    Dialogs are [110, 119]
MIN_LAYER = 1
MAX_LAYER = 119

# These are different, since these are the highest and lowest layer that
# a window can be 'set' to (since 'setting' the layer keeps the focus offset
# intact)
BOTTOM_LAYER = 10
TOP_LAYER = 110

INCR_LAYER = 10
FOCUS_OFFSET = 5

def positive_int(text):
    """
    Converts a str into a positive int - if the str is not a valid number, or
    the int is not positive, this raises a ValueError.
    """
    value = int(text, 0)
    if value <= 0:
        raise ValueError
    return value

def is_visible(wm, window):
    """
    Determines whether or not a window should be visible.
    """
    raise NotImplementedError
