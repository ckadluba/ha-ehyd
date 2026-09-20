"""The eHYD integration component for Home Assistant."""

import asyncio
from typing import TYPE_CHECKING

from homeassistant.helpers import config_validation as cv

from .const import COORDINATOR, DOMAIN, PLATFORMS, SETUP_LOCK
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
    hass.data.setdefault(DOMAIN, {})
    domain_data = hass.data[DOMAIN]
    # Prevent parallel config-entry setup from creating multiple coordinators.
    setup_lock = domain_data.setdefault(SETUP_LOCK, asyncio.Lock())

    async with setup_lock:
        coordinator = domain_data.get(COORDINATOR)

        if coordinator is None:
            coordinator = EhydDataUpdateCoordinator(hass)
            await coordinator.async_config_entry_first_refresh()
            domain_data[COORDINATOR] = coordinator
        else:
            await coordinator.async_ensure_data()

        domain_data[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

        remaining_entries = [
            current_entry
            for current_entry in hass.config_entries.async_entries(DOMAIN)
            if current_entry.entry_id != entry.entry_id
        ]
        if not remaining_entries:
            coordinator = hass.data[DOMAIN].pop(COORDINATOR, None)
            if coordinator is not None:
                await coordinator.async_shutdown()
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
