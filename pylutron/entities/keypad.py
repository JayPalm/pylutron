from entities.lutron_entity import LutronEntity
from logger import _LOGGER


class Keypad(LutronEntity):
    """Object representing a Lutron keypad.

    Currently we don't really do much with it except handle the events
    (and drop them on the floor).
    """

    _CMD_TYPE = "DEVICE"

    def __init__(self, lutron, name, keypad_type, location, integration_id, uuid):
        """Initializes the Keypad object."""
        super(Keypad, self).__init__(lutron, name, uuid)
        self._buttons = []
        self._leds = []
        self._components = {}
        self._location = location
        self._integration_id = integration_id
        self._type = keypad_type

        self._lutron.register_id(Keypad._CMD_TYPE, self)

    def add_button(self, button):
        """Adds a button that's part of this keypad. We'll use this to
        dispatch button events."""
        self._buttons.append(button)
        self._components[button.component_number] = button

    def add_led(self, led):
        """Add an LED that's part of this keypad."""
        self._leds.append(led)
        self._components[led.component_number] = led

    @property
    def id(self):
        """The integration id"""
        return self._integration_id

    @property
    def name(self):
        """Returns the name of this keypad"""
        return self._name

    @property
    def type(self):
        """Returns the keypad type"""
        return self._type

    @property
    def location(self):
        """Returns the location in which the keypad is installed"""
        return self._location

    @property
    def buttons(self):
        """Return a tuple of buttons for this keypad."""
        return tuple(button for button in self._buttons)

    @property
    def leds(self):
        """Return a tuple of leds for this keypad."""
        return tuple(led for led in self._leds)

    def handle_update(self, args):
        """The callback invoked by the main event loop if there's an event from this keypad."""
        component = int(args[0])
        action = int(args[1])
        params = [int(x) for x in args[2:]]
        _LOGGER.debug(
            "Updating %d(%s): c=%d a=%d params=%s"
            % (self._integration_id, self._name, component, action, params)
        )
        if component in self._components:
            return self._components[component].handle_update(action, params)
        return False
