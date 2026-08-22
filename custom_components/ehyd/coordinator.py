"""Coordinator for the eHYD integration."""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EhydApi
from .const import DEFAULT_INTERVAL, DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class EhydDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinate data updates for the eHYD integration."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.config_entry = config_entry
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=DEFAULT_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from the upstream API."""
        api = EhydApi(self.hass)

        try:
            await api.async_update()
        except Exception as err:
            msg = f"Error fetching eHYD data: {err}"
            raise UpdateFailed(msg) from err

        return api.raw_response or {}
