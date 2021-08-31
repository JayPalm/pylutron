from pylutron.entities import LutronEntity
from pylutron.events import LutronEvent
from pylutron.lutron import Lutron
from pylutron.logger import _LOGGER


class Output(LutronEntity):
    """This is the output entity in Lutron universe. This generally refers to a
    switched/dimmed load, e.g. light fixture, outlet, etc."""

    _CMD_TYPE = "OUTPUT"
    _ACTION_ZONE_LEVEL = 1

    class Event(LutronEvent):
        """Output events that can be generated.

        LEVEL_CHANGED: The output level has changed.
            Params:
              level: new output level (float)
        """

        LEVEL_CHANGED = 1

    def __init__(self, lutron, name, watts, output_type, integration_id, uuid):
        """Initializes the Output."""
        super(Output, self).__init__(lutron, name, uuid)
        self._watts = watts
        self._output_type = output_type
        self._level = 0.0
        self._query_waiters = _RequestHelper()
        self._integration_id = integration_id

        self._lutron.register_id(Output._CMD_TYPE, self)

    def __str__(self):
        """Returns a pretty-printed string for this object."""
        return 'Output name: "%s" watts: %d type: "%s" id: %d' % (
            self._name,
            self._watts,
            self._output_type,
            self._integration_id,
        )

    def __repr__(self):
        """Returns a stringified representation of this object."""
        return str(
            {
                "name": self._name,
                "watts": self._watts,
                "type": self._output_type,
                "id": self._integration_id,
            }
        )

    @property
    def id(self):
        """The integration id"""
        return self._integration_id

    def handle_update(self, args):
        """Handles an event update for this object, e.g. dimmer level change."""
        _LOGGER.debug("handle_update %d -- %s" % (self._integration_id, args))
        state = int(args[0])
        if state != Output._ACTION_ZONE_LEVEL:
            return False
        level = float(args[1])
        _LOGGER.debug(
            "Updating %d(%s): s=%d l=%f"
            % (self._integration_id, self._name, state, level)
        )
        self._level = level
        self._query_waiters.notify()
        self._dispatch_event(Output.Event.LEVEL_CHANGED, {"level": self._level})
        return True

    def __do_query_level(self):
        """Helper to perform the actual query the current dimmer level of the
        output. For pure on/off loads the result is either 0.0 or 100.0."""
        self._lutron.send(
            Lutron.OP_QUERY,
            Output._CMD_TYPE,
            self._integration_id,
            Output._ACTION_ZONE_LEVEL,
        )

    def last_level(self):
        """Returns last cached value of the output level, no query is performed."""
        return self._level

    @property
    def level(self):
        """Returns the current output level by querying the remote controller."""
        ev = self._query_waiters.request(self.__do_query_level)
        ev.wait(1.0)
        return self._level

    @level.setter
    def level(self, new_level):
        """Sets the new output level."""
        if self._level == new_level:
            return
        self._lutron.send(
            Lutron.OP_EXECUTE,
            Output._CMD_TYPE,
            self._integration_id,
            Output._ACTION_ZONE_LEVEL,
            "%.2f" % new_level,
        )
        self._level = new_level

    # At some later date, we may want to also specify fade and delay times
    # def set_level(self, new_level, fade_time, delay):
    #     self._lutron.send(
    #         Lutron.OP_EXECUTE,
    #         Output._CMD_TYPE,
    #         Output._ACTION_ZONE_LEVEL,
    #         new_level,
    #         fade_time,
    #         delay,
    #     )

    @property
    def watts(self):
        """Returns the configured maximum wattage for this output (not an actual
        measurement)."""
        return self._watts

    @property
    def type(self):
        """Returns the output type. At present AUTO_DETECT or NON_DIM."""
        return self._output_type

    @property
    def is_dimmable(self):
        """Returns a boolean of whether or not the output is dimmable."""
        return self.type != "NON_DIM" and not self.type.startswith("CCO_")
