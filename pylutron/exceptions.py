import socket


class LutronException(Exception):
    """Top level module exception."""

    pass


class IntegrationIdExistsError(LutronException):
    """Asserted when there's an attempt to register a duplicate integration id."""

    pass


class ConnectionExistsError(LutronException):
    """Raised when a connection already exists (e.g. user calls connect() twice)."""

    pass


class InvalidSubscription(LutronException):
    """Raised when an invalid subscription is requested (e.g. calling
    Lutron.subscribe on an incompatible object."""

    pass


_EXPECTED_NETWORK_EXCEPTIONS = (
    BrokenPipeError,
    # OSError: [Errno 101] Network unreachable
    OSError,
    EOFError,
    TimeoutError,
    socket.timeout,
)
