"""
Application settings, loaded from environment variables (with sensible local
defaults for `docker compose up` — see docker-compose.yml / .env.example).

No secrets live here. This service is intentionally unauthenticated in
Phase 1 (see SECURITY.md) — CORS_ORIGINS and MAX_BODY_BYTES are the actual
guardrails until real auth lands in a later phase.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KEYMAP_", env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"

    # Never wildcard this — see SECURITY.md §CORS. Comma-separated in the env var.
    cors_origins: List[str] = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://motaseemabdalla0-ux.github.io",
    ]

    # A bulk operation over thousands of plots is a multi-MB GeoJSON payload;
    # this caps it so an oversized request fails fast and cleanly (413) rather
    # than degrading the process. See ARCHITECTURE.md §Payload limits.
    max_body_bytes: int = 15 * 1024 * 1024  # 15 MB

    # Sliver-intersection filter default for /geometry/intersection when the
    # caller doesn't specify one — shared-edge floating point noise between
    # real adjacent survey polygons is common enough to need a default.
    default_min_intersection_area_m2: float = 1.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
