from typing import Any

from dishka import AsyncContainer, Provider, make_async_container

from backend.internal.cls import SingletonMeta


class GlobalContainer(metaclass=SingletonMeta):
    __slots__ = ("_container",)

    def __init__(self) -> None:
        self._container: AsyncContainer = make_async_container()

    def add_providers(
        self, *providers: Provider, context: dict[type[Any], Any] | None = None
    ) -> None:
        new_container = make_async_container(*providers, context=context)
        new_container.parent_container = self._container
        self._container = new_container

    def get_container(self) -> AsyncContainer:
        return self._container
