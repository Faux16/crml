from __future__ import annotations

from typing import Iterable


def _clean_numeric_string(raw: str) -> str:
    # Allow readability separators commonly used in YAML/JSON.
    # - regular space
    # - thin space (U+202F)
    # - underscore
    # - comma
    return (
        raw.strip()
        .replace(" ", "")
        .replace("\u202f", "")
        .replace("_", "")
        .replace(",", "")
    )


def parse_floatish(value, *, allow_percent: bool) -> float:
    if value is None:
        raise TypeError("value is None")

    if isinstance(value, bool):
        raise TypeError("boolean is not a valid numeric value")

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        s = _clean_numeric_string(value)
        if not s:
            raise ValueError("empty numeric string")

        if s.endswith("%"):
            if not allow_percent:
                raise ValueError("percent values are not allowed here")
            number_part = s[:-1]
            return float(number_part) / 100.0

        return float(s)

    raise TypeError(f"unsupported numeric type: {type(value).__name__}")


def parse_intish(value) -> int:
    if value is None:
        raise TypeError("value is None")

    if isinstance(value, bool):
        raise TypeError("boolean is not a valid integer")

    if isinstance(value, int):
        return value

    # Strict: floats are not accepted even if integer-like (e.g. 10.0).
    if isinstance(value, float):
        raise TypeError("expected an integer, got float")

    if isinstance(value, str):
        s = _clean_numeric_string(value)
        if not s:
            raise ValueError("empty integer string")
        if s.endswith("%"):
            raise ValueError("percent values are not allowed for integers")

        # Strict: digits only (no decimals, no exponent).
        if s.startswith("+"):
            s = s[1:]
        if not s.isdigit():
            raise ValueError("expected an integer")
        return int(s)

    raise TypeError(f"unsupported integer type: {type(value).__name__}")


def parse_float_list(values: Iterable, *, allow_percent: bool) -> list[float]:
    return [parse_floatish(v, allow_percent=allow_percent) for v in values]
