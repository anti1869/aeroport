"""
Helpers & generics
"""

from sunhead.rest.views import JSONView


class NotImplementedView(JSONView):

    async def get(self):
        return self.json_response({})
