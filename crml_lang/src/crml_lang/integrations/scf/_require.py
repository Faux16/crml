from importlib.util import find_spec

def require_scf() -> None:
    """
    Raises ImportError if `openpyxl` is not installed.
    """
    if find_spec("openpyxl") is None:
        raise ImportError(
            "The 'scf' integration requires `openpyxl`. "
            "Install with: pip install \"crml-lang[scf]\""
        )
