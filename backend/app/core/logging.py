"""
Structured logging. Deliberately logs shape (operation, feature count,
duration, outcome) and never geometry/attribute payload contents by default —
see SECURITY.md §Logging. The data-minimization choice is the point, not an
afterthought.
"""
import logging
import sys
import time
from contextlib import contextmanager
from typing import Iterator

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
        stream=sys.stdout,
    )


logger = logging.getLogger("keymap.geo")


@contextmanager
def log_operation(name: str, **counts: int) -> Iterator[None]:
    """Usage: with log_operation("buffer", feature_count=len(features)): ..."""
    start = time.monotonic()
    extra = " ".join(f"{k}={v}" for k, v in counts.items())
    logger.info("op=%s start %s", name, extra)
    try:
        yield
    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.warning("op=%s FAILED %s duration_ms=%s error=%s", name, extra, duration_ms, exc)
        raise
    else:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.info("op=%s ok %s duration_ms=%s", name, extra, duration_ms)
