from entities.lutron_entity import LutronEntity
from logger import _LOGGER


class KeypadComponent(LutronEntity):
    """Base class for a keypad component such as a button, or an LED."""

    def __init__(self, lutron, keypad, name, num, component_num, uuid):
        """Initializes the base keypad component class."""
        super(KeypadComponent, self).__init__(lutron, name, uuid)
        self._keypad = keypad
        self._num = num
        self._component_num = component_num

    @property
    def number(self):
        """Returns the user-friendly number of this component (e.g. Button 1,
        or LED 1."""
        return self._num

    @property
    def component_number(self):
        """Return the lutron component number, which is referenced in commands and
        events. This is different from KeypadComponent.number because this property
        is only used for interfacing with the controller."""
        return self._component_num

    def handle_update(self, action, params):
        """Handle the specified action on this component."""
        _LOGGER.debug(
            'Keypad: "%s" Handling "%s" Action: %s Params: %s"'
            % (self._keypad.name, self.name, action, params)
        )
        return False
