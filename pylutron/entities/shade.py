from entities.output import Output
from lutron import Lutron


class Shade(Output):
    """This is the output entity for shades in Lutron universe."""

    _ACTION_RAISE = 2
    _ACTION_LOWER = 3
    _ACTION_STOP = 4

    def start_raise(self):
        """Starts raising the shade."""
        self._lutron.send(
            Lutron.OP_EXECUTE,
            Output._CMD_TYPE,
            self._integration_id,
            Output._ACTION_RAISE,
        )

    def start_lower(self):
        """Starts lowering the shade."""
        self._lutron.send(
            Lutron.OP_EXECUTE,
            Output._CMD_TYPE,
            self._integration_id,
            Output._ACTION_LOWER,
        )

    def stop(self):
        """Starts raising the shade."""
        self._lutron.send(
            Lutron.OP_EXECUTE,
            Output._CMD_TYPE,
            self._integration_id,
            Output._ACTION_STOP,
        )
