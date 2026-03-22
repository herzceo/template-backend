from typing import TYPE_CHECKING, cast

from dishka import FromDishka

if TYPE_CHECKING:
    type Depends[T] = T
else:

    class Depends(FromDishka): ...


def from_di[T]() -> Depends[T]:
    return cast("Depends[T]", ...)
