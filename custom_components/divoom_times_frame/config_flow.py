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
STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_DEVICE_ID): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


class ConfigFlow(
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
            try:
                host = validate_ip_address(str(user_input[CONF_HOST]))
            except ValueError:
                return self.async_show_form(
                    step_id="user",
                    data_schema=STEP_USER_SCHEMA,
                    errors={CONF_HOST: "invalid_ip"},
                )

            try:
                device_id = normalize_device_id(str(user_input[CONF_DEVICE_ID]))
            except ValueError:
                return self.async_show_form(
                    step_id="user",
                    data_schema=STEP_USER_SCHEMA,
                    errors={CONF_DEVICE_ID: "invalid_device_id"},
                )

            try:
                port = int(user_input.get(CONF_PORT, DEFAULT_PORT))
                if not 1 <= port <= 65535:
                    raise ValueError("Port must be between 1 and 65535")
            except (TypeError, ValueError):
                return self.async_show_form(
                    step_id="user",
                    data_schema=STEP_USER_SCHEMA,
                    errors={CONF_PORT: "invalid_port"},
                )

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

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
