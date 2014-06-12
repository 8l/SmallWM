"""
Useful, general functions and constants used in various places throughout
SmallWM.
"""

from Xlib import X

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
    client = wm.client_data[window]

    has_icon = client.icon is not None
    is_moved_resized = client.move_resize is not None
    if has_icon or is_moved_resized:
        return False

    if client.desktop == wm.wm_state.current_desktop:
        return True

    return False

def adjust_layer(wm, window, *, offset):
    """
    Adjusts the layer of a window, relative to where it already is.

    Note that this is in utils since the focus routines use it also.
    """
    current_layer = wm.client_data[window].layer
    current_layer += offset

    # Avoid needless adjustments, by allowing only valid adjustments to cause
    # restacking.
    if MIN_LAYER <= current_layer <= MAX_LAYER:
        wm.client_data[window].layer += offset
        wm.wm_state.update_layers = True

def unfocus(wm, window):
    """
    Removes the focus from a window.
    """
    wm_state = wm.wm_state
    window.configure(border_pixel=wm_state.white_pixel)
    window.grab_button(X.AnyButton, X.AnyModifier, False,
            X.ButtonPressMask | X.ButtonReleaseMask,
            X.GrabModeAsync, X.GrabModeAsync, None, None)

    adjust_layer(wm, window, offset=-INCR_LAYER)

def set_focus(wm, window):
    """
    Changes the input focus to the given window.
    """
    wm_state = wm.wm_state
    if wm_state.current_focus is not None:
        # Restore the grab on the previously focused window before changing
        # the focus to us
        unfocus(wm, window)

    attrs = window.get_attributes()
    if (attrs.win_class != Xlib.X.InputOnly
            and attrs.map_state == X.IsViewable):
        window.ungrab_button(X.AnyButton, X.AnyModifier)
        window.set_input_focus(X.RevertToNone, X.CurrentTime)

        # Assume that the focus transferred properly, and make the layer and
        # border changes (if not, we'll call unfocus() to fix these things)
        adjust_layer(wm, window, offset=INCR_LAYER)
        window.configure(border_pixel=wm_state.black_pixel)

        # Make sure that the focus transferred properly
        focus_state = wm_state.display.get_input_focus()
        if focus_state.focus != window:
            # If not, then nobody is focused
            unfocus(wm, window)
            wm_state.current_focus = None

    wm_state.update_layers = True
