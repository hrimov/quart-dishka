from collections.abc import Callable, Generator, Iterable
from contextlib import contextmanager
from functools import partial
from typing import Any
from unittest.mock import Mock

import pytest
from dishka import FromDishka, make_async_container
from quart import Quart, g

from quart_dishka.extension import QuartDishka, inject

from .mocks import REQUEST_DEP_VALUE, AppProvider, RequestDep


@contextmanager
def dishka_app_with_lifecycle_hooks(
    view: Callable[..., Any],
    provider: AppProvider,
    *,
    before_request: Iterable[Callable] | None = None,
    teardown_request: Iterable[Callable] | None = None,
) -> Generator[Quart, None, None]:
    app = Quart(__name__)

    if before_request:
        for func in before_request:
            app.before_request(func)

    app.route('/')(inject(view))

    container = make_async_container(provider)
    QuartDishka(app=app, container=container)

    if teardown_request:
        for func in teardown_request:
            app.teardown_request(func)

    yield app


async def handle_with_request(
    req_dep: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> str:
    mock(req_dep)
    return 'OK'


async def record_container_presence(
    mock: Mock,
    *_args: Any,
    **_kwargs: Any,
) -> None:
    mock(has_container=hasattr(g, 'dishka_container'))


def before_request_interceptor(*args, **kwargs) -> str:
    return 'OK'


@pytest.mark.asyncio
async def test_before_request_adds_container_to_quart_g(
    app_provider: AppProvider,
) -> None:
    teardown_mock = Mock()

    with dishka_app_with_lifecycle_hooks(
        handle_with_request,
        app_provider,
        teardown_request=(partial(record_container_presence, teardown_mock),),
    ) as app:
        test_client = app.test_client()
        response = await test_client.get('/')

        assert response.status_code == 200
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        teardown_mock.assert_called_once_with(has_container=True)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_teardown_skips_container_close_when_not_in_quart_g(
    app_provider: AppProvider,
) -> None:
    teardown_mock = Mock()

    with dishka_app_with_lifecycle_hooks(
        handle_with_request,
        app_provider,
        before_request=(before_request_interceptor,),
        teardown_request=(partial(record_container_presence, teardown_mock),),
    ) as app:
        test_client = app.test_client()
        response = await test_client.get('/')

        assert response.status_code == 200
        app_provider.mock.assert_not_called()
        teardown_mock.assert_called_once_with(has_container=False)
        app_provider.request_released.assert_not_called()
