"""
Sensors for the eHYD Home Assistant integration.

This module defines the PollenSensor entity which exposes pollen
contamination levels from the integration's coordinator data.
"""

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.ehyd.const import (
    CONF_SELECTED_STATIONS,
    DOMAIN,
    ICON_RIVER_SENSOR,
    INTEGRATION_DEVICE_MANUFACTURER,
    RIVER_STATION_NAMETAG,
    RIVER_STATION_UNIT_OF_MEASUREMENT,
    RIVER_STATIONS,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


def get_enabled_station_configs(
    config_entry: ConfigEntry,
) -> list[dict[str, int | str]]:
    """Return the configured river stations that are enabled."""
    entry_data = getattr(config_entry, "data", {})
    entry_options = getattr(config_entry, "options", {})
    selected = entry_options.get(
        CONF_SELECTED_STATIONS,
        entry_data.get(CONF_SELECTED_STATIONS, []),
    )

    if not isinstance(selected, list):
        return []

    return [station for station in RIVER_STATIONS if station["suffix"] in selected]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up eHYD sensors for a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensors: list[RiverStationSensor] = [
        RiverStationSensor(coordinator, str(item["suffix"]), int(item["hzbnr"]))
        for item in get_enabled_station_configs(config_entry)
    ]

    _LOGGER.debug("Setting up sensor entities: %s", sensors)

    async_add_entities(sensors)


class StationSensor(CoordinatorEntity, SensorEntity):
    """
    Coordinator-backed sensor base class for hydrological data.

    1. Builds the sensor name and unique ID based on the provided station name suffix.
    2. Uses the passed DataExtractor to extract the relevant hydrological data from
       coordinator's response and exposes the values as properties.

    param coordinator: The data update coordinator for this integration.
    param data_extractor: An instance of a DataExtractor subclass to extract the
        relevant hydrological data from the coordinator's response.
    param station_name: The name of the station (e.g., "schwechat_hallenbad").
    param icon: The icon for the sensor entity (default is ICON_RIVER_SENSOR)
    """

    def __init__(
        self,
        coordinator,  # noqa: ANN001
        data_extractor: DataExtractor,
        station_name: str,
        icon: str = ICON_RIVER_SENSOR,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator)

        self.data_extractor = data_extractor
        self.name_suffix = station_name

        # We use the domain as part of every entity allthough it is not
        # HA recommended style. The domain is short and this ensures
        # that the entity_id is unique and descriptive.
        canonical_entity_name = f"{DOMAIN}_{station_name}_{RIVER_STATION_NAMETAG}"
        self._attr_has_entity_name = True
        self._attr_unique_id = canonical_entity_name
        self._attr_icon = icon
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = RIVER_STATION_UNIT_OF_MEASUREMENT

        # Ensure canonical entity_id independent of friendly name
        self.entity_id = f"sensor.{canonical_entity_name}"

        self.entity_description = SensorEntityDescription(
            key=canonical_entity_name,
            translation_key=canonical_entity_name,
            icon=ICON_RIVER_SENSOR,
            native_unit_of_measurement=RIVER_STATION_UNIT_OF_MEASUREMENT,
            state_class=SensorStateClass.MEASUREMENT,
        )

        display_name = station_name.replace("_", " ").title()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_name)},
            name=display_name,
            manufacturer=INTEGRATION_DEVICE_MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
        )

        self._attr_name = f"{display_name} {RIVER_STATION_NAMETAG.title()}"

        _LOGGER.debug(
            ("StationSensor initialized with _attr_unique_id: %s, station_name: %s"),
            self._attr_unique_id,
            self.name_suffix,
        )

    @property
    def native_value(self) -> float | None:
        """Return the current water level."""
        return self.data_extractor.get_native_value()

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional sensor attributes."""
        return self.data_extractor.get_extra_state_attributes()


class DataExtractor:
    """Mixin base class to extract hydrological data from the coordinator response."""

    def __init__(self, coordinator) -> None:  # noqa: ANN001
        """Initialize the data extractor."""
        self.coordinator = coordinator

    @abstractmethod
    def get_native_value(self) -> float | None:
        """Return the current water level for the given element name."""

    @abstractmethod
    def get_extra_state_attributes(self) -> dict:
        """Return additional sensor attributes."""


class RiverStationDataExtractor(DataExtractor):
    """
    Mixin class to extract river station water level data from the coordinator response.

    param coordinator: The data update coordinator for this integration.
    param hzbnr: The numeric ID for the river station according to the API response.
    """

    def __init__(self, coordinator, hzbnr: int) -> None:  # noqa: ANN001
        """Initialize the data extractor."""
        self.coordinator = coordinator
        self._hzbnr = hzbnr

    def get_native_value(self) -> float | None:
        """Return the current water level for the river station."""
        data = self._get_hzbnr_entry()
        if not data or data.get("wert") is None:
            return None

        return float(data["wert"])

    def get_extra_state_attributes(self) -> dict:
        """Return additional sensor attributes."""
        return {}

    def _get_hzbnr_entry(self) -> dict | None:
        """Extract the contamination entry for this pollen type."""
        response = self.coordinator.data
        if not response:
            return None

        features = response.get("features")
        if isinstance(features, list):
            for feature in features:
                if not isinstance(feature, dict):
                    continue

                properties = feature.get("properties")
                if not isinstance(properties, dict):
                    continue

                if properties.get("hzbnr") == self._hzbnr:
                    return properties

        _LOGGER.error(
            ("RiverStationDataExtractor element with hzbnr %d not found in data"),
            self._hzbnr,
        )
        return None


class RiverStationSensor(StationSensor):
    """
    Sensor for the current water level for one specific river station.

    param coordinator: The data update coordinator for this integration.
    param station_name: The name of the station (e.g., "schwechat_hallenbad").
    param hzbnr: The numeric ID for the river station according to the API response.
    """

    def __init__(self, coordinator, station_name: str, hzbnr: int) -> None:  # noqa: ANN001
        """Initialize the sensor entity."""
        super().__init__(
            coordinator,
            RiverStationDataExtractor(coordinator, hzbnr),
            station_name,
        )

        self.hzbnr = hzbnr

        _LOGGER.debug(
            (
                "RiverStationSensor initialized with _attr_unique_id: %s, "
                "station_name: %s, hzbnr: %s"
            ),
            self._attr_unique_id,
            station_name,
            hzbnr,
        )
