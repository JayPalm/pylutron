import time
from lutron import Lutron
from entities.lutron_entity import LutronEntity

from events import LutronEvent
from lutron_enum import BatteryStatus, PowerSource
from request_helper import _RequestHelper

from logger import _LOGGER


class MotionSensor(LutronEntity):
    """Placeholder class for the motion sensor device.
    Although sensors are represented in the XML, all of the protocol
    happens at the OccupancyGroup level. To read the state of an area,
    use area.occupancy_group.
    """

    _CMD_TYPE = "DEVICE"

    _ACTION_BATTERY_STATUS = 22

    class Event(LutronEvent):
        """MotionSensor events that can be generated.
        STATUS_CHANGED: Battery status changed
            Params:
              power: PowerSource
              battery: BatteryStatus
        Note that motion events are reported by OccupancyGroup, not individual
        MotionSensors.
        """

        STATUS_CHANGED = 1

    def __init__(self, lutron, name, integration_id, uuid):
        """Initializes the motion sensor object."""
        super(MotionSensor, self).__init__(lutron, name, uuid)
        self._integration_id = integration_id
        self._battery = None
        self._power = None
        self._lutron.register_id(MotionSensor._CMD_TYPE, self)
        self._query_waiters = _RequestHelper()
        self._last_update = None

    @property
    def id(self):
        """The integration id"""
        return self._integration_id

    def __str__(self):
        """Returns a pretty-printed string for this object."""
        return "MotionSensor {} Id: {} Battery: {} Power: {}".format(
            self.name, self.id, self.battery_status, self.power_source
        )

    def __repr__(self):
        """String representation of the MotionSensor object."""
        return str(
            {
                "motion_sensor_name": self.name,
                "id": self.id,
                "battery": self.battery_status,
                "power": self.power_source,
            }
        )

    @property
    def _update_age(self):
        """Returns the time of the last poll in seconds."""
        if self._last_update is None:
            return 1e6
        else:
            return time.time() - self._last_update

    @property
    def battery_status(self):
        """Returns the current BatteryStatus."""
        # Battery status won't change frequently but can't be retrieved for MONITORING.
        # So rate limit queries to once an hour.
        if self._update_age > 3600.0:
            ev = self._query_waiters.request(self._do_query_battery)
            ev.wait(1.0)
        return self._battery

    @property
    def power_source(self):
        """Returns the current PowerSource."""
        self.battery_status  # retrieved by the same query
        return self._power

    def _do_query_battery(self):
        """Helper to perform the query for the current BatteryStatus."""
        component_num = 1  # doesn't seem to matter
        return self._lutron.send(
            Lutron.OP_QUERY,
            MotionSensor._CMD_TYPE,
            self._integration_id,
            component_num,
            MotionSensor._ACTION_BATTERY_STATUS,
        )

    def handle_update(self, args):
        """Handle the specified action on this component."""
        if len(args) != 6:
            _LOGGER.debug(
                "Wrong number of args for MotionSensor update {}".format(len(args))
            )
            return False
        _, action, _, power, battery, _ = args
        action = int(action)
        if action != MotionSensor._ACTION_BATTERY_STATUS:
            _LOGGER.debug("Unknown action %d for motion sensor {}".format(self.name))
            return False
        self._power = PowerSource(int(power))
        self._battery = BatteryStatus(int(battery))
        self._last_update = time.time()
        self._query_waiters.notify()
        self._dispatch_event(
            MotionSensor.Event.STATUS_CHANGED,
            {"power": self._power, "battery": self._battery},
        )
        return True
