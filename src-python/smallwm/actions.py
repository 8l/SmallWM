"""
Represents actions to be done when a client is first mapped.
"""

from collections import namedtuple

Stick = namedtuple('Stick', [])
Maximize = namedtuple('Maximize', [])
SetLayer = namedtuple('SetLayer', ['layer'])
Snap = namedtuple('Snap', ['direction'])

# Directions that a window can be snapped in
(LEFT, RIGHT, BOTTOM, TOP) = range(4)
