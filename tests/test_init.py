import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.ehyd import (
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.ehyd.const import DATA_COORDINATOR, DOMAIN


def test_async_setup_initializes_domain_data() -> None:
    hass = SimpleNamespace(data={})

    assert asyncio.run(async_setup(hass, {})) is True
    assert hass.data == {DOMAIN: {}}


def test_entries_share_coordinator_and_remove_it_after_last_unload(monkeypatch) -> None:
    coordinators = []

    class FakeCoordinator:
        def __init__(self, hass) -> None:
            coordinators.append(self)

        async def async_config_entry_first_refresh(self) -> None:
            return None

    monkeypatch.setattr(
        "custom_components.ehyd.EhydDataUpdateCoordinator", FakeCoordinator
    )

    async def forward_entry_setups(entry, platforms) -> None:
        return None

    async def unload_platforms(entry, platforms) -> bool:
        return True

    def add_update_listener(callback):
        return callback

    entries = [
        SimpleNamespace(
            entry_id="entry-1",
            async_on_unload=lambda callback: None,
            add_update_listener=add_update_listener,
        ),
        SimpleNamespace(
            entry_id="entry-2",
            async_on_unload=lambda callback: None,
            add_update_listener=add_update_listener,
        ),
    ]
    hass = SimpleNamespace(
        data={},
        config_entries=SimpleNamespace(
            async_forward_entry_setups=forward_entry_setups,
            async_unload_platforms=unload_platforms,
        ),
    )

    asyncio.run(async_setup_entry(hass, entries[0]))
    asyncio.run(async_setup_entry(hass, entries[1]))

    assert len(coordinators) == 1
    assert hass.data[DOMAIN]["entry-1"] is coordinators[0]
    assert hass.data[DOMAIN]["entry-2"] is coordinators[0]
    assert hass.data[DOMAIN][DATA_COORDINATOR] is coordinators[0]

    asyncio.run(async_unload_entry(hass, entries[0]))
    assert DATA_COORDINATOR in hass.data[DOMAIN]

    asyncio.run(async_unload_entry(hass, entries[1]))
    assert hass.data[DOMAIN] == {}
