__all__ = [
    "QuartDishka",
    "inject",
]
import functools
import inspect
from collections.abc import Callable
from typing import Any, TypeAlias, TypeVar

from dishka import AsyncContainer
from dishka.integrations.base import is_dishka_injected, wrap_injection
from quart import Quart, g
from quart.blueprints import Blueprint

from quart_dishka.container import ContainerMiddleware
from quart_dishka.exceptions import ContainerNotSetError

try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec  # type: ignore[assignment]

P = ParamSpec("P")
T = TypeVar("T")
# Note: in Flaks there was a general parent class for app & blueprint,
#       but in Quart there is no such thing, so for typecheker we make an alias
Scaffold: TypeAlias = Blueprint | Quart


def _inject_routes(app: Scaffold) -> None:
    for endpoint, func in app.view_functions.items():
        if not is_dishka_injected(func):
            wrapped = _make_wrapper(func)
            app.view_functions[endpoint] = wrapped

def _make_wrapper(func: Any) -> Any:
    @functools.wraps(func)
    async def wrapped(*args: Any, **kwargs: Any) -> Any:
        injected = inject(func)
        result = injected(*args, **kwargs)

        if inspect.isawaitable(result):
            result = await result

        return result

    return wrapped


def inject(func: Callable[P, T]) -> Callable[P, T]:
    return wrap_injection(
        func=func,
        is_async=True,
        container_getter=lambda _, p: g.dishka_container,
    )


class QuartDishka:
    """Quart extension for Dishka dependency injection.

    Example:
        >>> from dishka.async_container import make_async_container
        >>> from quart_dishka.provider import QuartProvider
        >>> app = Quart(__name__)
        >>> container = make_async_container(QuartProvider())
        >>> QuartDishka(app=app, container=container)

    Args:
        app: Optional Quart application
        container: Optional AsyncContainer instance
        auto_inject: If True, enables auto-injection for all routes
    """

    def __init__(
            self,
            app: Quart | None = None,
            container: AsyncContainer | None = None,
            *,
            auto_inject: bool = False,
    ) -> None:
        self.container = container
        self.auto_inject = auto_inject

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Quart) -> None:

        if not self.container:
            raise ContainerNotSetError

        middleware = ContainerMiddleware(self.container)
        middleware.setup(app)

        if self.auto_inject:
            _inject_routes(app)
            for blueprint in app.blueprints.values():
                # Note: incoming type is flask.sansio.blueprints.Blueprint,
                #       but at runtime it's quart.blueprints.Blueprint
                #       https://github.com/pallets/quart/issues/404
                _inject_routes(blueprint)  # type: ignore[arg-type]

        app.extensions["QUART_DISHKA"] = self
