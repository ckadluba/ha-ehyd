"""Config flow for the eHYD integration."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_SENSOR_PREFIX,
    DOMAIN,
    INTEGRATION_NAME,
    RIVER_STATIONS,
)


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
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title=INTEGRATION_NAME, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    **{
                        vol.Optional(
                            f"{CONF_SENSOR_PREFIX}{station['suffix']}",
                            default=True,
                        ): bool
                        for station in RIVER_STATIONS
                    },
                }
            ),
        )


class EhydOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self) -> None:
        """Initialize options flow."""
        self._conf_app_id: str | None = None

    async def async_step_init(self, user_input: dict[str, str] | None = None):  # noqa: ANN201
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title=INTEGRATION_NAME, data=user_input)

        default_options = self.config_entry.options
        data_options = self.config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    **{
                        vol.Optional(
                            f"{CONF_SENSOR_PREFIX}{station['suffix']}",
                            default=default_options.get(
                                f"{CONF_SENSOR_PREFIX}{station['suffix']}",
                                data_options.get(
                                    f"{CONF_SENSOR_PREFIX}{station['suffix']}",
                                    True,
                                ),
                            ),
                        ): bool
                        for station in RIVER_STATIONS
                    },
                }
            ),
        )
