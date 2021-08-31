from pylutron.lutron_connection import LutronConnection
from pylutron.entities.lutron_entity import LutronEntity
from pylutron.exceptions import InvalidSubscription, IntegrationIdExistsError
from pylutron.logger import _LOGGER


class Lutron(object):
    """Main Lutron Controller class.

    This object owns the connection to the controller, the rooms that exist in the
    network, handles dispatch of incoming status updates, etc.
    """

    # All Lutron commands start with one of these characters
    # See http://www.lutron.com/TechnicalDocumentLibrary/040249.pdf
    OP_EXECUTE = "#"
    OP_QUERY = "?"
    OP_RESPONSE = "~"

    def __init__(self, host, user, password):
        """Initializes the Lutron object. No connection is made to the remote
        device."""
        self._host = host
        self._user = user
        self._password = password
        self._name = None
        self._conn = LutronConnection(host, user, password, self._recv)
        self._ids = {}
        self._legacy_subscribers = {}
        self._areas = []
        self._guid = None

    @property
    def areas(self):
        """Return the areas that were discovered for this Lutron controller."""
        return self._areas

    def set_guid(self, guid):
        self._guid = guid

    @property
    def guid(self):
        return self._guid

    @property
    def name(self):
        return self._name

    def subscribe(self, obj, handler):
        """Subscribes to status updates of the requested object.

        DEPRECATED

        The handler will be invoked when the controller sends a notification
        regarding changed state. The user can then further query the object for the
        state itself."""
        if not isinstance(obj, LutronEntity):
            raise InvalidSubscription("Subscription target not a LutronEntity")
        _LOGGER.warning(
            "DEPRECATED: Subscribing via Lutron.subscribe is obsolete. "
            "Please use LutronEntity.subscribe"
        )
        if obj not in self._legacy_subscribers:
            self._legacy_subscribers[obj] = handler
            obj.subscribe(self._dispatch_legacy_subscriber, None)

    def register_id(self, cmd_type, obj):
        """Registers an object (through its integration id) to receive update
        notifications. This is the core mechanism how Output and Keypad objects get
        notified when the controller sends status updates."""
        ids = self._ids.setdefault(cmd_type, {})
        if obj.id in ids:
            raise IntegrationIdExistsError
        self._ids[cmd_type][obj.id] = obj

    def _dispatch_legacy_subscriber(self, obj, *args, **kwargs):
        """This dispatches the registered callback for 'obj'. This is only used
        for legacy subscribers since new users should register with the target
        object directly."""
        if obj in self._legacy_subscribers:
            self._legacy_subscribers[obj](obj)

    def _recv(self, line):
        """Invoked by the connection manager to process incoming data."""
        if line == "":
            return
        # Only handle query response messages, which are also sent on remote status
        # updates (e.g. user manually pressed a keypad button)
        if line[0] != Lutron.OP_RESPONSE:
            _LOGGER.debug("ignoring %s" % line)
            return
        parts = line[1:].split(",")
        cmd_type = parts[0]
        integration_id = int(parts[1])
        args = parts[2:]
        if cmd_type not in self._ids:
            _LOGGER.info("Unknown cmd %s (%s)" % (cmd_type, line))
            return
        ids = self._ids[cmd_type]
        if integration_id not in ids:
            _LOGGER.warning("Unknown id %d (%s)" % (integration_id, line))
            return
        obj = ids[integration_id]
        handled = obj.handle_update(args)

    def connect(self):
        """Connects to the Lutron controller to send and receive commands and status"""
        self._conn.connect()

    def send(self, op, cmd, integration_id, *args):
        """Formats and sends the requested command to the Lutron controller."""
        out_cmd = ",".join((cmd, str(integration_id)) + tuple((str(x) for x in args)))
        self._conn.send(op + out_cmd)

    def load_xml_db(self, cache_path=None):
        """Load the Lutron database from the server.

        If a locally cached copy is available, use that instead.
        """

        xml_db = None
        loaded_from = None
        if cache_path:
            try:
                with open(cache_path, "rb") as f:
                    xml_db = f.read()
                    loaded_from = "cache"
            except Exception:
                pass
        if not loaded_from:
            import urllib.request

            url = "http://" + self._host + "/DbXmlInfo.xml"
            with urllib.request.urlopen(url) as xmlfile:
                xml_db = xmlfile.read()
                loaded_from = "repeater"

        _LOGGER.info("Loaded xml db from %s" % loaded_from)

        parser = LutronXmlDbParser(lutron=self, xml_db_str=xml_db)
        assert parser.parse()  # throw our own exception
        self._areas = parser.areas
        self._name = parser.project_name

        _LOGGER.info(
            "Found Lutron project: %s, %d areas" % (self._name, len(self.areas))
        )

        if cache_path and loaded_from == "repeater":
            with open(cache_path, "wb") as f:
                f.write(xml_db)

        return True
