"""
Represents actions to be done when a client is first mapped.
"""

from collections import namedtuple

class Stick(namedtuple('Stick', [])):
    """
    This action indicates that a client should be visible on all desktops.
    """

class Maximize(namedtuple('Maximize', [])):
    """
    This action indicates that a client should take up the entire screen.
    """

class SetLayer(namedtuple('SetLayer', ['layer'])):
    """
    This action indicates that a client should have a particular location in 
    the stacking order.

    .. py:attribute layer

        The layer to put the client on. Note that this is a logical layer, and
        thus must be from [1,9].
    """

class Snap(namedtuple('Snap', ['direction'])):
    """
    This action indicates that a client should be snapped to a particular half
    of the screen.

    .. py:attribute direction
        
        The side of the screen to snap the client towards.

    .. py:attribute LEFT
        
        Snap a client to the left half of the screen.

    .. py:attribute RIGHT
        
        Snap a client to the right half of the screen.

    .. py:attribute BOTTOM

        Snap a client to the bottom half of the screen.

    .. py:attribute TOP
        
        Snap a client to the top half of the screen.
    """
    (LEFT, RIGHT, BOTTOM, TOP) = range(4)
