"""
Shared utilities for CRML simulation.
"""
from typing import Union

NumberOrString = Union[int, float, str]

def parse_numberish_value(v: NumberOrString) -> float:
    """Parse a numeric value encoded as an int/float/string.

    Supported string forms:
        - thousands separators using regular spaces or thin spaces (U+202F)
        - comma separators (removed)
        - percentages (e.g. "50%" -> 0.5)

    Args:
        v: Input value.

    Returns:
        Parsed numeric value.

    Notes:
        Parsing is strict: invalid numeric strings raise ValueError.

    Examples:
        "1 000" -> 1000.0
        "50%" -> 0.5
        "1,234.56" -> 1234.56
    """
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        # Remove spaces, thin spaces, and commas
        s = v.strip().replace(' ', '').replace('\u202f', '').replace(',', '')
        if s.endswith('%'):
            try:
                return float(s[:-1]) / 100.0
            except Exception as e:
                raise ValueError(f"Invalid percentage value: {v!r}") from e
        try:
            return float(s)
        except Exception as e:
            raise ValueError(f"Invalid numeric value: {v!r}") from e

    raise TypeError(f"Unsupported numeric type: {type(v).__name__}")
