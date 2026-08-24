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
    DOMAIN,
    ICON_RIVER_SENSOR,
    INTEGRATION_DEVICE_MANUFACTURER,
    INTEGRATION_NAME,
    RIVER_STATION_NAMETAG,
    RIVER_STATION_UNIT_OF_MEASUREMENT,
    RIVER_STATIONS,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up eHYD sensors for a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Setup river water level sensors for each station defined in RIVER_STATIONS
    sensors: list[CoordinatorSensor] = [
        RiverStationSensor(coordinator, item["suffix"], item["hzbnr"])
        for item in RIVER_STATIONS
    ]

    _LOGGER.debug("Setting up sensor entities: %s", sensors)

    async_add_entities(sensors)


class CoordinatorSensor(CoordinatorEntity, SensorEntity):
    """
    Coordinator-backed sensor base class for hydrological data.

    1. Builds the sensor name and unique ID based on the provided station name suffix.
    2. Uses the passed DataExtractor to extract the relevant hydrological data from
       coordinator's response and exposes the values as properties.

    param coordinator: The data update coordinator for this integration.
    param data_extractor: An instance of a DataExtractor subclass to extract the
        relevant hydrological data from the coordinator's response.
    param sensor_name_suffix: The suffix for the sensor name (e.g.,
        "schwechat_hallenbad").
    param icon: The icon for the sensor entity (default is ICON_RIVER_SENSOR)
    """

    def __init__(
        self,
        coordinator,  # noqa: ANN001
        data_extractor: DataExtractor,
        name_suffix: str,
        icon: str = ICON_RIVER_SENSOR,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator)

        self.data_extractor = data_extractor
        self.name_suffix = name_suffix

        canonical_entity_name = f"{DOMAIN}_{name_suffix}"
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

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "ehyd")},
            name=INTEGRATION_NAME,
            manufacturer=INTEGRATION_DEVICE_MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
        )

        _LOGGER.debug(
            ("CoordinatorSensor initialized with _attr_unique_id: %s, name_suffix: %s"),
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


class RiverStationSensor(CoordinatorSensor):
    """
    Sensor for the current water level for one specific river station.

    param coordinator: The data update coordinator for this integration.
    param station_name_suffix: The suffix for the station (e.g., "schwechat_hallenbad").
    param hzbnr: The numeric ID for the river station according to the API response.
    """

    def __init__(self, coordinator, station_name_suffix: str, hzbnr: int) -> None:  # noqa: ANN001
        """Initialize the sensor entity."""
        super().__init__(
            coordinator,
            RiverStationDataExtractor(coordinator, hzbnr),
            f"{RIVER_STATION_NAMETAG}_{station_name_suffix}",
        )

        self.hzbnr = hzbnr

        _LOGGER.debug(
            (
                "RiverStationSensor initialized with _attr_unique_id: %s, "
                "station_name_suffix: %s, hzbnr: %s"
            ),
            self._attr_unique_id,
            station_name_suffix,
            hzbnr,
        )
