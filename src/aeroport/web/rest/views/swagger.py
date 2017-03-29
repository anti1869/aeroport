import os

from sunhead.rest.views import BasicView


class Swagger(BasicView):

    async def get(self):
        fname = os.path.join(os.path.dirname(__file__), "..", "swagger.yml")
        host = self.request.host
        with open(fname, "r") as f:
            yml = f.read().replace("{{ host }}", host)
        return self.basic_response(text=yml)
