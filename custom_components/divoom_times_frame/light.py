"""Light platform for Divoom Times Frame."""

from __future__ import annotations

from typing import Any, Awaitable

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import DivoomError, DivoomTimesFrameApi
from .const import DOMAIN
from .helpers import device_brightness_to_ha, ha_brightness_to_device
from .models import DeviceState


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Times Frame light."""
    data: dict[str, Any] = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            DivoomTimesFrameLight(
                data["coordinator"],
                data["api"],
                entry,
                data["device_id"],
            )
        ]
    )


class DivoomTimesFrameLight(
    CoordinatorEntity[DataUpdateCoordinator[DeviceState]],
    LightEntity,
):
    """Represent the Times Frame display as a dimmable light."""

    _attr_has_entity_name = True
    _attr_translation_key = "display"
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[DeviceState],
        api: DivoomTimesFrameApi,
        entry: ConfigEntry,
        device_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{device_id}_display"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer="Divoom",
            model="Times Frame",
            name=entry.title,
        )

    @property
    def is_on(self) -> bool:
        """Return whether the frame display is on."""
        return self.coordinator.data.is_on

    @property
    def color_mode(self) -> ColorMode:
        """Return the display's supported brightness mode."""
        return ColorMode.BRIGHTNESS

    @property
    def brightness(self) -> int:
        """Return brightness in Home Assistant's 0-255 scale."""
        return device_brightness_to_ha(self.coordinator.data.brightness)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the frame on and optionally set its brightness."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        operations = []
        if brightness is not None:
            operations.append(
                self._api.async_set_brightness(
                    ha_brightness_to_device(int(brightness))
                )
            )
        operations.append(self._api.async_set_power(True))
        await self._async_execute(*operations)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the frame off."""
        await self._async_execute(self._api.async_set_power(False))

    async def _async_execute(self, *operations: Awaitable[None]) -> None:
        """Execute a device command and refresh state, surfacing failures."""
        try:
            for operation in operations:
                await operation
            await self.coordinator.async_request_refresh()
        except DivoomError as err:
            raise HomeAssistantError(
                f"Could not control the Divoom Times Frame: {err}"
            ) from err
