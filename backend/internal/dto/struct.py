from collections.abc import Mapping
from typing import Any, Self

import uuid_utils
from msgspec import Struct, convert, to_builtins


def _enc_hook(obj: object) -> object:
    if isinstance(obj, uuid_utils.UUID):
        return str(obj)
    raise TypeError(f"Encoding objects of type {type(obj)} is unsupported")


def _dec_hook(typ: type, obj: object) -> object:
    if typ is uuid_utils.UUID and isinstance(obj, str):
        return uuid_utils.UUID(obj)
    raise TypeError(f"Decoding objects of type {typ} is unsupported")


class ImplToBuiltinsSupported(Struct):
    def to_builtins(self) -> Mapping[str, Any]:
        return to_builtins(self, str_keys=True, enc_hook=_enc_hook)  # type: ignore[no-any-return]


class ImplFromBuiltinsSupported(Struct):
    @classmethod
    def from_builtins(cls, data: Mapping[str, Any]) -> Self:
        return convert(data, type=cls, from_attributes=True, dec_hook=_dec_hook)


class ImplFromObjectSupported(Struct):
    @classmethod
    def from_object(cls, obj: object) -> Self:
        return convert(obj, type=cls, from_attributes=True)


class StructDTO(
    ImplToBuiltinsSupported,
    ImplFromBuiltinsSupported,
    ImplFromObjectSupported,
): ...
