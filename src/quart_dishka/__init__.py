__all__ = [
    'QuartDishka',
    'QuartProvider',
    '__version__',
    'inject',
]

from importlib.metadata import version

from .extension import QuartDishka, inject
from .provider import QuartProvider

__version__ = version('quart-dishka')
