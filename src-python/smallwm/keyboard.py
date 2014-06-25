"""
A list of keyboard actions.

.. py:data:: NEXT_DESKTOP

    Displays the desktop after the current desktop.

.. py:data:: PREV_DESKTOP

    Displays the desktop before the current desktop.

.. py:data:: TOGGLE_STICK

    Makes a client sticky if it isn't, or non-sticky if it is.

.. py:data:: CLIENT_NEXT_DESKTOP

    Moves a client onto the next desktop.

.. py:data:: CLIENT_PREV_DESKTOP

    Moves a client onto the previous desktop.

.. py:data:: ICONIFY

    Hides a client and displays its icon.

.. py:data:: MAXIMIZE

    Resizes a client to take up the whole screen.

.. py:data:: REQUEST_CLOSE

    Requests that a client close, allowing it to show save dialogs and the like.

.. py:data:: FORCE_CLOSE

    Forcibly closes a client.

.. py:data:: SNAP_TOP
    
    Snaps a client to the top half of the screen.

.. py:data:: SNAP_BOTTOM

.. py:data:: SNAP_LEFT

.. py:data:: SNAP_RIGHT

.. py:data:: LAYER_ABOVE

    Moves a client up a layer.

.. py:data:: LAYER_BELOW

    Moves a client down a layer.

.. py:data:: LAYER_TOP

    Puts a client on top of all other clients.

.. py:data:: LAYER_BOTTOM

    Puts a client below all other clients.

.. py:data:: LAYER_1

.. py:data:: LAYER_2

.. py:data:: LAYER_3

.. py:data:: LAYER_4

.. py:data:: LAYER_5

.. py:data:: LAYER_6

.. py:data:: LAYER_7

.. py:data:: LAYER_8

.. py:data:: LAYER_9
"""
(CLIENT_NEXT_DESKTOP, CLIENT_PREV_DESKTOP, TOGGLE_STICK,
 NEXT_DESKTOP, PREV_DESKTOP,
 ICONIFY, MAXIMIZE,
 REQUEST_CLOSE, FORCE_CLOSE,
 SNAP_TOP, SNAP_BOTTOM, SNAP_LEFT, SNAP_RIGHT,
 LAYER_ABOVE, LAYER_BELOW, LAYER_TOP, LAYER_BOTTOM,
 LAYER_1, LAYER_2, LAYER_3, LAYER_4, LAYER_5,
 LAYER_6, LAYER_7, LAYER_8, LAYER_9,
 EXIT_WM) = range(27)
