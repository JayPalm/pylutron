"""
Lutron RadioRA 2 module for interacting with the Main Repeater. Basic operations
for enumerating and controlling the loads are supported.

"""

__author__ = "Dima Zavin"
__copyright__ = "Copyright 2016, Dima Zavin"


# __all__ = ["lutron"]


from pylutron.lutron import Lutron

# import pylutron.entities
# import pylutron.area
# import pylutron.events

# from exceptions import (
#     LutronException,
#     IntegrationIdExistsError,
#     ConnectionExistsError,
#     InvalidSubscription,
# )


# We brute force exception handling in a number of areas to ensure
# connections can be recovered


# This describes the type signature of the callback that LutronEntity
# subscribers must provide.
