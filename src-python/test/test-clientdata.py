"""
Tests that the client data object produces valid transformations.
"""
import os
import sys
import unittest
from Xlib.xobject import icccm

# Ensure we can import smallwm
sys.path.append(os.path.join(*os.path.split(sys.path[0])[:-1]))

import smallwm.client_data, smallwm.structs, smallwm.utils

# A unique token which stands in as a client
X = object()
Y = object()

MAX_DESKTOPS = 5
class WMState(metaclass=smallwm.structs.Struct):
    __slots__ = ('max_desktops',)
    __defaults__ = {'max_desktops': MAX_DESKTOPS}

class FakeHints(metaclass=smallwm.structs.Struct):
    __slots__ = ('flags', 'input', 'initial_state', 'icon_pixmap', 'icon_window', 
            'icon_x', 'icon_y', 'icon_mask', 'window_group')
    __defaults__ = {'flags': 0, 'input': 0, 'initial_state': 0, 
        'icon_pixmap': 0, 'icon_window': 0, 'icon_x': 0, 'icon_y': 0,
        'icon_mask': 0, 'window_group': 0}

class Geometry(metaclass=smallwm.structs.Struct):
    __slots__ = ('depth', 'sequence_number', 'root', 
        'x', 'y', 'width', 'height', 'border_width')
    __defaults__ = {'depth': 0, 'sequence_number': 0, 'root': 0, 
        'x': 0, 'y': 0, 'width': 0, 'height': 0, 'border_width': 0}

class TestLayerManagement(unittest.TestCase):
    """
    Tests that the layer management functions operate upon client data properly.
    """
    def setUp(self):
        """
        Creates a client data manager.
        """
        wm_state = WMState()
        self.manager = smallwm.client_data.ClientData(wm_state)

        hints = FakeHints()
        geometry = Geometry()
        self.manager.add_client(X, hints, geometry)

        # Get rid of the excess events
        self.manager.flush_changes()

    def test_finder_functions(self):
        """
        Make sure that the find_* methods return proper values, and raise
        the proper exceptions.
        """
        self.assertTrue(self.manager.is_client(X))
        self.assertEqual(self.manager.find_desktop(X), 1)
        self.assertEqual(self.manager.find_layer(X), 
            smallwm.utils.DEFAULT_LAYER)
       
        self.manager.remove_client(X)
        self.assertFalse(self.manager.is_client(X))
        with self.assertRaises(KeyError):
            self.manager.find_desktop(X)

        with self.assertRaises(KeyError):
            self.manager.find_layer(X)

    def test_layer_set(self):
        """
        Sets the layer of a client.
        """
        new_layer = 8

        self.assertIn(X, self.manager.layers[smallwm.utils.DEFAULT_LAYER])
        self.assertNotIn(X, self.manager.layers[new_layer])

        self.manager.set_layer(X, new_layer)
        events = self.manager.flush_changes()

        self.assertIn(X, self.manager.layers[new_layer])
        self.assertNotIn(X, self.manager.layers[smallwm.utils.DEFAULT_LAYER])
        self.assertEqual(events,
            [smallwm.client_data.ChangeLayer(X, new_layer)])
        self.assertEqual(self.manager.find_layer(X), new_layer)

    def test_invalid_layer_set(self):
        """
        Sets an invalid layer.
        """
        with self.assertRaises(ValueError):
            self.manager.set_layer(X, 42)

    def test_move_up_at_top(self):
        """
        Moves a client to the top, and then make sure it can't move up anymore.
        """
        self.manager.set_layer(X, smallwm.utils.MAX_LAYER)
        self.assertIn(X, self.manager.layers[smallwm.utils.MAX_LAYER])
        self.assertEqual(self.manager.flush_changes(), 
            [smallwm.client_data.ChangeLayer(X, smallwm.utils.MAX_LAYER)])

        self.manager.up_layer(X)
        self.assertIn(X, self.manager.layers[smallwm.utils.MAX_LAYER])
        self.assertEqual(self.manager.flush_changes(), [])

    def test_move_down_at_bottom(self):
        """
        Moves a client to the bottom, and then make sure it can't move down anymore.
        """
        self.manager.set_layer(X, smallwm.utils.MIN_LAYER)
        self.assertIn(X, self.manager.layers[smallwm.utils.MIN_LAYER])
        self.assertEqual(self.manager.find_layer(X), smallwm.utils.MIN_LAYER)
        self.assertEqual(self.manager.flush_changes(),
            [smallwm.client_data.ChangeLayer(X, smallwm.utils.MIN_LAYER)])

        self.manager.down_layer(X)
        self.assertIn(X, self.manager.layers[smallwm.utils.MIN_LAYER])
        self.assertEqual(self.manager.flush_changes(), [])
        self.assertEqual(self.manager.find_layer(X), smallwm.utils.MIN_LAYER)

    def test_layer_up(self):
        """
        Moves the client a layer up, making sure that the:

         - Layer manager actually moves it up
         - Layer manager fires a ChangeLayer event
        """
        self.assertIn(X, self.manager.layers[smallwm.utils.DEFAULT_LAYER])
        self.assertNotIn(X, 
            self.manager.layers[smallwm.utils.DEFAULT_LAYER + 1])
        self.assertEqual(self.manager.find_layer(X), 
            smallwm.utils.DEFAULT_LAYER)

        self.manager.up_layer(X)
        events = self.manager.flush_changes()
        
        self.assertIn(X, 
            self.manager.layers[smallwm.utils.DEFAULT_LAYER + 1])
        self.assertNotIn(X, self.manager.layers[smallwm.utils.DEFAULT_LAYER])
        self.assertEqual(events, 
            [smallwm.client_data.ChangeLayer(X, 
                smallwm.utils.DEFAULT_LAYER + 1)])
        self.assertEqual(self.manager.find_layer(X), 
            smallwm.utils.DEFAULT_LAYER + 1)

    def test_layer_down(self):
        """
        Moves the client a layer down, making sure that the:

         - Layer manager actually moves it down
         - Layer manager fires a ChangeLayer event
        """
        self.assertIn(X, self.manager.layers[smallwm.utils.DEFAULT_LAYER])
        self.assertNotIn(X, self.manager.layers[
            smallwm.utils.DEFAULT_LAYER - 1])
        self.assertEqual(self.manager.find_layer(X), 
            smallwm.utils.DEFAULT_LAYER)

        self.manager.down_layer(X)
        events = self.manager.flush_changes()
        
        self.assertIn(X, 
            self.manager.layers[smallwm.utils.DEFAULT_LAYER - 1])
        self.assertNotIn(X, self.manager.layers[smallwm.utils.DEFAULT_LAYER])
        self.assertEqual(events, 
            [smallwm.client_data.ChangeLayer(X, 
                smallwm.utils.DEFAULT_LAYER - 1)])
        self.assertEqual(self.manager.find_layer(X), 
            smallwm.utils.DEFAULT_LAYER - 1)

    def test_client_next_desktop(self):
        """
        Moves the client through all desktops, starting at 1 and going ahead.
        """
        focus = X
        desktop = 1
        for x in range(25): # Some arbitrary number, > MAX_DESKTOPS
            self.assertEqual(self.manager.find_desktop(X), desktop)

            self.manager.client_next_desktop(X)
            desktop += 1

            if desktop > MAX_DESKTOPS:
                desktop = 1

            if focus is X:
                # Only the first iteration should change this, since X
                # was focused in the beginning
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeFocus(X, None),
                     smallwm.client_data.ChangeClientDesktop(X, desktop)])
                focus = None
            else:
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeClientDesktop(X,
                        desktop)])

    def test_client_prev_desktop(self):
        """
        Moves the client through all desktops, starting at 1 and going back.
        """
        desktop = 1
        focus = X
        for x in range(25):
            self.assertEqual(self.manager.find_desktop(X), desktop)

            self.manager.client_prev_desktop(X)
            desktop -= 1

            if desktop < 1:
                desktop += MAX_DESKTOPS

            if focus is X:
                # Only the first iteration should change this, since X
                # was focused in the beginning
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeFocus(X, None),
                     smallwm.client_data.ChangeClientDesktop(X, desktop)])
                focus = None
            else:
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeClientDesktop(X,
                        desktop)])

    def test_client_desktop_invalid_states(self):
        """
        Tests that moving a client to a different desktop, starting from an
        invalid desktop (for example, if the client is iconified) causes
        a ValueError.

        Also tests that moving nonexistent desktops causes a KeyError.
        """
        with self.assertRaises(KeyError):
            self.manager.client_next_desktop(Y)

        with self.assertRaises(KeyError):
            self.manager.client_prev_desktop(Y)

        # Changing the desktop of an iconified client is invalid
        self.manager.iconify(X)
        with self.assertRaises(ValueError):
            self.manager.client_next_desktop(X)

        with self.assertRaises(ValueError):
            self.manager.client_prev_desktop(X)

    def test_next_desktop(self):
        """
        Cycles through all the desktops, starting at 1 and going ahead.
        """
        focus = X
        desktop = 1
        for x in range(25): # An arbitrary number > MAX_DESKTOPS
            self.assertEqual(self.manager.current_desktop, desktop)
            
            self.manager.next_desktop()
            desktop += 1

            if desktop > MAX_DESKTOPS:
                desktop = 1

            if focus is X:
                # Only the first iteration should change this, since X
                # was focused in the beginning
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeFocus(X, None),
                     smallwm.client_data.ChangeCurrentDesktop(desktop)])
                focus = None
            else:
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeCurrentDesktop(desktop)])

    def test_prev_desktop(self):
        """
        Cycles through all the desktops, starting at 1 and going back.
        """
        focus = X
        desktop = 1
        for x in range(25): # An arbitrary number > MAX_DESKTOPS
            self.assertEqual(self.manager.current_desktop, desktop)
            
            self.manager.prev_desktop()
            desktop -= 1

            if desktop < 1:
                desktop += MAX_DESKTOPS

            if focus is X:
                # Only the first iteration should change this, since X
                # was focused in the beginning
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeFocus(X, None),
                     smallwm.client_data.ChangeCurrentDesktop(desktop)])
                focus = None
            else:
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeCurrentDesktop(desktop)])

    def test_bad_desktop_switch(self):
        """
        Runs through some scenarios where the desktop can't be changed, and
        ensure that exceptions are thrown.
        """
        # You can't change desktops while moving a window
        self.manager.start_moving(X)
        with self.assertRaises(ValueError):
            self.manager.next_desktop()
        self.manager.stop_moving(X, Geometry())

        self.manager.start_moving(X)
        with self.assertRaises(ValueError):
            self.manager.prev_desktop()
        self.manager.stop_moving(X, Geometry())

    def test_iconify(self):
        """
        Iconifies a window, and then ensure that it is iconified.
        
        And then deiconify it, and then ensure that it was deiconified.
        """
        self.manager.iconify(X)
        
        # Note the order of these events - the (un)focusing must happen before
        # a client goes to a different desktop (see below), but _after_ it 
        # gets back to the current one (see after `.deiconify()`)
        self.assertEqual(self.manager.flush_changes(),
            [ smallwm.client_data.ChangeFocus(X, None), 
              smallwm.client_data.ChangeClientDesktop(X, 
                smallwm.client_data.DESKTOP_ICONS)])
        self.assertEqual(self.manager.find_desktop(X), 
            smallwm.client_data.DESKTOP_ICONS)

        self.manager.deiconify(X)
        self.assertEqual(self.manager.flush_changes(),
            [smallwm.client_data.ChangeClientDesktop(X, 
                self.manager.current_desktop),
             smallwm.client_data.ChangeFocus(None, X)])
        self.assertEqual(self.manager.find_desktop(X), 
            self.manager.current_desktop)

    def test_bad_iconify(self):
        """
        Ensures that invalid attempts to iconify raise the appropriate 
        exceptions.
        """
        # Nonexistent clients raise KeyErrors
        with self.assertRaises(KeyError):
            self.manager.iconify(Y)

        with self.assertRaises(KeyError):
            self.manager.deiconify(Y)

        # Deiconifying non-iconified clients raises ValueErrors
        with self.assertRaises(ValueError):
            self.manager.deiconify(X)

        # You can't iconify something that is being moved
        self.manager.start_moving(X)
        with self.assertRaises(ValueError):
            self.manager.iconify(X)
        self.manager.stop_moving(X, Geometry())

    def test_moving(self):
        """
        Starts, and then stops, moving a window to make sure the correct
        events are handled.
        """
        self.manager.start_moving(X)
        self.assertEqual(self.manager.flush_changes(),
            [smallwm.client_data.ChangeFocus(X, None), 
             smallwm.client_data.ChangeClientDesktop(X, 
                smallwm.client_data.DESKTOP_MOVING)])
        self.assertEqual(self.manager.find_desktop(X),
            smallwm.client_data.DESKTOP_MOVING)

        new_location = Geometry()
        new_location.x = 42
        new_location.y = 42
        self.manager.stop_moving(X, new_location)

        self.assertEqual(self.manager.flush_changes(),
            [smallwm.client_data.ChangeClientDesktop(X, 
                self.manager.current_desktop),
             smallwm.client_data.ChangeLocation(X, 42, 42),
             smallwm.client_data.ChangeFocus(None, X)])
        self.assertEqual(self.manager.find_desktop(X),
            self.manager.current_desktop)

    def test_bad_moving(self):
        """
        Tests scenarios which are invalid, and ensures that exceptions are
        raised.
        """
        # You can't move a nonexistent client
        with self.assertRaises(KeyError):
            self.manager.start_moving(Y)

        # You can't move an already moving window
        self.manager.start_moving(X)
        with self.assertRaises(ValueError):
            self.manager.start_moving(X)
        self.manager.stop_moving(X, Geometry())

        # You can't move an iconified window
        self.manager.iconify(X)
        with self.assertRaises(ValueError):
            self.manager.start_moving(X)
        self.manager.deiconify(X)

        # You can't move two windows at once
        hints = FakeHints()
        geometry = Geometry()
        self.manager.add_client(Y, hints, geometry)

        self.manager.start_moving(X)
        with self.assertRaises(ValueError):
            self.manager.start_moving(Y)
        self.manager.stop_moving(X, Geometry())

if __name__ == '__main__':
    unittest.main()
