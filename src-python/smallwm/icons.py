"""
Manages how icons are drawn, and what happens when they are clicked on.
"""

from Xlib import X
from smallwm import keyboard, structs, utils

def bind_x_events(x_events):
    """
    Binds X events to particular functions.
    """
    x_events.register(X.ButtonPress, remove_icon)
    x_events.register(X.Expose, redraw_icon)

def bind_keys(key_events):
    """
    Binds keyboard events to particular functions.
    """
    key_events.register(keyboard.ICONIFY, make_icon)

def get_client_of_icon(wm, icon):
    """
    Finds out which client is associated with a given icon.
    """
    for window, client in wm.client_data.items():
        if client.icon is not None and client.icon.window == icon:
            return window, client

    return None, None

def reflow_icons(wm):
    """
    Takes all the clients which have icons, and arranges their icons.

    This is done in a group of horizontal rows, stretching from the left to the
    right of each row.
    """
    x = 0
    y = 0
    x_incr = wm.wm_config.icon_width
    y_incr = wm.wm_config.icon_height
    screen_width = wm.wm_state.screen_width

    for client in wm.client_data:
        if client.icon is not None:
            # Move the icon's window to the current position
            icon_win = client.icon.window
            icon_win.configure(x=x, y=y)

            # Move the current position over, and down if we've hit the edge
            # of the screen
            x += x_incr
            if x >= screen_width:
                x = 0
                y += y_incr

def redraw_icon(wm, event):
    """
    Draws the icon specified by the given event.
    """
    icon_window = event.window
    wm_config = wm.wm_config
    client_window, client_data = get_client_of_icon(wm, icon_window)

    if client_window is None:
        return

    icon = client_data.icon
    icon_pixmap = icon.pixmap

    # Gets the client's preferred icon text, or failing that, falls back
    # upon the client's main name
    icon_name = (client_window.get_wm_icon_name() or
        client_window.get_wm_name())

    # Calculate how far left to draw the text
    text_offset = 0 if icon_pixmap is not None else icon.pix_width

    icon_window.clear_area(width=wm_config.icon_width,
            height=wm_config.icon_height)

    # Draw the pixmap (if the window provided one) and the icon name (if the
    # window provided one)
    if icon_pixmap is not None:
        icon_window.copy_area(icon_pixmap,
                0, 0, icon.pix_width, icon.pix_height,
                0, 0)

    if icon_name:
        icon_window.image_text(icon.gc,
                text_offset, wm_config.icon_height, icon_name)

def make_icon(wm, window):
    """
    Creates an icon for a particular window.
    """
    # Create and map the icon window without drawing it (that will be done
    # later)
    wm_state = wm.wm_state
    wm_config = wm.wm_config
    icon_window = wm_state.root.create_window(-200, -200,
        wm_config.icon_width, wm_config,
        1, wm_state.root.root_depth,
        background_pixel=wm_state.root.white_pixel,
        border_pixel=wm_state.root.black_pixel,
        event_mask=X.ExposureMask | X.ButtonPressMask | X.ButtonReleaseMask)
    icon_window.map()

    icon_gc = icon_window.create_gc(foreground=wm_state.root.white_pixel,
            background=wm_state.root.black_pixel)

    # Pre-set all these properties, in case we don't actually get a pixmap
    # back
    icon_pixmap = None
    icon_pixmap_width = 0
    icon_pixmap_height = 0

    # Check and see if there is a pixmap - and if there is, get it and its size
    hints = window.get_wm_hints()
    if wm_config.show_pixmaps and hints.pixmap.id != 0:
        icon_pixmap = hints.pixmap

        pixmap_geometry = icon_pixmap.get_geometry()
        icon_pixmap_width = pixmap_geometry.width
        icon_pixmap_height = pixmap_geometry.height

    icon = structs.Icon(icon_window, icon_gc,
        icon_pixmap, icon_pixmap_width, icon_pixmap_height)
    wm.client_data[window].icon = icon

    # Since we've added this new icon, we need to go ahead and position it
    # properly
    reflow_icons(wm)

def remove_icon(wm, event):
    """
    Removes an icon, and remaps the client of the icon.
    """
    icon_window = event.window
    client_window, client_data = get_client_of_icon(wm, icon_window)

    if client_window is None:
        return

    # Get rid of all the icon's resources
    icon = client_data.icon
    icon.window.destroy()
    icon.gc.free()
    client_data.icon = None

    # Show the client, and focus it
    client_window.map()
    utils.set_focus(wm, client_window)

    # Reposition all the remaining icons
    reflow_icons(wm)
