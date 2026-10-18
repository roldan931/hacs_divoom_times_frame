"""Divoom Times Frame integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import TYPE_CHECKING

from .const import DOMAIN, UPDATE_INTERVAL
from .models import DeviceState

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

PLATFORMS = ["light"]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured Times Frame."""
    from homeassistant.exceptions import ConfigEntryNotReady
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from homeassistant.helpers.update_coordinator import (
        DataUpdateCoordinator,
        UpdateFailed,
    )

    from .api import DivoomError, DivoomTimesFrameApi

    api = DivoomTimesFrameApi(
        async_get_clientsession(hass),
        entry.data["host"],
        entry.data["device_id"],
        entry.data["port"],
    )
    device_id = entry.data["device_id"]

    try:
        await api.async_validate_device()
    except DivoomError as err:
        raise ConfigEntryNotReady(
            f"Could not validate Divoom DeviceID at {entry.data['host']}"
        ) from err

    async def async_update_data() -> DeviceState:
        try:
            return await api.async_get_state()
        except DivoomError as err:
            raise UpdateFailed(f"Could not retrieve Times Frame state: {err}") from err

    coordinator: DataUpdateCoordinator[DeviceState] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{entry.title} status",
        update_method=async_update_data,
        update_interval=timedelta(seconds=UPDATE_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "device_id": device_id,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Times Frame config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False

    hass.data[DOMAIN].pop(entry.entry_id)
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return True
