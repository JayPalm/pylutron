from pylutron.entities.keypad import Keypad
from pylutron.entities.keypad_component import KeypadComponent
from pylutron.events import LutronEvent

# from pylutron.lutron import Lutron


from pylutron.logger import _LOGGER


class Button(KeypadComponent):
    """This object represents a keypad button that we can trigger and handle
    events for (button presses)."""

    _ACTION_PRESS = 3
    _ACTION_RELEASE = 4

    class Event(LutronEvent):
        """Button events that can be generated.

        PRESSED: The button has been pressed.
            Params: None

        RELEASED: The button has been released. Not all buttons
                  generate this event.
            Params: None
        """

        PRESSED = 1
        RELEASED = 2

    def __init__(self, lutron, keypad, name, num, button_type, direction, uuid):
        """Initializes the Button class."""
        super(Button, self).__init__(lutron, keypad, name, num, num, uuid)
        self._button_type = button_type
        self._direction = direction

    def __str__(self):
        """Pretty printed string value of the Button object."""
        return 'Button name: "%s" num: %d type: "%s" direction: "%s"' % (
            self.name,
            self.number,
            self._button_type,
            self._direction,
        )

    def __repr__(self):
        """String representation of the Button object."""
        return str(
            {
                "name": self.name,
                "num": self.number,
                "type": self._button_type,
                "direction": self._direction,
            }
        )

    @property
    def button_type(self):
        """Returns the button type (Toggle, MasterRaiseLower, etc.)."""
        return self._button_type

    def press(self):
        """Triggers a simulated button press to the Keypad."""
        self._lutron.send(
            # Lutron.OP_EXECUTE,
            self._lutron.OP_EXECUTE,
            Keypad._CMD_TYPE,
            self._keypad.id,
            self.component_number,
            Button._ACTION_PRESS,
        )

    def release(self):
        """Triggers a simulated button release to the Keypad."""
        self._lutron.send(
            # Lutron.OP_EXECUTE,
            self._lutron.OP_EXECUTE,
            Keypad._CMD_TYPE,
            self._keypad.id,
            self.component_number,
            Button._ACTION_RELEASE,
        )

    def tap(self):
        """Triggers a simulated button tap to the Keypad."""
        self.press()
        self.release()

    def handle_update(self, action, params):
        """Handle the specified action on this component."""
        _LOGGER.debug(
            'Keypad: "%s" %s Action: %s Params: %s"'
            % (self._keypad.name, self, action, params)
        )
        ev_map = {
            Button._ACTION_PRESS: Button.Event.PRESSED,
            Button._ACTION_RELEASE: Button.Event.RELEASED,
        }
        if action not in ev_map:
            _LOGGER.debug(
                "Unknown action %d for button %d in keypad %s"
                % (action, self.number, self._keypad.name)
            )
            return False
        self._dispatch_event(ev_map[action], {})
        return True
