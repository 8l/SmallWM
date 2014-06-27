"""
Declares the storage used for client data.

.. py:data:: DESKTOP_ALL

    Similar to :const:`DESKTOP_INVISIBLE`, but for use with windows that are
    displayed on every desktop.

.. py:data:: DESKTOP_ICONS

    Similar to :const:`DESKTOP_ICONS` -- each window that belongs to this
    desktop is iconified.

.. py:data:: DESKTOP_MOVING

    Similar to :const:`DESKTOP_MOVING` -- there can only ever be one or zero 
    windows on this desktop, and if there is a window, it is currently being
    moved. Note that this desktop and :const:`DESKTOP_RESIZING` are mutually
    exclusive -- if there is a window on one, then there cannot be a window
    on the other.

.. py:data:: DESKTOP_RESIZING

    Similar to :const:`DESKTOP_RESIZING`, but for the window which is currently
    being resized.
"""

from collections import namedtuple
from Xlib import Xutil

from smallwm import utils

DESKTOP_ALL = -2
DESKTOP_ICONS = -3
DESKTOP_MOVING = -4
DESKTOP_RESIZING = -5

VIRTUAL_DESKTOPS = {DESKTOP_ALL, DESKTOP_ICONS, DESKTOP_MOVING, 
    DESKTOP_RESIZING}
INVISIBLE_DESKTOPS = {DESKTOP_ICONS, DESKTOP_MOVING, DESKTOP_RESIZING}

class ChangeLayer(namedtuple('ChangeLayer', ['window', 'layer'])):
    """
    A notification that the layer of a client was changed.
    """

class ChangeFocus(namedtuple('ChangeSize', ['old', 'new'])):
    """
    A notification that the currently focused window was changed.
    """

class ChangeClientDesktop(namedtuple('ChangeDesktop', ['window', 'desktop'])):
    """
    A notification that the desktop of a client was changed.
    """

class ChangeCurrentDesktop(namedtuple('ChangeCurrentDesktop', ['desktop'])):
    """
    A notification that the current desktop was changed.
    """

class ChangeLocation(namedtuple('ChangeLocation', ['window', 'x', 'y'])):
    """
    A notification that the location of a window was changed.
    """

class ChangeSize(namedtuple('ChangeSize', ['window', 'width', 'height'])):
    """
    A notification that the size of a window was changed.
    """

class ClientData:
    """
    This structure holds data for every client that SmallWM manages.

    .. py:attribute:: layers

        A mapping between each numeric layer and set of windows which are
        on that layer.

    .. py:attribute:: desktops

        A mapping between each desktop and the windows contained on it.

    .. py:attribute:: focused

        The window which is currently focused, or ``None``.

    .. py:attribute:: current_desktop

        The current desktop which is now being displayed.

    .. py:attribute:: location

        A mapping between each window and its location.

    .. py:attribute:: size

        A mapping between each window and its size.

    .. py:attribute:: changes

        A list of changes that have occurred. Note that this is expected to be
        cleared each time to avoid having to handle the same changes more than
        once.
    """
    def __init__(self, wm_state):
        self.wm_state = wm_state
        self.changes = []
        self.current_desktop = 1

        self.layers = {
            layer: set() for layer in 
            range(utils.MIN_LAYER, utils.MAX_LAYER + 1)
        }

        self.desktops = {
            DESKTOP_ALL: set(),
            DESKTOP_ICONS: set(),
            DESKTOP_MOVING: set(),
            DESKTOP_RESIZING: set()
        }
        for desktop in range(1, wm_state.max_desktops + 1):
            self.desktops[desktop] = set()

        self.focused = None
        self.location = {}
        self.size = {}

    def push_change(self, change):
        """
        Pushes a change to the changes list.

        :param change: The change to add.
        """
        self.changes.append(change)

    def flush_changes(self):
        """
        Gets the currently queued changes, and then clear them.

        :return: A list of changes which have occurred.
        """
        changes = self.changes
        self.changes = []
        return changes

    def add_client(self, client, wm_hints, geometry):
        """
        Registers a new client, which will appear on the current desktop.

        :param client: The client window to add.
        :param Xlib.xobject.icccm.WMHints wm_hints: The hints given by the \
            window.
        :param Xlib.protocol.request.GetGeometry geometry: The location and \
            size of the window when it was created.
        """
        if not (wm_hints.flags & Xutil.StateHint):
            self.desktops[self.current_desktop].add(client)
            self.push_change(ChangeClientDesktop(client, 
                self.current_desktop))
        else:
            # Handle the client's request to have itself mapped as it wants
            if wm_hints.initial_state == Xutil.NormalState:
                self.desktops[self.current_desktop].add(client)
                self.push_change(ChangeClientDesktop(client, 
                    self.current_desktop))
            elif wm.hints.initial_state == Xutil.IconicState:
                self.desktops[DESKTOP_ICONS].add(client)
                self.push_change(ChangeClientDesktop(client, DESKTOP_ICONS))

        self.push_change(ChangeLayer(client, utils.DEFAULT_LAYER))
        self.layers[utils.DEFAULT_LAYER].add(client)

        self.location[client] = (geometry.x, geometry.y)
        self.size[client] = (geometry.width, geometry.height)

        self.focus(client)

    def remove_client(self, client):
        """
        Removes a client from the window manager. Note that this pushes out no
        events, since the only way this could be called is when the window is
        actually deleted, and at that point, nobody cares about those events.

        :param client: The client window to remove.
        """
        # You can't have a nonexistent window with the focus
        self.check_focus(client)

        client_desktop = self.find_desktop(client)
        self.desktops[client_desktop].remove(client)

        client_layer = self.find_layer(client)
        self.layers[client_layer].remove(client)

        del self.location[client]
        del self.size[client]

    def is_client(self, window):
        """
        Checks to see if a window is actually a client.
        
        :param window: The window to check.
        :return: ``True`` if the window is registered, ``False`` otherwise.
        """
        # Every client must have an associated desktop, whether it be 'real'
        # or 'virtual' (like DESKTOP_ALL or DESKTOP_ICON)
        try:
            self.find_desktop(window)
        except KeyError:
            return False
        else:
            return True

    def focus(self, client):
        """
        Focuses a client, and pushes a notification about this change.

        :param client: The client to focus.
        :raises ValueError: The client is not visible.
        :raises KeyError: The client is not known.
        """
        client_desktop = self.find_desktop(client)
        if client_desktop != self.current_desktop:
            # Cannot focus something that isn't visible
            raise ValueError('Cannot focus non-visible window')

        old_focus = self.focused
        self.focused = client
        self.push_change(ChangeFocus(old_focus, client))

    def check_focus(self, client):
        """
        Checks to see if the given client is currently focused.

        If it is, then it is unfocused.

        :param client: The client to check the focus of.
        :raises KeyError: The client is not known.
        """
        if not self.is_client(client):
            raise KeyError('The given client does not exist')

        if self.focused == client:
            self.unfocus()

    def unfocus(self):
        """
        Unfocuses the current client, whatever client that is.
        """
        if self.focused is not None:
            old_focus = self.focused
            self.focused = None
            self.push_change(ChangeFocus(old_focus, None))

    def find_desktop(self, client):
        """
        Finds the desktop which is inhabited by a client.

        :param client: The client to find.
        :return: The desktop that the client is on.
        :raises KeyError: If the client isn't listed in the desktop list.
        """
        for desktop, win_list in self.desktops.items():
            if client in win_list:
                return desktop

        raise KeyError('Could not find the desktop of a client')

    def find_layer(self, client):
        """
        Finds the layer which is inhabited by a client.

        :param client: The client to find.
        :return: The layer that the client is on.
        :raises KeyError: If the client isn't listed in the layer list.
        """
        for layer, win_list in self.layers.items():
            if client in win_list:
                return layer

        raise KeyError('Could not find the layer of a client')

    def up_layer(self, client):
        """
        Moves a client up one layer.

        :param client: The client window to move up.
        :raises KeyError: If the client is not known.
        """
        old_layer = self.find_layer(client)
        if old_layer < utils.MAX_LAYER:
            self.push_change(ChangeLayer(client, old_layer + 1))

            self.layers[old_layer].remove(client)
            self.layers[old_layer + 1].add(client)

    def down_layer(self, client):
        """
        Moves a client down one layer.

        :param client: The client window to move down.
        :raises KeyError: If the client is not known.
        """
        old_layer = self.find_layer(client)
        if old_layer > utils.MIN_LAYER:
            self.push_change(ChangeLayer(client, old_layer - 1))

            self.layers[old_layer].remove(client)
            self.layers[old_layer - 1].add(client)

    def set_layer(self, client, layer):
        """
        Sets the layer of a client.

        :param client: The client to set the layer of.
        :param int layer: The layer to set the client to.
        :raises ValueError: If the given layer is an invalid layer.
        :raises KeyError: If the client is not known.
        """ 
        if layer not in self.layers:
            raise ValueError('The layer {} is not a valid layer'.format(repr(layer)))

        old_layer = self.find_layer(client)
        if old_layer != layer:
            self.push_change(ChangeLayer(client, layer))

            self.layers[old_layer].remove(client)
            self.layers[layer].add(client)

    def client_next_desktop(self, client):
        """
        Moves a client to the desktop after the current desktop.

        :param client: The client to move.
        :raises KeyError: If the client is not known.
        """
        old_desktop = self.find_desktop(client)

        if old_desktop in VIRTUAL_DESKTOPS:
            # These are invalid desktops for a user to try to change from -
            # there are special methods which manage those desktops.
            raise ValueError('Cannot change from a special desktop')

        self.desktops[old_desktop].remove(client)
        if old_desktop + 1 in self.desktops:
            # We're not at the end
            self.desktops[old_desktop + 1].add(client)
            self.push_change(ChangeClientDesktop(client, old_desktop + 1))
        else:
            self.desktops[1].add(client)
            self.push_change(ChangeClientDesktop(client, 1))

        # A window which is now on a different desktop cannot be focused,
        # so unfocus it if necessary.
        self.check_focus(client)

    def client_prev_desktop(self, client):
        """
        Moves a client to the desktop before the current desktop.

        :param client: The client to move.
        :raises KeyError: If the client is not known.
        """
        old_desktop = self.find_desktop(client)

        if old_desktop in VIRTUAL_DESKTOPS:
            # These are invalid desktops for a user to try to change from -
            # there are special methods which manage those desktops.
            raise ValueError('Cannot change from a special desktop')

        self.desktops[old_desktop].remove(client)
        if old_desktop - 1 in self.desktops:
            # We're not at the beginning
            self.desktops[old_desktop - 1].add(client)
            self.push_change(ChangeClientDesktop(client, old_desktop - 1))
        else:
            self.desktops[self.wm_state.max_desktops].add(client)
            self.push_change(ChangeClientDesktop(client, 
                self.wm_state.max_desktops))

        # A window which is now on a different desktop cannot be focused,
        # so unfocus it if necessary.
        self.check_focus(client)

    def next_desktop(self):
        """
        Moves the current desktop ahead one.
        """
        if self.current_desktop == self.wm_state.max_desktops:
            self.current_desktop = 1
        else:
            self.current_desktop += 1

        self.push_change(ChangeCurrentDesktop(self.current_desktop))

        # Since the currently focused window is no longer visible, unfocus it
        self.unfocus()

    def prev_desktop(self):
        """
        Moves the current desktop back one.
        """
        if self.current_desktop == 1:
            self.current_desktop = self.wm_state.max_desktops
        else:
            self.current_desktop -= 1

        self.push_change(ChangeCurrentDesktop(self.current_desktop))

        # Since the currently focused window is no longer visible, unfocus it
        self.unfocus()

    def iconify(self, client):
        """
        Marks the client as an icon.

        :param client: The client to iconify.
        :raises ValueError: If the client cannot be iconified.
        :raises KeyError: If the client is not known.
        """
        old_desktop = self.find_desktop(client)

        if old_desktop == DESKTOP_ICONS:
            # This icon is already iconified
            raise ValueError('The client is already iconified')
        elif old_desktop in INVISIBLE_DESKTOPS:
            # You cannot iconfiy something that isn't visible, so this request
            # makes no sense
            raise ValueError('Cannot iconify hidden client')

        self.push_change(ChangeClientDesktop(client, DESKTOP_ICONS))
        self.desktops[old_desktop].remove(client)
        self.desktops[DESKTOP_ICONS].add(client)

        # If the newly iconified client *was* focused, it can't be any more
        self.check_focus(client)

    def deiconify(self, client):
        """
        Unmarks the client as an icon.

        :param client: The client to iconify.
        :raises ValueError: If the client is not already iconified.
        :raises KeyError: If the client is not known.
        """
        old_desktop = self.find_desktop(client)

        if old_desktop != DESKTOP_ICONS:
            raise ValueError('The client is not currently iconified')

        self.push_change(ChangeClientDesktop(client, self.current_desktop))
        self.desktops[DESKTOP_ICONS].remove(client)
        self.desktops[self.current_desktop].add(client)

        self.focus(client)
