import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.ehyd.config_flow import station_is_configured
from custom_components.ehyd.const import DOMAIN
from custom_components.ehyd.sensor import (
    RiverStationDataExtractor,
    RiverStationSensor,
    StationSensor,
    async_setup_entry,
    get_enabled_station_configs,
)


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


class DummyDataExtractor:
    def get_native_value(self) -> float:
        return 1.23

    def get_extra_state_attributes(self) -> dict[str, str]:
        return {"source": "test"}


def test_station_sensor_generates_expected_unique_id() -> None:
    sensor = StationSensor(
        SimpleNamespace(data={}),
        DummyDataExtractor(),
        "schwechat_hallenbad",
    )

    assert sensor.unique_id == "ehyd_schwechat_hallenbad_discharge"
    assert sensor.entity_id == "sensor.ehyd_schwechat_hallenbad_discharge"
    assert sensor.name == "Schwechat Hallenbad Discharge"
    assert sensor.native_value == 1.23
    assert sensor.extra_state_attributes == {"source": "test"}
    assert sensor.device_info["identifiers"] == {(DOMAIN, "schwechat_hallenbad")}


def test_async_setup_entry_creates_one_sensor_per_selected_station() -> None:
    coordinator = SimpleNamespace(data={})
    config_entry = SimpleNamespace(
        entry_id="entry-1",
        data={},
        options={"selected_stations": ["korneuburg", "schwechat_hallenbad"]},
    )
    hass = SimpleNamespace(data={DOMAIN: {"entry-1": coordinator}})
    added: list[RiverStationSensor] = []

    def fake_add_entities(sensors):
        added.extend(sensors)

    import asyncio

    asyncio.run(async_setup_entry(hass, config_entry, fake_add_entities))

    assert [sensor.unique_id for sensor in added] == [
        "ehyd_schwechat_hallenbad_discharge",
        "ehyd_korneuburg_discharge",
    ]
    assert [sensor.hzbnr for sensor in added] == [208157, 207241]


def test_river_station_data_extractor_reads_matching_station_values() -> None:
    coordinator = SimpleNamespace(
        data={
            "features": [
                {"properties": {"hzbnr": 208157, "wert": 4.5}},
                {"properties": {"hzbnr": 207241, "wert": 3.2}},
            ]
        }
    )
    extractor = RiverStationDataExtractor(coordinator, 208157)

    assert extractor._get_hzbnr_entry() == {"hzbnr": 208157, "wert": 4.5}
    assert extractor.get_native_value() == 4.5
    assert extractor.get_extra_state_attributes() == {}


def test_river_station_sensor_uses_suffix_and_hzbnr_for_unique_id() -> None:
    coordinator = SimpleNamespace(
        data={
            "features": [
                {"properties": {"hzbnr": 213371, "wert": 2.75}},
            ]
        }
    )
    sensor = RiverStationSensor(coordinator, "fischering", 213371)

    assert sensor.unique_id == "ehyd_fischering_discharge"
    assert sensor.hzbnr == 213371
    assert sensor.native_value == 2.75
    assert sensor.entity_id == "sensor.ehyd_fischering_discharge"
