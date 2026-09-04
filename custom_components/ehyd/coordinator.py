"""Coordinator for the eHYD integration."""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EhydApi
from .const import (
    CONF_SELECTED_STATIONS,
    DEFAULT_INTERVAL,
    DOMAIN,
    GROUNDWATER_STATIONS,
    RIVER_STATIONS,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class EhydDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinate data updates for the eHYD integration."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=DEFAULT_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from the upstream API."""
        api = EhydApi(self.hass)
        selected = self._get_selected_stations()
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

        return api.raw_response or {}

    def _get_selected_stations(self) -> set[str]:
        """Return stations selected by all eHYD config entries."""
        selected: set[str] = set()
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            entry_options = getattr(entry, "options", {})
            entry_data = getattr(entry, "data", {})
            stations = entry_options.get(
                CONF_SELECTED_STATIONS,
                entry_data.get(CONF_SELECTED_STATIONS, []),
            )
            if isinstance(stations, list):
                selected.update(stations)
        return selected
