from __future__ import annotations

import pytest

from prophecy_api import ProphecyClient

BASE_URL = "https://app.prophecy.io"
TOKEN = "test-token"


@pytest.fixture
def client() -> ProphecyClient:
    return ProphecyClient(
        base_url=BASE_URL,
        token=TOKEN,
        retry_total=0,
    )


@pytest.fixture
def base_url() -> str:
    return BASE_URL
