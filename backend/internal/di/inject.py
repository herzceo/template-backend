from collections.abc import Callable
from typing import cast

from dishka.integrations.litestar import inject as _litestar_inject


def inject[T, **P](func: Callable[P, T]) -> Callable[P, T]:
    return cast("Callable[P, T]", _litestar_inject(func))
