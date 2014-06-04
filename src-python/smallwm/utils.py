"""
Useful, general functions and constants used in various places throughout
SmallWM.
"""

# The maximum layer is 119, since:
#    User windows are [1, 109]
#    Dialogs are [110, 119]
MAX_LAYER = 119

def positive_int(text):
    """
    Converts a str into a positive int - if the str is not a valid number, or
    the int is not positive, this raises a ValueError.
    """
    value = int(text, 0)
    if value <= 0:
        raise ValueError
    return value
