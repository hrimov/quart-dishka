from collections.abc import Callable, Generator, Iterable
from contextlib import contextmanager
from typing import Any

import pytest
from dishka import make_async_container
from quart import Quart, g

from quart_dishka.extension import QuartDishka, inject
from .mocks import AppProvider


@contextmanager
def dishka_app_with_lifecycle_hooks(
    view: Callable[..., Any],
    provider: AppProvider,
    *,
    before_request: Iterable[Callable] | None = None,
) -> Generator[Quart, None, None]:
    app = Quart(__name__)

    if before_request:
        for func in before_request:
            app.before_request(func)

    @app.route("/")
    @inject
    async def route_handler_view():
        return await view()

    container = make_async_container(provider)
    QuartDishka(app=app, container=container)

    yield app


async def static_ok_view() -> str:
    return "OK"


def before_request_interceptor(*args, **kwargs) -> str:
    return "OK"


@pytest.mark.asyncio
async def test_before_request_adds_container_to_quart_g(
    app_provider: AppProvider,
) -> None:
    with dishka_app_with_lifecycle_hooks(
        static_ok_view,
        app_provider,
    ) as app:
        async with app.test_request_context("/"):
            client = app.test_client()
            response = await client.get("/")
            assert response.status_code == 200
            assert hasattr(g, "dishka_container")


@pytest.mark.asyncio
async def test_teardown_skips_container_close_when_not_in_quart_g(
    app_provider: AppProvider,
) -> None:
    with dishka_app_with_lifecycle_hooks(
        static_ok_view,
        app_provider,
        before_request=(before_request_interceptor,),
    ) as app:
        async with app.test_request_context("/"):
            client = app.test_client()
            response = await client.get("/")
            assert response.status_code == 200
            assert not hasattr(g, "dishka_container")
