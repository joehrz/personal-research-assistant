from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from pra.config import Settings
from pra.main import create_app


@pytest.fixture()
def settings(tmp_path) -> Settings:
    return Settings(data_dir=tmp_path / "data")


@pytest.fixture()
def app(settings):
    return create_app(settings)


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        yield c
