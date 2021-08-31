from enum import Enum

# from pylutron.lutron import Lutron
from pylutron.entities.lutron_entity import LutronEntity
from pylutron.events import LutronEvent
from pylutron.request_helper import _RequestHelper


class OccupancyGroup(LutronEntity):
    """Represents one or more occupancy/vacancy sensors grouped into an Area."""

    _CMD_TYPE = "GROUP"
    _ACTION_STATE = 3

    class State(Enum):
        """Possible states of an OccupancyGroup."""

        OCCUPIED = 3
        VACANT = 4
        UNKNOWN = 255

    class Event(LutronEvent):
        """OccupancyGroup event that can be generated.
        OCCUPANCY: Occupancy state has changed.
            Params:
              state: an OccupancyGroup.State
        """

        OCCUPANCY = 1

    def __init__(self, lutron, group_number, uuid):
        super(OccupancyGroup, self).__init__(lutron, None, uuid)
        self._area = None
        self._group_number = group_number
        self._integration_id = None
        self._state = None
        self._query_waiters = _RequestHelper()

    def _bind_area(self, area):
        self._area = area
        self._integration_id = area.id
        self._lutron.register_id(OccupancyGroup._CMD_TYPE, self)

    @property
    def id(self):
        """The integration id"""
        return self._integration_id

    @property
    def group_number(self):
        """The OccupancyGroupNumber"""
        return self._group_number

    @property
    def name(self):
        """Return the name of this OccupancyGroup, which is 'Occ' plus the name of the area."""
        return "Occ {}".format(self._area.name)

    @property
    def state(self):
        """Returns the current occupancy state."""
        # Poll for the first request.
        if self._state == None:
            ev = self._query_waiters.request(self._do_query_state)
            ev.wait(1.0)
        return self._state

    def __str__(self):
        """Returns a pretty-printed string for this object."""
        return 'OccupancyGroup for Area "{}" Id: {} State: {}'.format(
            self._area.name, self.id, self.state.name
        )

    def __repr__(self):
        """Returns a stringified representation of this object."""
        return str({"area_name": self.area.name, "id": self.id, "state": self.state})

    def _do_query_state(self):
        """Helper to perform the actual query for the current OccupancyGroup state."""
        return self._lutron.send(
            # Lutron.OP_QUERY,
            self._lutron.OP_QUERY,
            OccupancyGroup._CMD_TYPE,
            self._integration_id,
            OccupancyGroup._ACTION_STATE,
        )

    def handle_update(self, args):
        """Handles an event update for this object, e.g. occupancy state change."""
        action = int(args[0])
        if action != OccupancyGroup._ACTION_STATE or len(args) != 2:
            return False
        try:
            self._state = OccupancyGroup.State(int(args[1]))
        except ValueError:
            self._state = OccupancyGroup.State.UNKNOWN
        self._query_waiters.notify()
        self._dispatch_event(OccupancyGroup.Event.OCCUPANCY, {"state": self._state})
        return True
