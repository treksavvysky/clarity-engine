"""Shared pytest fixtures for in-process FastAPI testing."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from fastapi.testclient import TestClient

from app.main import app

EXAMPLE_MANIFEST_PATH = PROJECT_ROOT / "packets" / "examples" / "context_packet_example.json"


@pytest.fixture(scope="session")
def client() -> TestClient:
    """In-process FastAPI client for endpoint tests."""

    return TestClient(app)


@pytest.fixture(scope="session")
def example_manifest() -> dict:
    """Load the golden example manifest used across endpoint tests."""

    with EXAMPLE_MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)
