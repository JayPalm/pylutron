from typing import Any, Callable, Dict
from enum import Enum

# from entities.lutron_entity import LutronEntity  # Is not this circular?

LutronEventHandler = Callable[["LutronEntity", Any, "LutronEvent", Dict], None]


class LutronEvent(Enum):
    """Base class for the events LutronEntity-derived objects can produce."""

    pass
