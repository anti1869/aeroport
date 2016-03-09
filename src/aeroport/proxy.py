"""
Managing proxies to use with site scrapers and other connections.
"""

from random import randrange


class ProxyCollection(object):

    PROXIES_LIST = [
        ("159.182.107.151:80", "http"),
    ]

    def get_proxy(self):
        idx = randrange(len(self.PROXIES_LIST))
        proxy = self.PROXIES_LIST[idx]
        return proxy