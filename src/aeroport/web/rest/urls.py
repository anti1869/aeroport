"""
Urls configuration for REST endpoint.
"""

from aeroport.web.rest.views import jobs
from aeroport.web.rest.views.generic import NotImplementedView

urlconf = (

    # API mainpage
    ("GET", "/", NotImplementedView),

    # Jobs
    ("GET", "/jobs/", NotImplementedView),
    ("POST", "/jobs/", jobs.JobsListView),

)
