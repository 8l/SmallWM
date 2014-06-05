"""
Handles desktop-related elements, including:

 - Window stickiness
 - Computing which windows are visible on a given desktop
 - Changing the desktop of a window
"""
from Xlib import X
from smallwm import keyboard, layer, utils

def bind_x_events(_):
    """
    Binds X events to particular functions.

    (Here, this does nothing, but it is a required part of the module)
    """

def bind_keys(key_events):
    """
    Binds keyboard events to particular functions.
    """
    key_events.register(keyboard.CLIENT_NEXT_DESKTOP, client_next_desktop)
    key_events.register(keyboard.CLIENT_PREV_DESKTOP, client_prev_desktop)
    key_events.regsiter(keyboard.NEXT_DESKTOP, view_next_desktop)
    key_events.register(keyboard.PREV_DESKTOP, view_prev_desktop)
    key_events.register(keyboard.TOGGLE_STICK, flip_sticky_flag)

def update_desktop(wm):
    """
    Shows all windows which should be visible (likewise for hiding).
    """
    for client in wm.client_data:
        client_attributes = client.get_attributes()
        is_currently_visible = (client_attributes.map_state == X.IsViewable)

        # utils.is_visible is confusing here, just think of it as
        # "should be visible"
        if is_currently_visible and not utils.is_visible(wm, client):
            # Hide this client, since it shouldn't be visible but it is anyway
            client.unmap()
        elif not is_currently_visible and utils.is_visible(wm, client):
            # Show this client, since it isn't visible but should be
            client.map()

    layer.update_layers(wm)

def flip_sticky_flag(wm, window):
    """
    Flips the current 'stickiness' of a window.
    """
    old_visibility = utils.is_visible(wm, window)
    stickiness = wm.client_data[window].is_sticky
    wm.client_data[window].is_sticky = not stickiness

    # Only update the desktop here if we actually changed anything
    if utils.is_visible(wm, window) != old_visibility:
        update_desktop(wm)

def client_next_desktop(wm, window):
    """
    Moves a client to the next desktop.
    """
    max_desktops = wm.wm_config.max_desktops
    current_desktop = wm.client_data[window].desktop
    wm.client_data[window].desktop = (current_desktop + 1) % max_desktops
    update_desktop(wm)

def client_prev_desktop(wm, window):
    """
    Moves a client to the previous desktop.
    """
    max_desktops = wm.wm_config.max_desktops
    current_desktop = wm.client_data[window].desktop
    wm.client_data[window].desktop = (current_desktop - 1) % max_desktops
    update_desktop(wm)

def view_next_desktop(wm, _):
    """
    Updates the view to the next desktop.
    """
    max_desktops = wm.wm_config.max_desktops
    current_desktop = wm.wm_state.current_desktop
    wm.wm_state.current_desktop = (current_desktop + 1) % max_desktops
    update_desktop(wm)

def view_prev_desktop(wm, _):
    """
    Updates the view to the previous desktop.
    """
    max_desktops = wm.wm_config.max_desktops
    current_desktop = wm.wm_state.current_desktop
    wm.wm_state.current_desktop = (current_desktop - 1) % max_desktops
    update_desktop(wm)
