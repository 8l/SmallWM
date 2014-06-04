"""
Useful, general functions and constants used in various places throughout
SmallWM.
"""

# The maximum layer is 119, since:
#    User windows are [1, 109]
#    Dialogs are [110, 119]
MAX_LAYER = 119

# The properties that are stored for each client
(CD_DESKTOP, # The current desktop of the client
 CD_STICKY, # Whether the client is sticky or not
 CD_LAYER, # The current stacking layer of the client
 CD_STATE, # The currents state of the client
 CD_ICON, # The icon state of the clientA
) = range(5)

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
