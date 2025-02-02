from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
from dishka import FromDishka, make_async_container
from quart import Quart, Request, Websocket

from quart_dishka.container import ContainerMiddleware
from quart_dishka.extension import inject
from quart_dishka.provider import QuartProvider


@asynccontextmanager
async def provider_http_app(handler) -> AsyncGenerator[Quart, None]:
    app = Quart(__name__)
    app.route("/", methods=["GET", "POST"])(inject(handler))
    container = make_async_container(QuartProvider())

    middleware = ContainerMiddleware(container)
    middleware.setup(app)

    try:
        yield app
    finally:
        await container.close()


@asynccontextmanager
async def provider_ws_app(handler) -> AsyncGenerator[Quart, None]:
    app = Quart(__name__)
    app.websocket("/")(inject(handler))
    container = make_async_container(QuartProvider())

    middleware = ContainerMiddleware(container)
    middleware.setup(app)

    try:
        yield app
    finally:
        await container.close()


async def handle_request_get(request: FromDishka[Request]) -> dict:
    return {
        "method": request.method,
        "path": request.path,
        "headers": dict(request.headers),
        "query_string": request.query_string.decode(),
    }


async def handle_request_post(request: FromDishka[Request]) -> dict:
    data = await request.get_json()
    return {
        "method": request.method,
        "content_type": request.headers["content-type"],
        "data": data,
    }


async def handle_websocket(websocket: FromDishka[Websocket]) -> None:
    await websocket.accept()

    headers = dict(websocket.headers)
    path = websocket.path

    data = await websocket.receive_json()

    await websocket.send_json({
        "headers": headers,
        "path": path,
        "echo": data,
    })


@pytest.mark.asyncio
async def test_quart_provider_request_get():
    async with provider_http_app(handle_request_get) as app:
        client = app.test_client()

        headers = {"X-Test": "test-value"}
        response = await client.get("/?param=value", headers=headers)

        assert response.status_code == 200
        data = await response.get_json()

        assert data["method"] == "GET"
        assert data["path"] == "/"
        assert data["query_string"] == "param=value"
        assert data["headers"]["X-Test"] == "test-value"


@pytest.mark.asyncio
async def test_quart_provider_request_post():
    async with provider_http_app(handle_request_post) as app:
        client = app.test_client()

        test_data = {"key": "value"}
        response = await client.post("/", json=test_data)

        assert response.status_code == 200
        data = await response.get_json()

        assert data["method"] == "POST"
        assert data["content_type"] == "application/json"
        assert data["data"] == test_data


@pytest.mark.asyncio
async def test_quart_provider_websocket():
    async with (
        provider_ws_app(handle_websocket) as app,
        app.test_client().websocket("/") as test_client,
    ):
        test_data = {"message": "hello"}
        await test_client.send_json(test_data)

        response = await test_client.receive_json()

        assert response["path"] == "/"
        assert "headers" in response
        assert response["echo"] == test_data
