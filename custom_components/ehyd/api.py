"""API client for eHYD."""

import logging
from typing import TYPE_CHECKING

import aiohttp
from aiohttp import ClientTimeout

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

RIVER_URL = "https://ehyd.gv.at/services/PegelAktuell/json"
GROUNDWATER_URL = "https://ehyd.gv.at/services/GrundwasserAktuell/json"


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

    async def async_update(
        self,
        *,
        fetch_river: bool = True,
        fetch_groundwater: bool = True,
    ) -> dict:
        """Query data from API and store the raw response."""
        endpoints = []
        if fetch_river:
            endpoints.append(("river", RIVER_URL))
        if fetch_groundwater:
            endpoints.append(("groundwater", GROUNDWATER_URL))

        if not endpoints:
            self._raw_response = {}
            return self._raw_response

        async with aiohttp.ClientSession() as session:
            responses = {}
            for response_name, url in endpoints:
                try:
                    _LOGGER.debug("Fetching %s data from URL: %s", response_name, url)
                    async with session.get(
                        url, timeout=ClientTimeout(total=10)
                    ) as response:
                        response.raise_for_status()
                        responses[response_name] = await response.json()
                except TimeoutError as err:
                    error_msg = (
                        f"Timeout while fetching {response_name} data from eHYD API "
                        f"({url})"
                    )
                    _LOGGER.exception(error_msg)
                    raise RuntimeError(error_msg) from err
                except aiohttp.ClientResponseError as err:
                    error_msg = (
                        f"HTTP error while fetching {response_name} data from "
                        f"eHYD API ({url}): status {err.status}"
                    )
                    _LOGGER.exception(error_msg)
                    raise RuntimeError(error_msg) from err
                except aiohttp.ClientError as err:
                    error_msg = (
                        f"Error while fetching {response_name} data from eHYD API "
                        f"({url}): {err}"
                    )
                    _LOGGER.exception(error_msg)
                    raise RuntimeError(error_msg) from err
                except (TypeError, ValueError) as err:
                    error_msg = (
                        f"Invalid response from {response_name} eHYD API ({url}): {err}"
                    )
                    _LOGGER.exception(error_msg)
                    raise RuntimeError(error_msg) from err

            self._raw_response = responses
            return responses
