from typing import Any

from dishka import AsyncContainer, Scope
from quart import Quart, Request, Websocket, g, request, websocket


class ContainerMiddleware:
    def __init__(self, container: AsyncContainer) -> None:
        self.container = container

    def setup(self, app: Quart) -> None:
        app.before_request(self.enter_request)
        app.before_websocket(self.enter_websocket)
        app.teardown_request(self.exit_scope)
        app.teardown_websocket(self.exit_scope)

    async def enter_request(self) -> None:
        wrapper = self.container({Request: request}, scope=Scope.REQUEST)
        g.dishka_container_wrapper = wrapper
        g.dishka_container = await wrapper.__aenter__()

    async def enter_websocket(self) -> None:
        wrapper = self.container({Websocket: websocket}, scope=Scope.SESSION)
        g.dishka_container_wrapper = wrapper
        g.dishka_container = await wrapper.__aenter__()

    # noinspection PyMethodMayBeStatic
    async def exit_scope(self, *_args: Any, **_kwargs: Any) -> None:
        if container := getattr(g, "dishka_container", None):
            await container.close()
