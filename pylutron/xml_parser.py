from logger import _LOGGER
from area import Area
from entities import (
    LutronEntity,
    Output,
    Keypad,
    Shade,
    Button,
    Led,
    MotionSensor,
    OccupancyGroup,
)


class LutronXmlDbParser(object):
    """The parser for Lutron XML database.

    The database describes all the rooms (Area), keypads (Device), and switches
    (Output). We handle the most relevant features, but some things like LEDs,
    etc. are not implemented."""

    def __init__(self, lutron, xml_db_str):
        """Initializes the XML parser, takes the raw XML data as string input."""
        self._lutron = lutron
        self._xml_db_str = xml_db_str
        self.areas = []
        self._occupancy_groups = {}
        self.project_name = None

    def parse(self):
        """Main entrypoint into the parser. It interprets and creates all the
        relevant Lutron objects and stuffs them into the appropriate hierarchy."""
        import xml.etree.ElementTree as ET

        root = ET.fromstring(self._xml_db_str)
        # The structure is something like this:
        # <Areas>
        #   <Area ...>
        #     <DeviceGroups ...>
        #     <Scenes ...>
        #     <ShadeGroups ...>
        #     <Outputs ...>
        #     <Areas ...>
        #       <Area ...>

        # The GUID is unique to the repeater and is useful for constructing unique
        # identifiers that won't change over time.
        self._lutron.set_guid(root.find("GUID").text)

        # Parse Occupancy Groups
        # OccupancyGroups are referenced by entities in the rest of the XML.  The
        # current structure of the code expects to go from areas -> devices ->
        # other assets and attributes.  Here we index the groups to be bound to
        # Areas later.
        groups = root.find("OccupancyGroups")
        for group_xml in groups.iter("OccupancyGroup"):
            group = self._parse_occupancy_group(group_xml)
            if group.group_number:
                self._occupancy_groups[group.group_number] = group
            else:
                _LOGGER.warning("Occupancy Group has no number.  XML: %s", group_xml)

        # First area is useless, it's the top-level project area that defines the
        # "house". It contains the real nested Areas tree, which is the one we want.
        top_area = root.find("Areas").find("Area")
        self.project_name = top_area.get("Name")
        areas = top_area.find("Areas")
        for area_xml in areas.iter("Area"):
            area = self._parse_area(area_xml)
            self.areas.append(area)
        return True

    def _parse_area(self, area_xml):
        """Parses an Area tag, which is effectively a room, depending on how the
        Lutron controller programming was done."""
        occupancy_group_id = area_xml.get("OccupancyGroupAssignedToID")
        occupancy_group = self._occupancy_groups.get(occupancy_group_id)
        area_name = area_xml.get("Name")
        if not occupancy_group:
            _LOGGER.warning(
                "Occupancy Group not found for Area: %s; ID: %s",
                area_name,
                occupancy_group_id,
            )
        area = Area(
            self._lutron,
            name=area_name,
            integration_id=int(area_xml.get("IntegrationID")),
            occupancy_group=occupancy_group,
        )
        for output_xml in area_xml.find("Outputs"):
            output = self._parse_output(output_xml)
            area.add_output(output)
        # device group in our case means keypad
        # device_group.get('Name') is the location of the keypad
        for device_group in area_xml.find("DeviceGroups"):
            if device_group.tag == "DeviceGroup":
                devs = device_group.find("Devices")
            elif device_group.tag == "Device":
                devs = [device_group]
            else:
                _LOGGER.info("Unknown tag in DeviceGroups child %s" % devs)
                devs = []
            for device_xml in devs:
                if device_xml.tag != "Device":
                    continue
                if device_xml.get("DeviceType") in (
                    "HWI_SEETOUCH_KEYPAD",
                    "SEETOUCH_KEYPAD",
                    "SEETOUCH_TABLETOP_KEYPAD",
                    "PICO_KEYPAD",
                    "HYBRID_SEETOUCH_KEYPAD",
                    "MAIN_REPEATER",
                    "HOMEOWNER_KEYPAD",
                ):
                    keypad = self._parse_keypad(device_xml, device_group)
                    area.add_keypad(keypad)
                elif device_xml.get("DeviceType") == "MOTION_SENSOR":
                    motion_sensor = self._parse_motion_sensor(device_xml)
                    area.add_sensor(motion_sensor)
                # elif device_xml.get('DeviceType') == 'VISOR_CONTROL_RECEIVER':
        return area

    def _parse_output(self, output_xml):
        """Parses an output, which is generally a switch controlling a set of
        lights/outlets, etc."""
        output_type = output_xml.get("OutputType")
        kwargs = {
            "name": output_xml.get("Name"),
            "watts": int(output_xml.get("Wattage")),
            "output_type": output_type,
            "integration_id": int(output_xml.get("IntegrationID")),
            "uuid": output_xml.get("UUID"),
        }
        if output_type == "SYSTEM_SHADE":
            return Shade(self._lutron, **kwargs)
        return Output(self._lutron, **kwargs)

    def _parse_keypad(self, keypad_xml, device_group):
        """Parses a keypad device (the Visor receiver is technically a keypad too)."""
        keypad = Keypad(
            self._lutron,
            name=keypad_xml.get("Name"),
            keypad_type=keypad_xml.get("DeviceType"),
            location=device_group.get("Name"),
            integration_id=int(keypad_xml.get("IntegrationID")),
            uuid=keypad_xml.get("UUID"),
        )
        components = keypad_xml.find("Components")
        if components is None:
            return keypad
        for comp in components:
            if comp.tag != "Component":
                continue
            comp_type = comp.get("ComponentType")
            if comp_type == "BUTTON":
                button = self._parse_button(keypad, comp)
                keypad.add_button(button)
            elif comp_type == "LED":
                led = self._parse_led(keypad, comp)
                keypad.add_led(led)
        return keypad

    def _parse_button(self, keypad, component_xml):
        """Parses a button device that part of a keypad."""
        button_xml = component_xml.find("Button")
        name = button_xml.get("Engraving")
        button_type = button_xml.get("ButtonType")
        direction = button_xml.get("Direction")
        # Hybrid keypads have dimmer buttons which have no engravings.
        if button_type == "SingleSceneRaiseLower":
            name = "Dimmer " + direction
        if not name:
            name = "Unknown Button"
        button = Button(
            self._lutron,
            keypad,
            name=name,
            num=int(component_xml.get("ComponentNumber")),
            button_type=button_type,
            direction=direction,
            uuid=button_xml.get("UUID"),
        )
        return button

    def _parse_led(self, keypad, component_xml):
        """Parses an LED device that part of a keypad."""
        component_num = int(component_xml.get("ComponentNumber"))
        led_base = 80
        if keypad.type == "MAIN_REPEATER":
            led_base = 100
        led_num = component_num - led_base
        led = Led(
            self._lutron,
            keypad,
            name=("LED %d" % led_num),
            led_num=led_num,
            component_num=component_num,
            uuid=component_xml.find("LED").get("UUID"),
        )
        return led

    def _parse_motion_sensor(self, sensor_xml):
        """Parses a motion sensor object.

        TODO: We don't actually do anything with these yet. There's a lot of info
        that needs to be managed to do this right. We'd have to manage the occupancy
        groups, what's assigned to them, and when they go (un)occupied. We'll handle
        this later.
        """
        return MotionSensor(
            self._lutron,
            name=sensor_xml.get("Name"),
            integration_id=int(sensor_xml.get("IntegrationID")),
            uuid=sensor_xml.get("UUID"),
        )

    def _parse_occupancy_group(self, group_xml):
        """Parses an Occupancy Group object.

        These are defined outside of the areas in the XML.  Areas refer to these
        objects by ID.
        """
        return OccupancyGroup(
            self._lutron,
            group_number=group_xml.get("OccupancyGroupNumber"),
            uuid=group_xml.get("UUID"),
        )
