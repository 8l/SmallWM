"""
All of the event handlers used in SmallWM, and their base event.
"""

from collections import defaultdict

class Dispatch:
    """
    Dispatches on events.
    """
    def __init__(self):
        self.events = defaultdict(set)
        self.terminated = False

    def get_next_event(self):
        """
        Gets a pair, (event_type, data), for the next event.
        """
        raise NotImplementedError

    def step(self):
        """
        Steps a single iteration, pumping just the next event.

        Returns True if the event loop is not terminated, or False if it is.
        """
        if self.terminated:
            return False

        next_event, event_params = self.get_next_event()
        self.dispatch(next_event, event_params)
        return True

    def run(self):
        """
        Runs the event loop, pumping events as they are received.
        """
        while self.step():
            pass

    def terminate(self):
        """
        Terminates the event loop.
        """
        self.terminated = True

    def register(self, event, callback):
        """
        Registers a callback on a particular event.
        """
        self.events[event].add(callback)

    def unregister(self, event, callback):
        """
        Unregisters a callback from a particular event.
        """
        self.events[event].remove(callback)

    def dispatch(self, event, data):
        """
        Dispatches on an event, calling all the necessary handlers.
        """
        for callback in self.events[event]:
            callback(*data)

class XEventDispatcher(Dispatch):
    """
    Dispatches on X events, received from an X display.
    """
    def __init__(self, wm):
        super().__init__()
        self.wm = wm

    def get_next_event(self):
        """
        Gets the next event to be pumped by the event loop.
        """
        event = self.wm.wm_state.display.next_event()
        return event.type, [wm, event]
