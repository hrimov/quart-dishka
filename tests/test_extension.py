import pytest
from dishka import FromDishka, make_async_container
from quart import Blueprint, Quart

from quart_dishka.exceptions import ContainerNotSetError
from quart_dishka.extension import QuartDishka, inject
from .mocks import APP_DEP_VALUE, AppDep, AppProvider


@pytest.mark.asyncio
async def test_quart_dishka_init():
    app = Quart(__name__)
    container = make_async_container(AppProvider())
    extension = QuartDishka(app=app, container=container)

    assert extension.container == container
    assert extension.auto_inject is False
    assert "QUART_DISHKA" in app.extensions


@pytest.mark.asyncio
async def test_quart_dishka_init_without_container():
    app = Quart(__name__)
    extension = QuartDishka(app=None)

    with pytest.raises(ContainerNotSetError,
                       match="Container must be set before initializing app"):
        extension.init_app(app)


@pytest.mark.asyncio
async def test_factory_pattern():
    container = make_async_container(AppProvider())
    extension = QuartDishka(container=container)

    app = Quart(__name__)
    extension.init_app(app)

    assert "QUART_DISHKA" in app.extensions


@pytest.mark.asyncio
async def test_quart_dishka_auto_inject():
    app = Quart(__name__)
    container = make_async_container(AppProvider())

    @app.route("/")
    async def index(app_dep: FromDishka[AppDep]) -> str:
        return str(app_dep)

    @app.route("/explicit")
    @inject
    async def explicit(app_dep: FromDishka[AppDep]) -> str:
        return str(app_dep)

    QuartDishka(app=app, container=container, auto_inject=True)

    client = app.test_client()

    response = await client.get("/")
    assert response.status_code == 200
    assert await response.get_data(as_text=True) == str(APP_DEP_VALUE)

    response = await client.get("/explicit")
    assert response.status_code == 200
    assert await response.get_data(as_text=True) == str(APP_DEP_VALUE)


@pytest.mark.asyncio
async def test_quart_dishka_blueprint_auto_inject():
    app = Quart(__name__)
    bp = Blueprint("test", __name__)
    container = make_async_container(AppProvider())

    @bp.route("/bp")
    async def bp_route(app_dep: FromDishka[AppDep]) -> str:
        return str(app_dep)

    @bp.route("/bp-explicit")
    @inject
    async def bp_explicit(app_dep: FromDishka[AppDep]) -> str:
        return str(app_dep)

    app.register_blueprint(bp)
    QuartDishka(app=app, container=container, auto_inject=True)

    client = app.test_client()

    response = await client.get("/bp")
    assert response.status_code == 200
    assert await response.get_data(as_text=True) == str(APP_DEP_VALUE)

    response = await client.get("/bp-explicit")
    assert response.status_code == 200
    assert await response.get_data(as_text=True) == str(APP_DEP_VALUE)
