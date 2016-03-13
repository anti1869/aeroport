"""
Urls configuration for REST endpoint.
"""

from aeroport.web.rest.views import jobs, airlines
from aeroport.web.rest.views.generic import NotImplementedView

urlconf = (

    # API mainpage
    ("GET", "/", NotImplementedView),

    # Jobs
    ("GET", "/jobs/", NotImplementedView),
    ("POST", "/jobs/", jobs.JobsListView),

    # Airlines & origins
    ("GET", "/airlines/", airlines.AirlinesListView),
    ("GET", "/airlines/{airline}/", airlines.AirlineView),
    ("PUT", "/airlines/{airline}/", airlines.AirlineView),
    ("GET", "/airlines/{airline}/{origin}/", airlines.OriginView),
    ("PUT", "/airlines/{airline}/{origin}/", NotImplementedView),

)
