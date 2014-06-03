"""
A generic event dispatcher, which supports multiple event types, and passing data
to event handlers.
"""

from collections import defaultdict

class Dispatch:
    """
    Dispatches on events.
    """
    def __init__(self):
        self.events = defaultdict(set)

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
            callback(data)
