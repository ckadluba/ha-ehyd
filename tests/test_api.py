import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.ehyd.api import (
    GROUNDWATER_URL,
    RIVER_URL,
    EhydApi,
)
from custom_components.ehyd.coordinator import EhydDataUpdateCoordinator


class FakeResponse:
    def __init__(self, url: str) -> None:
        self.url = url

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    def raise_for_status(self) -> None:
        return None

    async def json(self) -> dict:
        return {"url": self.url}


class FakeSession:
    def __init__(self) -> None:
        self.urls: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    def get(self, url: str, **kwargs) -> FakeResponse:
        self.urls.append(url)
        return FakeResponse(url)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("fetch_river", "fetch_groundwater", "expected_urls"),
    [
        (True, True, [RIVER_URL, GROUNDWATER_URL]),
        (True, False, [RIVER_URL]),
        (False, True, [GROUNDWATER_URL]),
        (False, False, []),
    ],
)
async def test_api_fetches_only_requested_station_types(
    monkeypatch,
    fetch_river: bool,
    fetch_groundwater: bool,
    expected_urls: list[str],
) -> None:
    session = FakeSession()
    monkeypatch.setattr(
        "custom_components.ehyd.api.aiohttp.ClientSession", lambda: session
    )

    result = await EhydApi(SimpleNamespace()).async_update(
        fetch_river=fetch_river,
        fetch_groundwater=fetch_groundwater,
    )

    assert session.urls == expected_urls
    assert list(result) == [
        name
        for name, enabled in (
            ("river", fetch_river),
            ("groundwater", fetch_groundwater),
        )
        if enabled
    ]
