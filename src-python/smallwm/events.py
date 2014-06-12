"""
All of the event handlers used in SmallWM, and their base event.
"""

from collections import defaultdict

class Dispatch:
    """
    An event dispatching mechanism, which can either be used as an event loop
    (where events are read and dispatched upon automatically) or as an event
    dispatcher (where events are provided from the outside, and only the
    dispatching is automatic).

    For the first case, consider the following example:
    >>> class X(Dispatch):
    ...     def get_next_event(self):
    ...         # Note that the second argument is a list, because the elements
    ...         # are unpacked and passed as *args
    ...         return event_type, [event_arguments]
    ...
    >>> x = X()
    >>> x.register('event-1', func_a)
    >>> x.register('event-2', func_b)
    >>> x.run()

    For the second case, consider this example instead:
    >>> x = Dispatcher()
    >>> x.register('event-1', func_a)
    >>> x.register('event-2', func_b)
    >>> x.dispatch('event-1', some, data) # Calls func_a(some, data)
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
        self._dispatch(next_event, event_params)
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

    def _dispatch(self, event, data):
        """
        Does dispatching directly on an event and a list of data.
        """
        for callback in self.events[event]:
            callback(*data)

    def dispatch(self, event, *data):
        """
        Dispatches on an event, calling all the necessary handlers.
        """
        self._dispatch(event, data)

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
