"""API client for eHYD."""

import logging
from typing import TYPE_CHECKING

import aiohttp
from aiohttp import ClientTimeout

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class EhydApi:
    """Class to handle API access for eHYD."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the API handler."""
        self.hass = hass
        self._raw_response = None

    @property
    def raw_response(self):  # noqa: ANN201
        """Return the latest raw API response."""
        return self._raw_response

    async def async_update(self):  # noqa: ANN201
        """Query data from API and store the raw response."""
        rivers_url = "https://ehyd.gv.at/services/PegelAktuell/json"
        _LOGGER.debug("Fetching data from URL: %s", rivers_url)

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.get(rivers_url, timeout=ClientTimeout(total=10)) as response,
            ):
                response.raise_for_status()
                data = await response.json()
                self._raw_response = data
                return data
        except aiohttp.ClientError as err:
            error_msg = f"Error fetching data from URL: {rivers_url}"
            _LOGGER.exception(error_msg)
            raise RuntimeError(error_msg) from err
