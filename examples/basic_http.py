from dataclasses import dataclass

from dishka import (
    Provider,
    FromDishka,
    Scope,
    make_async_container,
    provide,
)
from quart import Quart, Request, Blueprint
from quart_dishka import QuartDishka, inject
from quart_dishka.provider import QuartProvider


@dataclass
class User:
    id: int
    name: str


class UserProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def current_user(self, request: FromDishka[Request]) -> User:
        user_id = int(request.headers.get("X-User-Id", 0))
        return User(id=user_id, name=f"User {user_id}")


app = Quart(__name__)
container = make_async_container(QuartProvider(), UserProvider())
QuartDishka(app=app, container=container)


@app.route("/hello")
@inject
async def hello_app(user: FromDishka[User]) -> str:
    return f"Hello, {user.name}!"

bp = Blueprint("blueprint", __name__, url_prefix="/blueprint")


@bp.route("/hello")
@inject
async def hello_blueprint(user: FromDishka[User]) -> str:
    return f"Hello from blueprint, {user.name}!"

app.register_blueprint(bp)


if __name__ == "__main__":
    app.run()
