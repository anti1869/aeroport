"""
Common utilities for this airline.
"""

STREAM_CONFIG = {
    "streams": {
        "rabbitmq": {
            "transport": "sunhead.events.transports.amqp.AMQPClient",
            "connection_parameters": {
                "login": "guest",
                "password": "",
                "host": "localhost",
                "port": 5672,
                "virtualhost": "/",
            },
            "exchange_name": "like_bus",
            "exchange_type": "topic",
        },
    },
    "active_stream": "rabbitmq",
}
