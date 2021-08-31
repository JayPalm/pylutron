class Area(object):
    """An area (i.e. a room) that contains devices/outputs/etc."""

    def __init__(self, lutron, name, integration_id, occupancy_group):
        self._lutron = lutron
        self._name = name
        self._integration_id = integration_id
        self._occupancy_group = occupancy_group
        self._outputs = []
        self._keypads = []
        self._sensors = []
        if occupancy_group:
            occupancy_group._bind_area(self)

    def add_output(self, output):
        """Adds an output object that's part of this area, only used during
        initial parsing."""
        self._outputs.append(output)

    def add_keypad(self, keypad):
        """Adds a keypad object that's part of this area, only used during
        initial parsing."""
        self._keypads.append(keypad)

    def add_sensor(self, sensor):
        """Adds a motion sensor object that's part of this area, only used during
        initial parsing."""
        self._sensors.append(sensor)

    @property
    def name(self):
        """Returns the name of this area."""
        return self._name

    @property
    def id(self):
        """The integration id of the area."""
        return self._integration_id

    @property
    def occupancy_group(self):
        """Returns the OccupancyGroup for this area, or None."""
        return self._occupancy_group

    @property
    def outputs(self):
        """Return the tuple of the Outputs from this area."""
        return tuple(output for output in self._outputs)

    @property
    def keypads(self):
        """Return the tuple of the Keypads from this area."""
        return tuple(keypad for keypad in self._keypads)

    @property
    def sensors(self):
        """Return the tuple of the MotionSensors from this area."""
        return tuple(sensor for sensor in self._sensors)
