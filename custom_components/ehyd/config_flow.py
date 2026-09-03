"""Config flow for the eHYD integration."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_SELECTED_STATIONS,
    DOMAIN,
    GROUNDWATER_STATIONS,
    INTEGRATION_NAME,
    RIVER_STATIONS,
)

ALL_STATIONS = [*RIVER_STATIONS, *GROUNDWATER_STATIONS]


def station_label(station: dict[str, int | str]) -> str:
    """Return the labeled station name for a station selector."""
    station_type = "Groundwater" if station in GROUNDWATER_STATIONS else "River"
    name = str(station["suffix"]).replace("_", " ").title()
    return f"{station_type}: {name} ({station['hzbnr']})"


def station_is_configured(
    entries: list[config_entries.ConfigEntry], station_suffix: str
) -> bool:
    """Return whether a station is already configured in any existing entry."""
    normalized_station = station_suffix.replace("_", " ").title()

    for entry in entries:
        entry_domain = getattr(entry, "domain", None)
        if entry_domain is not None and entry_domain != DOMAIN:
            continue

        selected = list(getattr(entry, "data", {}).get(CONF_SELECTED_STATIONS, []))
        selected.extend(getattr(entry, "options", {}).get(CONF_SELECTED_STATIONS, []))

        if getattr(entry, "unique_id", None) == station_suffix:
            return True

        if station_suffix in selected:
            return True

        if (
            getattr(entry, "title", None)
            and entry.title.lower() == normalized_station.lower()
        ):
            return True

    return False


class EhydConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    @callback
    def async_get_options_flow(
        _config_entry: config_entries.ConfigEntry,
    ) -> EhydOptionsFlowHandler:
        """Return the options flow handler for this config entry."""
        return EhydOptionsFlowHandler()

    async def async_step_user(self, user_input: dict[str, str] | None = None):  # noqa: ANN201
        """Choose a river station when creating the integration."""
        if user_input is not None:
            station_suffix = user_input["station"]
            if station_is_configured(self._async_current_entries(), station_suffix):
                return self.async_abort(reason="already_configured")

            await self.async_set_unique_id(station_suffix)
            self._abort_if_unique_id_configured()

            station = next(
                item for item in ALL_STATIONS if item["suffix"] == station_suffix
            )
            title = station["suffix"].replace("_", " ").title()
            return self.async_create_entry(
                title=title,
                data={CONF_SELECTED_STATIONS: [station_suffix]},
            )

        existing_station_suffixes = {
            station
            for entry in self._async_current_entries()
            for station in [
                *entry.data.get(CONF_SELECTED_STATIONS, []),
                *entry.options.get(CONF_SELECTED_STATIONS, []),
            ]
        }
        available_stations = [
            station
            for station in ALL_STATIONS
            if station["suffix"] not in existing_station_suffixes
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("station"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {
                                    "value": station["suffix"],
                                    "label": station_label(station),
                                }
                                for station in available_stations
                            ],
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
        )


class EhydOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle per-station selection for the eHYD config entry."""

    def _get_selected_stations(self) -> list[str]:
        """Return the currently selected river station suffixes."""
        options = self.config_entry.options
        data = self.config_entry.data
        selected = options.get(
            CONF_SELECTED_STATIONS, data.get(CONF_SELECTED_STATIONS, [])
        )
        if not isinstance(selected, list):
            return []
        return selected

    async def async_step_init(self, user_input: dict[str, str] | None = None):  # noqa: ANN201
        """Show the available actions for this config entry."""
        if user_input is not None:
            if user_input.get("action") == "add_station":
                return await self.async_step_add_station()
            return self.async_create_entry(
                title=INTEGRATION_NAME,
                data={CONF_SELECTED_STATIONS: self._get_selected_stations()},
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("action", default="add_station"): vol.In(
                        {"add_station": "Add river station"}
                    )
                }
            ),
        )

    async def async_step_add_station(self, user_input: dict[str, str] | None = None):  # noqa: ANN201
        """Choose a river station to add as a service/device."""
        selected = self._get_selected_stations()
        available = [
            station for station in ALL_STATIONS if station["suffix"] not in selected
        ]

        if user_input is not None:
            station_suffix = user_input["station"]
            new_selection = list(dict.fromkeys([*selected, station_suffix]))
            return self.async_create_entry(
                title=INTEGRATION_NAME,
                data={CONF_SELECTED_STATIONS: new_selection},
            )

        if not available:
            return self.async_abort(reason="all_stations_added")

        return self.async_show_form(
            step_id="add_station",
            data_schema=vol.Schema(
                {
                    vol.Required("station"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {
                                    "value": station["suffix"],
                                    "label": station_label(station),
                                }
                                for station in available
                            ],
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
        )
