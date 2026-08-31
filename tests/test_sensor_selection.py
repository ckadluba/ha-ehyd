import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.ehyd.sensor import get_enabled_station_configs


def test_get_enabled_station_configs_defaults_to_all_enabled() -> None:
    config_entry = SimpleNamespace(data={}, options={})

    assert [
        station["suffix"] for station in get_enabled_station_configs(config_entry)
    ] == [
        "schwechat_hallenbad",
        "korneuburg",
        "fischering",
    ]


def test_get_enabled_station_configs_uses_selected_sensors_only() -> None:
    config_entry = SimpleNamespace(
        data={},
        options={
            "sensor_schwechat_hallenbad": True,
            "sensor_korneuburg": False,
            "sensor_fischering": True,
        },
    )

    assert [
        station["suffix"] for station in get_enabled_station_configs(config_entry)
    ] == [
        "schwechat_hallenbad",
        "fischering",
    ]
