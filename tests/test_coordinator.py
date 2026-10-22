import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from homeassistant.helpers.update_coordinator import UpdateFailed

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.ehyd.coordinator import EhydDataUpdateCoordinator


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
async def test_coordinator_requests_configured_station_types_only(
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
    coordinator.hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_entries=lambda _domain: [
                SimpleNamespace(
                    data={"selected_stations": selected_stations}, options={}
                )
            ]
        )
    )

    assert await coordinator._async_update_data() == {"result": "ok"}
    assert calls == [
        {
            "fetch_river": expected_flags[0],
            "fetch_groundwater": expected_flags[1],
        }
    ]


@pytest.mark.asyncio
async def test_coordinator_reports_api_errors_as_update_failed(monkeypatch) -> None:
    """API errors reach Home Assistant with their detailed message."""

    class FailingApi:
        def __init__(self, hass) -> None:
            self.raw_response = None

        async def async_update(self, **kwargs) -> None:
            msg = "Timeout while fetching river data from eHYD API (timeout: 10s)"
            raise RuntimeError(msg)

    monkeypatch.setattr("custom_components.ehyd.coordinator.EhydApi", FailingApi)
    coordinator = EhydDataUpdateCoordinator.__new__(EhydDataUpdateCoordinator)
    coordinator.hass = SimpleNamespace()
    coordinator.config_entry = SimpleNamespace(
        data={"selected_stations": ["schwechat_hallenbad"]}, options={}
    )

    with pytest.raises(UpdateFailed, match="Timeout while fetching river data"):
        await coordinator._async_update_data()


def test_coordinator_collects_stations_from_all_entries() -> None:
    coordinator = EhydDataUpdateCoordinator.__new__(EhydDataUpdateCoordinator)
    coordinator.hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_entries=lambda _domain: [
                SimpleNamespace(
                    data={"selected_stations": ["schwechat_hallenbad"]},
                    options={},
                ),
                SimpleNamespace(
                    data={"selected_stations": ["fischering"]},
                    options={"selected_stations": ["leobersdorf_bl_451"]},
                ),
            ]
        )
    )

    assert coordinator._get_selected_stations() == {
        "schwechat_hallenbad",
        "leobersdorf_bl_451",
    }
