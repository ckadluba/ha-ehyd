"""The eHYD integration component for Home Assistant."""

from typing import TYPE_CHECKING

from homeassistant.helpers import config_validation as cv

from .const import DATA_COORDINATOR, DOMAIN, PLATFORMS
from .coordinator import EhydDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

# Integration can only be set up from config entries
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:  # noqa: ARG001
    """Set up the eHYD component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up eHYD from a config entry."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    coordinator = domain_data.get(DATA_COORDINATOR)
    if coordinator is None:
        coordinator = EhydDataUpdateCoordinator(hass)
        await coordinator.async_config_entry_first_refresh()
        domain_data[DATA_COORDINATOR] = coordinator

    domain_data[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        domain_data = hass.data[DOMAIN]
        domain_data.pop(entry.entry_id, None)
        if not any(key != DATA_COORDINATOR for key in domain_data):
            domain_data.pop(DATA_COORDINATOR, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
