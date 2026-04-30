from __future__ import annotations

import pytest

from backend.internal.result import Err, Ok


def test_ok_raise_returns_value() -> None:
    result = Ok(data="hello")
    assert result.raise_() == "hello"


def test_err_raise_raises_exception() -> None:
    result = Err(error=ValueError("bad"))
    with pytest.raises(ValueError, match="bad"):
        result.raise_()


def test_ok_with_none_data() -> None:
    result: Ok[None] = Ok(data=None)
    assert result.raise_() is None


def test_err_with_non_exception_raises_type_error() -> None:
    result: Err[str] = Err(error="not_an_exception")
    with pytest.raises(TypeError):
        result.raise_()
