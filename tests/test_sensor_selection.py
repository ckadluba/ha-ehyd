import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.ehyd.config_flow import station_is_configured
from custom_components.ehyd.sensor import get_enabled_station_configs


def test_station_is_configured_detects_existing_station() -> None:
    entries = [
        SimpleNamespace(
            data={"selected_stations": ["korneuburg"]},
            options={},
        ),
        SimpleNamespace(
            data={},
            options={"selected_stations": ["fischering"]},
        ),
    ]

    assert station_is_configured(entries, "korneuburg") is True
    assert station_is_configured(entries, "schwechat_hallenbad") is False


def test_get_enabled_station_configs_defaults_to_empty() -> None:
    config_entry = SimpleNamespace(data={}, options={})

    assert [
        station["suffix"] for station in get_enabled_station_configs(config_entry)
    ] == []


def test_get_enabled_station_configs_uses_selected_sensors_only() -> None:
    config_entry = SimpleNamespace(
        data={"selected_stations": ["schwechat_hallenbad", "fischering"]},
        options={},
    )

    assert [
        station["suffix"] for station in get_enabled_station_configs(config_entry)
    ] == [
        "schwechat_hallenbad",
        "fischering",
    ]
