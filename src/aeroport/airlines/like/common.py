"""
Common utilities for this airline.
"""

import os

STREAM_CONFIG = {
    "streams": {
        "rabbitmq": {
            "transport": "sunhead.events.transports.amqp.AMQPClient",
            "connection_parameters": {
                "login": os.environ.get("AIR_LIKE_STREAM_USER", "guest"),
                "password": os.environ.get("AIR_LIKE_STREAM_PASSWORD", ""),
                "host": os.environ.get("AIR_LIKE_STREAM_HOST", "localhost"),
                "port": int(os.environ.get("AIR_LIKE_STREAM_PORT", 5672)),
                "virtualhost":  os.environ.get("AIR_LIKE_STREAM_VIRTUALHOST", "/"),
            },
            "exchange_name":  os.environ.get("AIR_LIKE_STREAM_EXCHANGE", "like_bus"),
            "exchange_type": "topic",
        },
    },
    "active_stream": "rabbitmq",
}
