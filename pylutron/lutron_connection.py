import threading
import telnetlib
import socket
import time


from exceptions import ConnectionExistsError, _EXPECTED_NETWORK_EXCEPTIONS
from logger import _LOGGER


class LutronConnection(threading.Thread):
    """Encapsulates the connection to the Lutron controller."""

    USER_PROMPT = b"login: "
    PW_PROMPT = b"password: "
    PROMPT = b"GNET> "

    def __init__(self, host, user, password, recv_callback):
        """Initializes the lutron connection, doesn't actually connect."""
        threading.Thread.__init__(self)

        self._host = host
        self._user = user.encode("ascii")
        self._password = password.encode("ascii")
        self._telnet = None
        self._connected = False
        self._lock = threading.Lock()
        self._connect_cond = threading.Condition(lock=self._lock)
        self._recv_cb = recv_callback
        self._done = False

        self.setDaemon(True)

    def connect(self):
        """Connects to the lutron controller."""
        if self._connected or self.is_alive():
            raise ConnectionExistsError("Already connected")
        # After starting the thread we wait for it to post us
        # an event signifying that connection is established. This
        # ensures that the caller only resumes when we are fully connected.
        self.start()
        with self._lock:
            self._connect_cond.wait_for(lambda: self._connected)

    def _send_locked(self, cmd):
        """Sends the specified command to the lutron controller.

        Assumes self._lock is held.
        """
        _LOGGER.debug("Sending: %s" % cmd)
        try:
            self._telnet.write(cmd.encode("ascii") + b"\r\n")
        except _EXPECTED_NETWORK_EXCEPTIONS:
            _LOGGER.exception("Error sending {}".format(cmd))
            self._disconnect_locked()

    def send(self, cmd):
        """Sends the specified command to the lutron controller.

        Must not hold self._lock.
        """
        with self._lock:
            if not self._connected:
                _LOGGER.debug(
                    "Ignoring send of '%s' because we are disconnected." % cmd
                )
                return
            self._send_locked(cmd)

    def _do_login_locked(self):
        """Executes the login procedure (telnet) as well as setting up some
        connection defaults like turning off the prompt, etc."""
        self._telnet = telnetlib.Telnet(self._host, timeout=2)  # 2 second timeout

        # Ensure we know that connection goes away somewhat quickly
        try:
            sock = self._telnet.get_socket()
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # Some operating systems may not include TCP_KEEPIDLE (macOS, variants of Windows)
            if hasattr(socket, "TCP_KEEPIDLE"):
                # Send keepalive probes after 60 seconds of inactivity
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
            # Wait 10 seconds for an ACK
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            # Send 3 probes before we give up
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
        except OSError:
            _LOGGER.exception("error configuring socket")

        self._telnet.read_until(LutronConnection.USER_PROMPT, timeout=3)
        self._telnet.write(self._user + b"\r\n")
        self._telnet.read_until(LutronConnection.PW_PROMPT, timeout=3)
        self._telnet.write(self._password + b"\r\n")
        self._telnet.read_until(LutronConnection.PROMPT, timeout=3)

        self._send_locked("#MONITORING,12,2")
        self._send_locked("#MONITORING,255,2")
        self._send_locked("#MONITORING,3,1")
        self._send_locked("#MONITORING,4,1")
        self._send_locked("#MONITORING,5,1")
        self._send_locked("#MONITORING,6,1")
        self._send_locked("#MONITORING,8,1")

    def _disconnect_locked(self):
        """Closes the current connection. Assume self._lock is held."""
        was_connected = self._connected
        self._connected = False
        self._connect_cond.notify_all()
        self._telnet = None
        if was_connected:
            _LOGGER.warning("Disconnected")

    def _maybe_reconnect(self):
        """Reconnects to the controller if we have been previously disconnected."""
        with self._lock:
            if not self._connected:
                _LOGGER.info("Connecting")
                # This can throw an exception, but we'll catch it in run()
                self._do_login_locked()
                self._connected = True
                self._connect_cond.notify_all()
                _LOGGER.info("Connected")

    def _main_loop(self):
        """Main body of the the thread function.

        This will maintain connection and receive remote status updates.
        """
        while True:
            line = b""
            try:
                self._maybe_reconnect()
                # If someone is sending a command, we can lose our connection so grab a
                # copy beforehand. We don't need the lock because if the connection is
                # open, we are the only ones that will read from telnet (the reconnect
                # code runs synchronously in this loop).
                t = self._telnet
                if t is not None:
                    line = t.read_until(b"\n", timeout=3)
                else:
                    raise EOFError("Telnet object already torn down")
            except _EXPECTED_NETWORK_EXCEPTIONS:
                _LOGGER.exception("Uncaught exception")
                try:
                    self._lock.acquire()
                    self._disconnect_locked()
                    # don't spam reconnect
                    time.sleep(1)
                    continue
                finally:
                    self._lock.release()
            self._recv_cb(line.decode("ascii").rstrip())

    def run(self):
        """Main entry point into our receive thread.

        It just wraps _main_loop() so we can catch exceptions.
        """
        _LOGGER.info("Started")
        try:
            self._main_loop()
        except Exception:
            _LOGGER.exception("Uncaught exception")
            raise
