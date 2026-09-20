"""Coordinator for the eHYD integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EhydApi
from .const import (
    CONF_SELECTED_STATIONS,
    DEFAULT_INTERVAL,
    DOMAIN,
)
from .stations import GROUNDWATER_STATIONS, RIVER_STATIONS

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class EhydDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinate data updates for the eHYD integration."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry | None = None
    ) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.config_entry = config_entry
        self._fetched_types: set[str] = set()
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=DEFAULT_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from the upstream API."""
        api = EhydApi(self.hass)
        selected = self._get_all_selected_stations()
        fetch_river = any(station["suffix"] in selected for station in RIVER_STATIONS)
        fetch_groundwater = any(
            station["suffix"] in selected for station in GROUNDWATER_STATIONS
        )

        try:
            _LOGGER.debug(
                "EhydDataUpdateCoordinator update fetch_river=%s, fetch_groundwater=%s",
                fetch_river,
                fetch_groundwater,
            )

            await api.async_update(
                fetch_river=fetch_river,
                fetch_groundwater=fetch_groundwater,
            )
        except Exception as err:
            msg = f"Error fetching eHYD data: {err}"
            raise UpdateFailed(msg) from err

        self._fetched_types = {
            station_type
            for station_type, fetched in (
                ("river", fetch_river),
                ("groundwater", fetch_groundwater),
            )
            if fetched
        }
        return api.raw_response or {}

    async def async_ensure_data(self) -> None:
        """Fetch newly required station types when another entry is added."""
        selected = self._get_all_selected_stations()
        required_types = {
            station_type
            for station_type, stations in (
                ("river", RIVER_STATIONS),
                ("groundwater", GROUNDWATER_STATIONS),
            )
            if any(station["suffix"] in selected for station in stations)
        }

        if required_types - self._fetched_types:
            await self.async_request_refresh()

    def _get_all_selected_stations(self) -> list[str]:
        """Return selected stations from all eHYD config entries."""
        if hasattr(self.hass, "config_entries"):
            entries = self.hass.config_entries.async_entries(DOMAIN)
        elif self.config_entry is not None:
            entries = [self.config_entry]
        else:
            entries = []

        selected: list[str] = []
        for config_entry in entries:
            selected.extend(self._get_entry_selected_stations(config_entry))
        return selected

    @staticmethod
    def _get_entry_selected_stations(config_entry: ConfigEntry) -> list[str]:
        """Return selected stations from one config entry."""
        selected = config_entry.options.get(
            CONF_SELECTED_STATIONS,
            config_entry.data.get(CONF_SELECTED_STATIONS, []),
        )
        return selected if isinstance(selected, list) else []

    def _get_selected_stations(self) -> set[str]:
        """Return the union of stations selected in all config entries."""
        return set(self._get_all_selected_stations())
