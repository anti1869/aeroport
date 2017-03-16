"""
Base application settings.
"""

import os

HOST = "0.0.0.0"
PORT = "31130"

DEBUG = os.environ.get("DEBUG", "False") == "True"

AIRLINES_MOUNT_POINT = "aeroport.airlines"
AIRLINE_CLASS_PATH_TEMPLATE = "%s.{name}.registration.Airline" % AIRLINES_MOUNT_POINT

DATA_DIR = os.environ.get("AERORPORT_DATA_DIR", os.path.expanduser("~/aeroport"))
DB_PATH = os.path.join(DATA_DIR, "aeroport.db")

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
        "port": int(os.environ.get("AERORPORT_DB_VPORT", 5432)),
        "register_hstore": False,
        # "max_connections": 20,
    }
}

DATABASE_PRESET = "default"