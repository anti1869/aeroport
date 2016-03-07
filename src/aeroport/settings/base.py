"""
Base application settings.
"""

import os

HOST = "0.0.0.0"
PORT = "31130"

DEBUG = os.environ.get("DEBUG", "False") == "True"

AIRLINES_MOUNT_POINT = "aeroport.airlines"
AIRLINE_CLASS_PATH_TEMPLATE = "%s.{name}.registration.Airline" % AIRLINES_MOUNT_POINT
