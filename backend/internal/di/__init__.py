from dishka import FromDishka as Depends

from .container import GlobalContainer
from .inject import inject
from .mock import from_di

__all__ = (
    "Depends",
    "GlobalContainer",
    "from_di",
    "inject",
)
