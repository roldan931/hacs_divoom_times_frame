"""Config flow for Divoom Times Frame."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    DivoomConnectionError,
    DivoomDeviceIdentityError,
    DivoomError,
    DivoomInvalidResponseError,
    DivoomTimesFrameApi,
)
from .const import DEFAULT_PORT, DOMAIN
from .helpers import normalize_device_id, validate_ip_address

CONF_DEVICE_ID = "device_id"


def _validate_ip(value: str) -> str:
    """Validate and normalize an IP address for the config form."""
    try:
        return validate_ip_address(value)
    except ValueError as err:
        raise vol.Invalid("Enter a valid IP address") from err


def _validate_device_id(value: str) -> str:
    """Validate the numeric Divoom cloud DeviceID."""
    try:
        return normalize_device_id(value)
    except ValueError as err:
        raise vol.Invalid("Enter the numeric Divoom DeviceID") from err


class DivoomTimesFrameConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Set up a Times Frame by checking its IP and DeviceID."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, str | int] | None = None,
    ) -> FlowResult:
        """Ask for the device's IP, DeviceID, and optional port."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = validate_ip_address(str(user_input[CONF_HOST]))
            device_id = normalize_device_id(str(user_input[CONF_DEVICE_ID]))
            port = int(user_input.get(CONF_PORT, DEFAULT_PORT))
            api = DivoomTimesFrameApi(
                async_get_clientsession(self.hass),
                host,
                device_id,
                port,
            )

            try:
                device_info = await api.async_validate_device()
            except DivoomConnectionError:
                errors["base"] = "cannot_connect"
            except DivoomDeviceIdentityError:
                errors["base"] = "device_id_mismatch"
            except DivoomInvalidResponseError:
                errors["base"] = "invalid_response"
            except DivoomError:
                errors["base"] = "device_error"
            else:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=str(
                        device_info.get("DeviceName")
                        or f"Divoom Times Frame ({host})"
                    ),
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_DEVICE_ID: device_id,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): _validate_ip,
                vol.Required(CONF_DEVICE_ID): _validate_device_id,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=65535),
                ),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
