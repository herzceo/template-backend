from collections.abc import Callable
from typing import Any

from dishka import AsyncContainer
from dishka.integrations.base import wrap_injection

from backend.internal.di.container import GlobalContainer


def inject[T, **P](func: Callable[P, T]) -> Callable[P, T]:
    def container_getter(*_args: Any, **_kwargs: Any) -> AsyncContainer:
        return GlobalContainer().get_container()

    return wrap_injection(
        func=func,
        container_getter=container_getter,
        is_async=True,
        manage_scope=True,
    )
