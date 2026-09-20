import asyncio
import logging
import sys
from pathlib import Path
from types import SimpleNamespace

import aiohttp
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "expected_message"),
    [
        (
            asyncio.TimeoutError(),
            "Timeout while fetching river data from eHYD API",
        ),
        (
            aiohttp.ClientResponseError(None, (), status=503),
            "HTTP error while fetching river data from eHYD API",
        ),
        (
            ValueError("invalid JSON"),
            "Invalid response from river eHYD API",
        ),
    ],
)
async def test_api_logs_specific_errors(
    monkeypatch,
    caplog,
    error: Exception,
    expected_message: str,
) -> None:
    class ErrorResponse(FakeResponse):
        def raise_for_status(self) -> None:
            if isinstance(error, aiohttp.ClientResponseError):
                raise error

        async def json(self) -> dict:
            raise error

    class ErrorSession(FakeSession):
        def get(self, url: str, **kwargs) -> ErrorResponse:
            self.urls.append(url)
            if isinstance(error, asyncio.TimeoutError):
                raise error
            return ErrorResponse(url)

    monkeypatch.setattr(
        "custom_components.ehyd.api.aiohttp.ClientSession", ErrorSession
    )

    with caplog.at_level(logging.ERROR, logger="custom_components.ehyd.api"):
        with pytest.raises(RuntimeError, match=expected_message):
            await EhydApi(SimpleNamespace()).async_update(
                fetch_river=True,
                fetch_groundwater=False,
            )

    assert expected_message in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("selected_stations", "expected_flags"),
    [
        (["schwechat_hallenbad"], (True, False)),
        (["leobersdorf_bl_451"], (False, True)),
        (["schwechat_hallenbad", "leobersdorf_bl_451"], (True, True)),
        ([], (False, False)),
    ],
)
async def test_coordinator_requests_only_configured_station_types(
    monkeypatch,
    selected_stations: list[str],
    expected_flags: tuple[bool, bool],
) -> None:
    calls = []

    class FakeApi:
        def __init__(self, hass) -> None:
            self.raw_response = {"result": "ok"}

        async def async_update(self, **kwargs) -> None:
            calls.append(kwargs)

    monkeypatch.setattr("custom_components.ehyd.coordinator.EhydApi", FakeApi)
    coordinator = EhydDataUpdateCoordinator.__new__(EhydDataUpdateCoordinator)
    coordinator.hass = SimpleNamespace()
    coordinator.config_entry = SimpleNamespace(
        data={"selected_stations": selected_stations}, options={}
    )

    assert await coordinator._async_update_data() == {"result": "ok"}
    assert calls == [
        {
            "fetch_river": expected_flags[0],
            "fetch_groundwater": expected_flags[1],
        }
    ]


@pytest.mark.asyncio
async def test_coordinator_requests_union_of_all_config_entries(monkeypatch) -> None:
    calls = []

    class FakeApi:
        def __init__(self, hass) -> None:
            self.raw_response = {"result": "ok"}

        async def async_update(self, **kwargs) -> None:
            calls.append(kwargs)

    monkeypatch.setattr("custom_components.ehyd.coordinator.EhydApi", FakeApi)
    entries = [
        SimpleNamespace(
            data={"selected_stations": ["schwechat_hallenbad"]}, options={}
        ),
        SimpleNamespace(
            data={"selected_stations": ["leobersdorf_bl_451"]}, options={}
        ),
    ]
    coordinator = EhydDataUpdateCoordinator.__new__(EhydDataUpdateCoordinator)
    coordinator.hass = SimpleNamespace(
        config_entries=SimpleNamespace(async_entries=lambda _domain: entries)
    )

    assert await coordinator._async_update_data() == {"result": "ok"}
    assert calls == [{"fetch_river": True, "fetch_groundwater": True}]
