"""Local HTTP API client for Divoom Times Frame."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import API_PATH, DEFAULT_PORT, REQUEST_TIMEOUT
from .helpers import normalize_device_id
from .models import DeviceState


class DivoomError(Exception):
    """Base exception for Divoom API failures."""


class DivoomConnectionError(DivoomError):
    """The device could not be reached."""


class DivoomInvalidResponseError(DivoomError):
    """The device returned an invalid response."""


class DivoomDeviceIdentityError(DivoomError):
    """The DeviceID returned by the device did not match configuration."""


class DivoomCommandError(DivoomError):
    """The device rejected a command."""


class DivoomTimesFrameApi:
    """Async client for the Times Frame local API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        device_id: str,
        port: int = DEFAULT_PORT,
    ) -> None:
        self._session = session
        formatted_host = f"[{host}]" if ":" in host else host
        self._url = f"http://{formatted_host}:{port}{API_PATH}"
        self._device_id = normalize_device_id(device_id)

    async def async_validate_device(self) -> dict[str, Any]:
        """Confirm that the responding frame reports the configured cloud DeviceID."""
        response = await self._async_command("Channel/GetClockInfo")
        self._check_device_identity(response)
        return response

    async def async_get_state(self) -> DeviceState:
        """Read screen state and brightness from the configured device."""
        clock = await self._async_command("Channel/GetClockInfo")
        self._check_device_identity(clock)
        screen = await self._async_command("Channel/GetOnOffScreen")
        try:
            on = int(screen["OnOff"])
            brightness = int(clock["Brightness"])
        except (KeyError, TypeError, ValueError) as err:
            raise DivoomInvalidResponseError(
                "The device response did not contain valid power and brightness"
            ) from err

        if on not in (0, 1) or not 0 <= brightness <= 100:
            raise DivoomInvalidResponseError(
                "The device returned power or brightness outside the supported range"
            )
        return DeviceState(is_on=bool(on), brightness=brightness)

    async def async_set_power(self, is_on: bool) -> None:
        """Turn the screen on or off after confirming the target device."""
        await self.async_validate_device()
        await self._async_command(
            "Channel/OnOffScreen",
            {"OnOff": 1 if is_on else 0},
        )

    async def async_set_brightness(self, brightness: int) -> None:
        """Set brightness after confirming the target device."""
        if not 0 <= brightness <= 100:
            raise ValueError("Brightness must be between 0 and 100")
        await self.async_validate_device()
        await self._async_command(
            "Channel/SetBrightness",
            {"Brightness": brightness},
        )

    def _check_device_identity(self, response: dict[str, Any]) -> None:
        """Reject responses that cannot confirm the configured DeviceID."""
        returned_id = response.get("DeviceId", response.get("DeviceID"))
        if returned_id is None:
            raise DivoomDeviceIdentityError(
                "The device did not include a DeviceID in its response"
            )

        try:
            actual_id = normalize_device_id(returned_id)
        except ValueError as err:
            raise DivoomDeviceIdentityError(
                "The device returned an invalid DeviceID"
            ) from err

        if actual_id != self._device_id:
            raise DivoomDeviceIdentityError(
                "The DeviceID returned by the configured IP does not match"
            )

    async def _async_command(
        self,
        command: str,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a GET request with the JSON body required by the device API."""
        payload = {"Command": command, **(parameters or {})}
        try:
            async with self._session.request(
                "GET",
                self._url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise DivoomConnectionError(
                f"Request {command} to the Times Frame failed"
            ) from err
        except ValueError as err:
            raise DivoomInvalidResponseError(
                f"Request {command} returned invalid JSON"
            ) from err

        if not isinstance(data, dict):
            raise DivoomInvalidResponseError(
                f"Request {command} did not return a JSON object"
            )

        return_code = data.get("ReturnCode")
        if return_code is not None and str(return_code) != "0":
            raise DivoomCommandError(
                f"Request {command} failed with return code {return_code}"
            )
        return data
