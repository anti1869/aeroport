"""
Production overrides to default config
"""

import os

from raven_aiohttp import AioHttpTransport

from sunhead.global_settings import LOGGING

from aeroport.settings.base import *

DEBUG = False
DEBUG_AUTORELOAD_APP = False

LOGGING["formatters"].update({
    "main_formatter": {
      "format": "%(levelname)-8s [%(name)s:%(lineno)s] %(message)s",
    }
})

LOGGING["handlers"].update({
    "rotater": {
        "level": os.environ.get("AEROPORT_LOGGING_ROTATER_LEVEL", "INFO"),
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "main_formatter",
        "backupCount": int(os.environ.get("AEROPORT_LOGGING_ROTATER_KEEP", 5)),
        "maxBytes": int(os.environ.get("AEROPORT_LOGGING_ROTATER_BYTES", 5242880)),
        "filename": os.environ.get(
            "AEROPORT_LOGGING_ROTATER_FILE",
            "/var/log/aeroport/aeroport.log"
        ),
    },
    "sentry": {
        "level": os.environ.get("AEROPORT_LOGGING_SENTRY_LEVEL", "WARNING"),
        "class": "raven.handlers.logging.SentryHandler",
        "transport": AioHttpTransport,
        "dsn": os.environ.get("AEROPORT_LOGGING_SENTRY_DSN", ""),
    }
})

LOGGING["loggers"][""]["handlers"] += ["rotater", "sentry"]
