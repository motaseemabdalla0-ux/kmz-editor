import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def concave_polygon() -> dict:
    return load_fixture("concave_polygon.json")


@pytest.fixture
def polygon_with_hole() -> dict:
    return load_fixture("polygon_with_hole.json")


@pytest.fixture
def adjacent_pair() -> dict:
    return load_fixture("adjacent_not_overlapping.json")


@pytest.fixture
def overlapping_pair() -> dict:
    return load_fixture("overlapping_pair.json")


@pytest.fixture
def known_area_square() -> dict:
    return load_fixture("known_area_square.json")
