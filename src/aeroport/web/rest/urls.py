"""
Urls configuration for REST endpoint.
"""

from aeroport.web.rest.views import flights, airlines
from aeroport.web.rest.views.generic import NotImplementedView, NavigationView

urlconf = (

    # API mainpage
    ("GET", "/", NavigationView),

    # Jobs
    ("GET", "/flights/", flights.FlightsListView),
    ("POST", "/flights/", flights.FlightsListView),

    # Airlines & origins
    ("GET", "/airlines/", airlines.AirlinesListView),
    ("GET", "/airlines/{airline}/", airlines.AirlineView),
    ("PUT", "/airlines/{airline}/", airlines.AirlineView),
    ("GET", "/airlines/{airline}/{origin}/", airlines.OriginView),
    ("PUT", "/airlines/{airline}/{origin}/", NotImplementedView),

)
