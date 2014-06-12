"""
Handles layer-related elements, including:

 - Adjusting windows as they are focused/unfocused
 - Moving windows up/down in the stacking order
 - Restacking the windows on a desktop.
"""
import functools

from smallwm import keyboard, utils

# Note that, before you try to understand, note that there are two concepts
# of what a layer is, exactly.
#
# The 'user' idea of a layer, is that there are 9 layers that they can use.
# Adjusting within these layers causes focused windows to appear above the
# other windows who share the same layer.
#
# SmallWM has a more granular concept, in that it measures layers on a scale
# of 1 to 119. 'User layers' are represented as 10, 20, 30, 40, and so on.
# Focusing behavior is accomplished by adding utils.FOCUS_OFFSET to the
# focused window and subtracting utils.FOCUS_OFFSET from the focused window
# when unfocusing it.

def bind_x_events(_):
    """
    Binds X events to particular functions.
    """

def bind_keys(key_events):
    """
    Binds keyboard events to particular functions.
    """
    key_events.register(keyboard.LAYER_ABOVE,
            functools.partial(utils.adjust_layer, offset=utils.INCR_LAYER))
    key_events.register(keyboard.LAYER_BELOW,
            functools.partial(utils.adjust_layer, offset=-utils.INCR_LAYER))
    key_events.register(keyboard.LAYER_TOP,
            functools.partial(set_layer, layer=utils.BOTTOM_LAYER))
    key_events.register(keyboard.LAYER_BOTTOM,
            functools.partial(set_layer, layer=utils.TOP_LAYER))

    for layer in range(1, 9 + 1):
        layer_action = getattr(keyboard, 'LAYER_' + str(layer))
        key_events.register(layer_action,
                functools.partial(set_layer, layer=utils.INCR_LAYER * layer))

def update_layers(wm):
    """
    Restacks all the visible windows according to their
    """
    windows = {}
    icons = []
    move_resize_placeholder = None

    for client in wm.client_data:
        window_data = wm.client_data[client]
        if utils.is_visible(wm, client):
            windows[client] = window_data.layer
        elif window_data.icon is not None:
            icons.append(window_data.icon.window)
        elif window_data.move_resize is not None:
            assert move_resize_placeholder == None
            move_resize_placeholder = window_data.move_resize.window

    stacked_windows = sorted(windows, key=lambda win: windows[win])
    for window in stacked_windows:
        window.raise_window()

    for icon in icons:
        icon.raise_window()

    if move_resize_placeholder is not None:
        move_resize_placeholder.raise_window()

def set_layer(wm, window, *, layer):
    """
    Sets the layer of a window, keeping in mind the offset caused by the
    focus.
    """
    current_layer = wm.client_data[window].layer
    layer_offset = current_layer % utils.INCR_LAYER
    wm.client_data[window].layer = layer + layer_offset
    wm.wm_state.update_desktops = True
