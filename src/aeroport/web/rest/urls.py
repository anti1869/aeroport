"""
Urls configuration for REST endpoint.
"""

from aeroport.web.rest.views import destinations, flights, airlines, swagger
from aeroport.web.rest.views.generic import NotImplementedView, NavigationView

urlconf = (

    # Docs
    ("*", "/swagger.yml", swagger.Swagger),

    # API mainpage
    ("GET", "/", NavigationView),

    # Jobs
    ("GET", "/flights/", flights.FlightsListView),
    ("POST", "/flights/", flights.FlightsListView),

    # Destinations
    ("GET", "/destinations/", destinations.DestinationsListView),
    ("POST", "/destinations/", destinations.DestinationsListView),
    ("GET", "/destinations/{destination}/", destinations.DestinationView),
    ("PUT", "/destinations/{destination}/", destinations.DestinationView),
    ("DELETE", "/destinations/{destination}/", destinations.DestinationView),

    # Airlines & origins
    ("GET", "/airlines/", airlines.AirlinesListView),
    ("GET", "/airlines/{airline}/", airlines.AirlineView),
    ("PUT", "/airlines/{airline}/", airlines.AirlineView),
    ("GET", "/airlines/{airline}/{origin}/", airlines.OriginView),
    ("PUT", "/airlines/{airline}/{origin}/", NotImplementedView),

)
