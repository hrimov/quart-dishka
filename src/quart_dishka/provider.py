__all__ = [
    "QuartProvider",
]

from dishka import Provider, Scope, from_context
from quart import Request, Websocket


class QuartProvider(Provider):
    request = from_context(Request, scope=Scope.REQUEST)
    websocket = from_context(Websocket, scope=Scope.SESSION)
