"""
The one error shape every endpoint returns, per the API design doc:
    {"error": {"code": "...", "message": "...", "detail": ...}}

GeometryError is what services raise; api/v1/*.py routers translate it (or
let the shared exception handler in main.py do it) into that shape.
"""
from typing import Any, Optional


class GeometryError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, detail: Optional[Any] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


def invalid_geometry(reason: str, feature_id: Optional[str] = None) -> GeometryError:
    detail = {"feature_id": feature_id} if feature_id else None
    return GeometryError("invalid_geometry", f"Could not parse geometry: {reason}", 400, detail)


def empty_input(what: str) -> GeometryError:
    return GeometryError("empty_input", f"{what} must contain at least one feature", 400)


def unknown_crs(crs: str) -> GeometryError:
    return GeometryError("unknown_crs", f"Unrecognized or unsupported CRS: {crs}", 400, {"crs": crs})
