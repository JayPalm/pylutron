from typing import Dict

from events.lutron_event import LutronEvent, LutronEventHandler


class LutronEntity(object):
    """Base class for all the Lutron objects we'd like to manage. Just holds basic
    common info we'd rather not manage repeatedly."""

    def __init__(self, lutron, name, uuid):
        """Initializes the base class with common, basic data."""
        self._lutron = lutron
        self._name = name
        self._subscribers = []
        self._uuid = uuid

    @property
    def name(self):
        """Returns the entity name (e.g. Pendant)."""
        return self._name

    @property
    def uuid(self):
        return self._uuid

    def _dispatch_event(self, event: LutronEvent, params: Dict):
        """Dispatches the specified event to all the subscribers."""
        for handler, context in self._subscribers:
            handler(self, context, event, params)

    def subscribe(self, handler: LutronEventHandler, context):
        """Subscribes to events from this entity.

        handler: A callable object that takes the following arguments (in order)
                 obj: the LutrongEntity object that generated the event
                 context: user-supplied (to subscribe()) context object
                 event: the LutronEvent that was generated.
                 params: a dict of event-specific parameters

        context: User-supplied, opaque object that will be passed to handler.
        """
        self._subscribers.append((handler, context))

    def handle_update(self, args):
        """The handle_update callback is invoked when an event is received
        for the this entity.

        Returns:
          True - If event was valid and was handled.
          False - otherwise.
        """
        return False
