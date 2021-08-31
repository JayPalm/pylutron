# from pylutron.lutron import Lutron

from pylutron.entities.keypad import Keypad
from pylutron.entities.keypad_component import KeypadComponent


from pylutron.events import LutronEvent
from pylutron.request_helper import _RequestHelper
from pylutron.logger import _LOGGER


class Led(KeypadComponent):
    """This object represents a keypad LED that we can turn on/off and
    handle events for (led toggled by scenes)."""

    _ACTION_LED_STATE = 9

    class Event(LutronEvent):
        """Led events that can be generated.

        STATE_CHANGED: The button has been pressed.
            Params:
              state: The boolean value of the new LED state.
        """

        STATE_CHANGED = 1

    def __init__(self, lutron, keypad, name, led_num, component_num, uuid):
        """Initializes the Keypad LED class."""
        super(Led, self).__init__(lutron, keypad, name, led_num, component_num, uuid)
        self._state = False
        self._query_waiters = _RequestHelper()

    def __str__(self):
        """Pretty printed string value of the Led object."""
        return 'LED keypad: "%s" name: "%s" num: %d component_num: %d"' % (
            self._keypad.name,
            self.name,
            self.number,
            self.component_number,
        )

    def __repr__(self):
        """String representation of the Led object."""
        return str(
            {
                "keypad": self._keypad,
                "name": self.name,
                "num": self.number,
                "component_num": self.component_number,
            }
        )

    def __do_query_state(self):
        """Helper to perform the actual query for the current LED state."""
        self._lutron.send(
            # Lutron.OP_QUERY,
            self._lutron.OP_QUERY,
            Keypad._CMD_TYPE,
            self._keypad.id,
            self.component_number,
            Led._ACTION_LED_STATE,
        )

    @property
    def last_state(self):
        """Returns last cached value of the LED state, no query is performed."""
        return self._state

    @property
    def state(self):
        """Returns the current LED state by querying the remote controller."""
        ev = self._query_waiters.request(self.__do_query_state)
        ev.wait(1.0)
        return self._state

    @state.setter
    def state(self, new_state: bool):
        """Sets the new led state.

        new_state: bool
        """
        self._lutron.send(
            # Lutron.OP_EXECUTE,
            self._lutron.OP_EXECUTE,
            Keypad._CMD_TYPE,
            self._keypad.id,
            self.component_number,
            Led._ACTION_LED_STATE,
            int(new_state),
        )
        self._state = new_state

    def handle_update(self, action, params):
        """Handle the specified action on this component."""
        _LOGGER.debug(
            'Keypad: "%s" %s Action: %s Params: %s"'
            % (self._keypad.name, self, action, params)
        )
        if action != Led._ACTION_LED_STATE:
            _LOGGER.debug(
                "Unknown action %d for led %d in keypad %s"
                % (action, self.number, self._keypad.name)
            )
            return False
        elif len(params) < 1:
            _LOGGER.debug(
                "Unknown params %s (action %d on led %d in keypad %s)"
                % (params, action, self.number, self._keypad.name)
            )
            return False
        self._state = bool(params[0])
        self._query_waiters.notify()
        self._dispatch_event(Led.Event.STATE_CHANGED, {"state": self._state})
        return True
