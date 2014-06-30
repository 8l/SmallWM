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
class Stringifyable:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

X = Stringifyable("<X window>")
Y = Stringifyable("<Y window>")

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
        'x': 0, 'y': 0, 'width': 5, 'height': 5, 'border_width': 0}

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

    def test_visible(self):
        # First, ensure that the client is visible by default
        self.assertTrue(self.manager.is_visible(X))

        # Moving, resizing, or iconified windows should not be visible
        self.manager.start_moving(X)
        self.assertFalse(self.manager.is_visible(X))
        self.manager.stop_moving(X, Geometry())
        self.assertTrue(self.manager.is_visible(X))

        self.manager.start_resizing(X)
        self.assertFalse(self.manager.is_visible(X))
        self.manager.stop_resizing(X, Geometry())
        self.assertTrue(self.manager.is_visible(X))

        self.manager.iconify(X)
        self.assertFalse(self.manager.is_visible(X))
        self.manager.deiconify(X)
        self.assertTrue(self.manager.is_visible(X))

        # Windows on different desktops are not visible - ensure that this is
        # the case by first moving the current desktop, then by moving the client
        self.manager.next_desktop()
        self.assertFalse(self.manager.is_visible(X))
        self.manager.prev_desktop()
        self.assertTrue(self.manager.is_visible(X))

        self.manager.prev_desktop()
        self.assertFalse(self.manager.is_visible(X))
        self.manager.next_desktop()
        self.assertTrue(self.manager.is_visible(X))

        self.manager.client_next_desktop(X)
        self.assertFalse(self.manager.is_visible(X))
        self.manager.client_prev_desktop(X)
        self.assertTrue(self.manager.is_visible(X))

        self.manager.client_prev_desktop(X)
        self.assertFalse(self.manager.is_visible(X))
        self.manager.client_next_desktop(X)
        self.assertTrue(self.manager.is_visible(X))

    def test_finder_functions(self):
        # Make sure that the `find_*` functions return proper results
        self.assertTrue(self.manager.is_client(X))
        self.assertEqual(self.manager.find_desktop(X), 1)
        self.assertEqual(self.manager.find_layer(X), 
            smallwm.utils.DEFAULT_LAYER)
      
        # Ensure that `is_client` returns False if a client doesn't exist, and
        # that the `find_*` methods raise KeyError
        self.manager.remove_client(X)
        self.assertFalse(self.manager.is_client(X))
        with self.assertRaises(KeyError):
            self.manager.find_desktop(X)

        with self.assertRaises(KeyError):
            self.manager.find_layer(X)

    def test_iter_functions(self):
        # Add another client on a different, so that the iterators have 
        # something to work from
        self.manager.next_desktop()

        hints = FakeHints()
        geometry = Geometry()
        self.manager.add_client(Y, hints, geometry)

        # Ensure that the desktop list shows only the new client, since the
        # desktop was switched before adding it
        clients = self.manager.get_visible_clients()
        self.assertEqual(clients, {Y})

        clients = self.manager.get_clients_of(
            self.manager.current_desktop)
        self.assertEqual(clients, {Y})

        layered_clients = list(self.manager.iter_by_layer())
        self.assertEqual(layered_clients, [Y])

        # Switch back and ensure that the desktop list shows the original client
        self.manager.prev_desktop()
        clients = self.manager.get_visible_clients()
        self.assertEqual(clients, {X})

        clients = self.manager.get_clients_of(
            self.manager.current_desktop)
        self.assertEqual(clients, {X})

        layered_clients = list(self.manager.iter_by_layer())
        self.assertEqual(layered_clients, [X])

        # Move the two onto the same desktop and ensure that the desktop list
        # shows them both.
        self.manager.client_prev_desktop(Y)
        clients = self.manager.get_visible_clients()
        self.assertEqual(clients, {X, Y})

        # Put X above Y and ensure that the proper order is returned
        self.manager.up_layer(X)
        layered_clients = list(self.manager.iter_by_layer())
        self.assertEqual(layered_clients, [Y, X])

        # Put Y above X
        self.manager.down_layer(X)
        self.manager.up_layer(Y)
        layered_clients = list(self.manager.iter_by_layer())
        self.assertEqual(layered_clients, [X, Y])

        # Stick Y, move to another desktop, and ensure that Y is still
        # listed as visible
        self.manager.toggle_stick(Y)
        self.manager.next_desktop()

        clients = self.manager.get_visible_clients()
        self.assertEqual(clients, {Y})

        clients = self.manager.get_clients_of(
            self.manager.current_desktop)
        # This is the case since `iter_desktop` gets only clients on 
        # a single desktop, ignoring DESKTOP_ALL
        self.assertEqual(clients, set())

        layered_clients = list(self.manager.iter_by_layer())
        self.assertEqual(layered_clients, [Y])

    def test_layer_set(self):
        new_layer = 8

        # Make sure that the client is on the original layer to start with
        self.assertEqual(self.manager.find_layer(X), smallwm.utils.DEFAULT_LAYER)

        self.manager.set_layer(X, new_layer)
        events = self.manager.flush_changes()

        # Ensure that the client is on the correct layer
        self.assertEqual(self.manager.find_layer(X), new_layer)

        # Ensure that the proper event has been raised
        self.assertEqual(events,
            [smallwm.client_data.ChangeLayer(X, new_layer)])

    def test_invalid_layer_set(self):
        # Ensure that an invalid layer raises an exception
        with self.assertRaises(ValueError):
            self.manager.set_layer(X, smallwm.utils.MAX_LAYER * 2)

    def test_move_up_at_top(self):
        # Move up the layer to the top, and ensure that the layer is changed
        self.manager.set_layer(X, smallwm.utils.MAX_LAYER)
        self.assertEqual(self.manager.find_layer(X), smallwm.utils.MAX_LAYER)
        self.assertEqual(self.manager.flush_changes(), 
            [smallwm.client_data.ChangeLayer(X, smallwm.utils.MAX_LAYER)])

        # Ensure that moving up at this point causes no changes
        self.manager.up_layer(X)
        self.assertEqual(self.manager.find_layer(X), smallwm.utils.MAX_LAYER)
        self.assertEqual(self.manager.flush_changes(), [])

    def test_move_down_at_bottom(self):
        # Move the client down to the lowest layer, and ensure that the layer
        # was changed
        self.manager.set_layer(X, smallwm.utils.MIN_LAYER)
        self.assertEqual(self.manager.find_layer(X), smallwm.utils.MIN_LAYER)
        self.assertEqual(self.manager.flush_changes(),
            [smallwm.client_data.ChangeLayer(X, smallwm.utils.MIN_LAYER)])

        # Move the client down and ensure that nothing changes
        self.manager.down_layer(X)
        self.assertEqual(self.manager.find_layer(X), smallwm.utils.MIN_LAYER)
        self.assertEqual(self.manager.flush_changes(), [])

    def test_layer_up(self):
        # Make sure that the original layer is correct
        self.assertEqual(self.manager.find_layer(X), 
            smallwm.utils.DEFAULT_LAYER)

        self.manager.up_layer(X)
        events = self.manager.flush_changes()
       
        # Ensure that the layer is now correct and that we got the correct
        # events
        self.assertEqual(self.manager.find_layer(X), 
            smallwm.utils.DEFAULT_LAYER + 1)
        self.assertEqual(events, 
            [smallwm.client_data.ChangeLayer(X, 
                smallwm.utils.DEFAULT_LAYER + 1)])

    def test_layer_down(self):
        # Ensure that the original layer is correct
        self.assertEqual(self.manager.find_layer(X), 
            smallwm.utils.DEFAULT_LAYER)

        self.manager.down_layer(X)
        events = self.manager.flush_changes()
       
        # Ensure that the layer is now correct and that we got the change event
        self.assertEqual(events, 
            [smallwm.client_data.ChangeLayer(X, 
                smallwm.utils.DEFAULT_LAYER - 1)])
        self.assertEqual(self.manager.find_layer(X), 
            smallwm.utils.DEFAULT_LAYER - 1)

    def test_client_next_desktop(self):
        # Ensure that the next desktop function works by cycling a window
        # through all the desktops
        focus = X
        desktop = 1
        for x in range(MAX_DESKTOPS * 2):
            # Ensure that we start off on the right desktop
            self.assertEqual(self.manager.find_desktop(X), desktop)

            self.manager.client_next_desktop(X)
            desktop += 1

            if desktop > MAX_DESKTOPS:
                desktop = 1

            if focus is X:
                # This is true only on the first iteration. The client was
                # focused when it was created, and so we should see the
                # following sequence of events.
                #
                # Note that the focus change comes *before* the desktop change,
                # since at no time do we ever want the focused window to not be
                # visible.
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeFocus(X, None),
                     smallwm.client_data.ChangeClientDesktop(X, desktop)])
                focus = None
            else:
                # On further iterations, no focus change ever occurs since
                # the window is never focused again.
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeClientDesktop(X,
                        desktop)])

    def test_client_prev_desktop(self):
        # This is directly symmetrical to `test_client_next_desktop`, so go
        # read that if you want an idea of what this does
        desktop = 1
        focus = X
        for x in range(MAX_DESKTOPS * 2):
            self.assertEqual(self.manager.find_desktop(X), desktop)

            self.manager.client_prev_desktop(X)
            desktop -= 1

            if desktop < 1:
                desktop += MAX_DESKTOPS

            if focus is X:
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeFocus(X, None),
                     smallwm.client_data.ChangeClientDesktop(X, desktop)])
                focus = None
            else:
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeClientDesktop(X,
                        desktop)])

    def test_client_desktop_invalid_states(self):
        # You cannot change the desktop of an invalid client
        with self.assertRaises(KeyError):
            self.manager.client_next_desktop(Y)

        with self.assertRaises(KeyError):
            self.manager.client_prev_desktop(Y)

        # Changing the desktop of an iconified client is invalid, since there is
        # no "next" after the iconified state
        self.manager.iconify(X)
        with self.assertRaises(ValueError):
            self.manager.client_next_desktop(X)

        with self.assertRaises(ValueError):
            self.manager.client_prev_desktop(X)
        self.manager.deiconify(X)

        # Applying the same reasoning to the above iconify case, you can't change
        # the desktop of a moving client or a resizing client
        self.manager.start_moving(X)
        with self.assertRaises(ValueError):
            self.manager.client_next_desktop(X)

        with self.assertRaises(ValueError):
            self.manager.client_prev_desktop(X)
        self.manager.stop_moving(X, Geometry())

        self.manager.start_resizing(X)
        with self.assertRaises(ValueError):
            self.manager.client_next_desktop(X)

        with self.assertRaises(ValueError):
            self.manager.client_prev_desktop(X)
        self.manager.stop_resizing(X, Geometry())

    def test_next_desktop(self):
        # `test_client_next_desktop` mirrors this almost exactly - go read the
        # comments there
        focus = X
        desktop = 1
        for x in range(MAX_DESKTOPS * 2):
            self.assertEqual(self.manager.current_desktop, desktop)
            
            self.manager.next_desktop()
            desktop += 1

            if desktop > MAX_DESKTOPS:
                desktop = 1

            if focus is X:
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeFocus(X, None),
                     smallwm.client_data.ChangeCurrentDesktop(desktop)])
                focus = None
            else:
                self.assertEqual(self.manager.flush_changes(),
                    [smallwm.client_data.ChangeCurrentDesktop(desktop)])

    def test_prev_desktop(self):
        # `test_client_next_desktop` mirrors this almost exactly - go read the
        # comments there
        focus = X
        desktop = 1
        for x in range(MAX_DESKTOPS * 2):
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
        # You can't change desktops while moving or resizing a window
        self.manager.start_moving(X)
        with self.assertRaises(ValueError):
            self.manager.next_desktop()

        with self.assertRaises(ValueError):
            self.manager.prev_desktop()
        self.manager.stop_moving(X, Geometry())

        self.manager.start_resizing(X)
        with self.assertRaises(ValueError):
            self.manager.next_desktop()

        with self.assertRaises(ValueError):
            self.manager.prev_desktop()
        self.manager.stop_resizing(X, Geometry())

    def test_iconify(self):
        self.manager.iconify(X)
       
        # Make sure that the order of events is correct - the focus change
        # must occur first, since we don't want the focus to be on an
        # iconified client
        self.assertEqual(self.manager.flush_changes(),
            [ smallwm.client_data.ChangeFocus(X, None), 
              smallwm.client_data.ChangeClientDesktop(X, 
                smallwm.client_data.DESKTOP_ICONS)])

        # Ensure that further queries put the client on the correct desktop
        self.assertEqual(self.manager.find_desktop(X), 
            smallwm.client_data.DESKTOP_ICONS)

        self.manager.deiconify(X)

        # The events here are in the reverse order - we can't focus first, since
        # the client is still iconified. So, it must be uniconified first.
        self.assertEqual(self.manager.flush_changes(),
            [smallwm.client_data.ChangeClientDesktop(X, 
                self.manager.current_desktop),
             smallwm.client_data.ChangeFocus(None, X)])

        # Ensure that further queries put the client on the correct desktop
        self.assertEqual(self.manager.find_desktop(X), 
            self.manager.current_desktop)

    def test_bad_iconify(self):
        # Trying to iconify nonexistent clients should raise exceptions
        with self.assertRaises(KeyError):
            self.manager.iconify(Y)

        with self.assertRaises(KeyError):
            self.manager.deiconify(Y)

        # Deiconifying non-iconified clients should raise exceptions
        with self.assertRaises(ValueError):
            self.manager.deiconify(X)

        # You can't iconify something that is being moved, since the client
        # that is being moved is not necessarily visible
        self.manager.start_moving(X)
        with self.assertRaises(ValueError):
            self.manager.iconify(X)
        self.manager.stop_moving(X, Geometry())

        # You can't iconify something that is being resized for the same reason
        self.manager.start_resizing(X)
        with self.assertRaises(ValueError):
            self.manager.iconify(X)
        self.manager.stop_resizing(X, Geometry())

    def test_moving(self):
        self.manager.start_moving(X)

        # You should be familiar with this order of events from previous
        # test-cases  - if not, read `test_iconify` to understand why the
        # order is important here.
        self.assertEqual(self.manager.flush_changes(),
            [smallwm.client_data.ChangeFocus(X, None), 
             smallwm.client_data.ChangeClientDesktop(X, 
                smallwm.client_data.DESKTOP_MOVING)])

        self.assertEqual(self.manager.find_desktop(X),
            smallwm.client_data.DESKTOP_MOVING)

        # Actually move the desktop, which only happens when the moving state
        # exits
        new_location = Geometry()
        new_location.x = 42
        new_location.y = 42
        self.manager.stop_moving(X, new_location)

        # The ordering, as usual, is significant. First, we have to make the
        # client visible. Only then can it be moved, and then focused.
        self.assertEqual(self.manager.flush_changes(),
            [smallwm.client_data.ChangeClientDesktop(X, 
                self.manager.current_desktop),
             smallwm.client_data.ChangeLocation(X, 42, 42),
             smallwm.client_data.ChangeFocus(None, X)])

        self.assertEqual(self.manager.find_desktop(X),
            self.manager.current_desktop)

    def test_bad_moving(self):
        # Moving a nonexistent client should raise exceptions
        with self.assertRaises(KeyError):
            self.manager.start_moving(Y)

        # You can't stop moving unless it was previously moving
        with self.assertRaises(ValueError):
            self.manager.stop_moving(X, Geometry())

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

        # You can't move a window while another is being resized
        self.manager.start_resizing(Y)
        with self.assertRaises(ValueError):
            self.manager.start_moving(X)
        self.manager.stop_resizing(Y, Geometry())

    def test_resizing(self):
        # Read `test_moving` to understand what this is testing for, since
        # this tests for the very same things
        self.manager.start_resizing(X)

        self.assertEqual(self.manager.flush_changes(),
            [smallwm.client_data.ChangeFocus(X, None), 
             smallwm.client_data.ChangeClientDesktop(X, 
                smallwm.client_data.DESKTOP_RESIZING)])

        self.assertEqual(self.manager.find_desktop(X),
            smallwm.client_data.DESKTOP_RESIZING)

        new_size = Geometry()
        new_size.width = 42
        new_size.height = 42
        self.manager.stop_resizing(X, new_size)

        self.assertEqual(self.manager.flush_changes(),
            [smallwm.client_data.ChangeClientDesktop(X, 
                self.manager.current_desktop),
             smallwm.client_data.ChangeSize(X, 42, 42),
             smallwm.client_data.ChangeFocus(None, X)])

        self.assertEqual(self.manager.find_desktop(X),
            self.manager.current_desktop)

    def test_bad_resizing(self):
        # Read `test_bad_moving` to understand what this does
        with self.assertRaises(KeyError):
            self.manager.start_resizing(Y)

        with self.assertRaises(ValueError):
            self.manager.stop_resizing(X, Geometry())

        self.manager.start_resizing(X)
        with self.assertRaises(ValueError):
            self.manager.start_resizing(X)
        self.manager.stop_resizing(X, Geometry())

        self.manager.iconify(X)
        with self.assertRaises(ValueError):
            self.manager.start_resizing(X)
        self.manager.deiconify(X)

        hints = FakeHints()
        geometry = Geometry()
        self.manager.add_client(Y, hints, geometry)

        self.manager.start_resizing(X)
        with self.assertRaises(ValueError):
            self.manager.start_resizing(Y)
        self.manager.stop_resizing(X, Geometry())

        self.manager.start_moving(Y)
        with self.assertRaises(ValueError):
            self.manager.start_resizing(X)
        self.manager.stop_moving(Y, Geometry())

    def test_stick(self):
        # First, ensure that the given window is visible at first
        self.assertTrue(self.manager.is_visible(X))

        # Next, move to the next desktop and make sure that it isn't visible.
        # Note that the focus change is unimportant to us, but we do have to
        # keep it in mind to avoid failing the test.
        self.manager.next_desktop()
        self.assertEqual(self.manager.flush_changes(),
            [smallwm.client_data.ChangeFocus(X, None),
             smallwm.client_data.ChangeCurrentDesktop(
                self.manager.current_desktop)])
        self.assertFalse(self.manager.is_visible(X))

        # Stick the client and make sure it regains its visibility
        self.manager.toggle_stick(X)
        self.assertEqual(self.manager.flush_changes(),
            [smallwm.client_data.ChangeClientDesktop(X, 
                smallwm.client_data.DESKTOP_ALL)])
        self.assertTrue(self.manager.is_visible(X))
        
        # Unstick the client and make sure it loses its visibility on
        # a different desktop
        self.manager.toggle_stick(X)
        old_desktop = self.manager.current_desktop
        self.manager.next_desktop()

        self.assertEqual(self.manager.flush_changes(),
            [smallwm.client_data.ChangeClientDesktop(X, 
                old_desktop),
             smallwm.client_data.ChangeCurrentDesktop(
                 self.manager.current_desktop)])
        self.assertFalse(self.manager.is_visible(X))

if __name__ == '__main__':
    unittest.main()
