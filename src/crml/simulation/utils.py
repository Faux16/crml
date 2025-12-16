"""
Shared utilities for CRML simulation.
"""
from typing import Union

NumberOrString = Union[int, float, str]

def parse_numberish_value(v: NumberOrString) -> float:
    """
    Parse a numeric value that may contain space-separated thousands 
    (ISO 80000-1 thin space or regular space) or percentages.
    
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
            except Exception:
                return v  # Return original if parsing fails
        try:
            return float(s)
        except Exception:
            return v  # Return original if parsing fails
    return float(v)
