"""
Base application settings.
"""

import os

HOST = "0.0.0.0"
PORT = "31130"

DEBUG = os.environ.get("DEBUG", "False") == "True"
