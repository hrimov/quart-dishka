# Quart-Dishka: Dishka integration for Quart

[![PyPI version](https://badge.fury.io/py/quart-dishka.svg)](
https://badge.fury.io/py/quart-dishka)
[![Supported versions](https://img.shields.io/pypi/pyversions/quart-dishka.svg)](
https://pypi.python.org/pypi/quart-dishka)
[![License](https://img.shields.io/github/license/hrimov/quart-dishka)](
https://github.com/hrimov/quart-dishka/blob/main/LICENSE)

Integration of [Dishka](http://github.com/reagento/dishka/) dependency injection
framework with [Quart](https://github.com/pallets/quart) web framework.

## Features

- **Automatic Scope Management**: Handles REQUEST and SESSION scopes for HTTP and
  WebSocket requests
- **Dependency Injection**: Injects dependencies into route handlers via:
    - Auto-injection mode for all routes
    - `@inject` decorator for manual setup
- **WebSocket Support**: Full support for WebSocket handlers with proper scoping
- **Blueprint Support**: Works with Quart blueprints out of the box

## Installation

Install using `pip`:

```sh
pip install quart-dishka
```

Or with `uv`:

```sh
uv add quart-dishka
```

## Quick Start

```python
from quart import Quart
from dishka import Provider, Scope, provide, make_async_container, FromDishka
from quart_dishka import QuartDishka, inject

# Define your providers
class StringProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def greeting(self) -> str:
        return "Hello"

# Create Quart app and Dishka container
app = Quart(__name__)
container = make_async_container(StringProvider())

# Initialize extension
QuartDishka(app=app, container=container)

# Use dependency injection in routes
@app.route("/")
@inject
async def hello(greeting: FromDishka[str]) -> str:
    return f"{greeting}, World!"

if __name__ == "__main__":
    app.run()
```

## Usage

### Method 1: Auto-Injection Mode

Enable automatic dependency injection for all routes:

```python
from quart import Quart
from dishka import FromDishka, make_async_container
from quart_dishka import QuartDishka

app = Quart(__name__)
container = make_async_container()
QuartDishka(app=app, container=container, auto_inject=True)

# No @inject decorator needed
@app.route("/")
async def hello(greeting: FromDishka[str]) -> str:
    return f"{greeting}, World!"
```

### Method 2: Manual Injection

Use the `@inject` decorator for specific routes:

```python
from dishka import FromDishka
from quart import Quart
from quart_dishka import inject


app = Quart(__name__)


@app.route("/")
@inject
async def hello(greeting: FromDishka[str]) -> str:
    return f"{greeting}, World!"
```

### WebSocket Support

```python
from dishka import FromDishka
from quart import Quart, Websocket
from quart_dishka import inject


app = Quart(__name__)


@app.websocket("/ws")
@inject
async def websocket(ws: FromDishka[Websocket], greeting: FromDishka[str]):
    await ws.accept()
    await ws.send(f"{greeting} from WebSocket!")
```

### Factory Pattern

```python
from dishka import make_async_container
from quart import Quart
from quart_dishka import QuartDishka

container = make_async_container()
dishka = QuartDishka(container=container)

def create_app():
    app = Quart(__name__)
    dishka.init_app(app)
    return app
```

### Blueprint Support

```python
from dishka import FromDishka
from quart import Blueprint, Quart
from quart_dishka import inject

app = Quart(__name__)
bp = Blueprint("example", __name__)


@bp.route("/hello")
@inject
async def hello(greeting: FromDishka[str]) -> str:
    return greeting


app.register_blueprint(bp)
```

## Requirements

- Python 3.10+
- Quart >= 0.20.0
- Dishka >= 1.4.0

## More Examples

Check out the [examples](https://github.com/hrimov/quart-dishka/tree/main/examples)
directory for more detailed examples:

- Basic HTTP routes
- WebSocket handlers
