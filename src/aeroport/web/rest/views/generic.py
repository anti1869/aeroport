"""
Helpers & generics
"""

from sunhead.rest.views import JSONView


class NotImplementedView(JSONView):

    async def get(self):
        return self.json_response({})


class NavigationView(JSONView):

    async def get(self):
        from sunhead.conf import settings
        from aeroport.web.rest.urls import urlconf
        nav =[
            {
                "url": "{}://{}/{}/{}".format(
                    self.request.scheme,
                    self.request.host,
                    settings.REST_URL_PREFIX.strip("/"),
                    path.lstrip("/")
                )
            }
            for method, path, __ in urlconf if method.lower() == "get"
        ]
        data = {
            "urls": nav,
        }
        return self.json_response(data)
