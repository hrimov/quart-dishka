from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import Mock

import pytest
from dishka import FromDishka, make_async_container
from quart import Quart, Websocket

from quart_dishka.container import ContainerMiddleware
from quart_dishka.extension import _inject_routes, inject
from .mocks import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    WS_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
    WebSocketAppProvider,
    WebSocketDep,
)


@asynccontextmanager
async def dishka_http_app(handler, provider) -> AsyncGenerator[Quart, None]:
    app = Quart(__name__)
    app.get("/")(inject(handler))
    container = make_async_container(provider)

    middleware = ContainerMiddleware(container)
    middleware.setup(app)

    try:
        yield app
    finally:
        await container.close()


@asynccontextmanager
async def dishka_ws_app(handler, provider) -> AsyncGenerator[Quart, None]:
    app = Quart(__name__)
    app.websocket("/")(inject(handler))
    container = make_async_container(provider)

    middleware = ContainerMiddleware(container)
    middleware.setup(app)

    try:
        yield app
    finally:
        await container.close()


@asynccontextmanager
async def dishka_auto_app(view, provider):
    app = Quart(__name__)
    container = make_async_container(provider)

    middleware = ContainerMiddleware(container)
    middleware.setup(app)

    _inject_routes(app)
    for blueprint in app.blueprints.values():
        _inject_routes(blueprint)

    app.route("/")(inject(view))
    yield app
    await container.close()


async def handle_with_app(
        a: FromDishka[AppDep],
        mock: FromDishka[Mock],
) -> None:
    mock(a)


@pytest.mark.parametrize("app_factory", [
    dishka_http_app, dishka_auto_app,
])
@pytest.mark.asyncio
async def test_http_app_dependency(app_provider: AppProvider, app_factory):
    async with app_factory(handle_with_app, app_provider) as app:
        test_client = app.test_client()
        await test_client.get("/")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


async def handle_with_request(
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
) -> None:
    mock(a)


@pytest.mark.asyncio
async def test_http_request_dependency(app_provider: AppProvider):
    async with dishka_http_app(handle_with_request, app_provider) as app:
        test_client = app.test_client()
        await test_client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_http_request_dependency2(app_provider: AppProvider):
    async with dishka_http_app(handle_with_request, app_provider) as app:
        test_client = app.test_client()
        await test_client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
        app_provider.mock.reset_mock()
        app_provider.request_released.reset_mock()
        await test_client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.fixture(autouse=True)
def reset_mock(ws_app_provider) -> None:
    ws_app_provider.mock.reset_mock()
    ws_app_provider.app_released.reset_mock()
    ws_app_provider.request_released.reset_mock()
    ws_app_provider.websocket_released.reset_mock()


async def get_with_app(
    ws: FromDishka[Websocket],
    app_dep: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> None:
    await ws.accept()
    await ws.receive()  # consume the message
    mock(app_dep)
    await ws.send("passed")


@pytest.mark.asyncio
async def test_websocket_app_dependency(
    ws_app_provider: WebSocketAppProvider,
) -> None:
    async with (
        dishka_ws_app(get_with_app, ws_app_provider) as app,
        app.test_client().websocket("/") as test_client,
    ):
        await test_client.send("ping")
        assert await test_client.receive() == "passed"
        ws_app_provider.mock.assert_called_with(APP_DEP_VALUE)
        ws_app_provider.app_released.assert_not_called()


async def get_with_request(
    ws: FromDishka[Websocket],
    req_dep: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> None:
    await ws.accept()
    await ws.receive()
    mock(req_dep)
    await ws.send("passed")


@pytest.mark.asyncio
async def test_websocket_request_dependency(
    ws_app_provider: WebSocketAppProvider,
) -> None:
    async with dishka_ws_app(get_with_request, ws_app_provider) as app:
        async with app.test_client().websocket("/") as test_client:
            await test_client.send("ping")
            assert await test_client.receive() == "passed"
            ws_app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        ws_app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_request_dependency_multiple(
    ws_app_provider: WebSocketAppProvider,
) -> None:
    async with dishka_ws_app(get_with_request, ws_app_provider) as app:
        async with app.test_client().websocket("/") as test_client:
            await test_client.send("ping")
            assert await test_client.receive() == "passed"
        ws_app_provider.request_released.assert_called_once()
        ws_app_provider.request_released.reset_mock()

        async with app.test_client().websocket("/") as test_client:
            await test_client.send("ping")
            assert await test_client.receive() == "passed"
        ws_app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        ws_app_provider.request_released.assert_called_once()


async def get_with_websocket(
    ws: FromDishka[Websocket],
    ws_dep: FromDishka[WebSocketDep],
    mock: FromDishka[Mock],
) -> None:
    await ws.accept()
    await ws.receive()
    mock(ws_dep)
    await ws.send("passed")


@pytest.mark.asyncio
async def test_websocket_dependency(
    ws_app_provider: WebSocketAppProvider,
) -> None:
    async with dishka_ws_app(get_with_websocket, ws_app_provider) as app:
        async with app.test_client().websocket("/") as test_client:
            await test_client.send("ping")
            assert await test_client.receive() == "passed"
            ws_app_provider.mock.assert_called_with(WS_DEP_VALUE)
        ws_app_provider.websocket_released.assert_called_once()
