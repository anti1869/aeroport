"""
Base application settings.
"""

import os

from aeroport import __version__ as PKG_VERSION


HOST = "0.0.0.0"
PORT = "31130"

DEBUG = os.environ.get("DEBUG", "False") == "True"

CONFIG_FILENAME = os.environ.get("STORE_CONFIG_FILE", "aeroport.yml")

AIRLINES_MOUNT_POINT = "aeroport.airlines"
AIRLINE_CLASS_PATH_TEMPLATE = "%s.{name}.registration.Airline" % AIRLINES_MOUNT_POINT

DATA_DIR = os.environ.get("AERORPORT_DATA_DIR", os.path.expanduser("~/aeroport"))
DB_PATH = os.path.join(DATA_DIR, "aeroport.db")
REST_URL_PREFIX = "/api/v1.0"

FILE_URL_CACHE = {
    "storage": {
        "class": "aeroport.storage.fs_storage.FileSystemStorage",
        "bucket": "filecache",
        "url_template": None,
        "fs_nesting_depth": 2,
        "storage_path": os.path.join(DATA_DIR, "filecache"),
    },
    "expires": os.environ.get("AERORPORT_FILE_URL_CACHE_EXPIRES", 3600 * 12),
}


DATABASE = {
    "default": {
        "engine": "peewee_asyncext.PooledPostgresqlExtDatabase",
        "database": os.environ.get("AERORPORT_DB_NAME", "aeroport"),
        "user": os.environ.get("AERORPORT_DB_USER", ""),
        "password": os.environ.get("AERORPORT_DB_PASSWORD", ""),
        "host": os.environ.get("AERORPORT_DB_HOST", "localhost"),
        "port": int(os.environ.get("AERORPORT_DB_PORT", 5432)),
        "register_hstore": False,
        # "max_connections": 20,
    }
}

DATABASE_PRESET = "default"