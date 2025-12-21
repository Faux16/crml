from __future__ import annotations


class OscalError(RuntimeError):
    """Base class for OSCAL helper errors."""


class OscalEndpointNotFoundError(OscalError):
    def __init__(self, endpoint_id: str):
        super().__init__(
            f"Unknown OSCAL endpoint id: {endpoint_id!r}. "
            "Call crml_lang.oscal.load_endpoints() to list available ids."
        )


class OscalFetchError(OscalError):
    def __init__(self, url: str, message: str):
        super().__init__(f"Failed to fetch OSCAL document from {url!r}: {message}")


class OscalParseError(OscalError):
    def __init__(self, source: str, message: str):
        super().__init__(f"Failed to parse OSCAL document from {source!r}: {message}")


class OscalConvertError(OscalError):
    def __init__(self, message: str):
        super().__init__(f"Failed to convert OSCAL to CRML: {message}")
