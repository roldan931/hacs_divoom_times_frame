"""Tests for the Divoom local API client."""

from __future__ import annotations

import unittest
from typing import Any

from custom_components.divoom_times_frame.api import (
    DivoomCommandError,
    DivoomDeviceIdentityError,
    DivoomTimesFrameApi,
)


class FakeResponse:
    """Small async context-manager response fake."""

    def __init__(self, data: Any) -> None:
        self.data = data

    async def __aenter__(self) -> FakeResponse:
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    async def json(self, content_type: str | None = None) -> Any:
        return self.data


class FakeSession:
    """Record requests and return prepared responses."""

    def __init__(self, *responses: Any) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return FakeResponse(self.responses.pop(0))


class ApiTests(unittest.IsolatedAsyncioTestCase):
    """Exercise API command format and identity checks."""

    def make_api(self, session: FakeSession) -> DivoomTimesFrameApi:
        return DivoomTimesFrameApi(session, "192.168.1.10", "300123")

    async def test_validates_device_id_returned_by_ip(self) -> None:
        session = FakeSession(
            {
                "ReturnCode": 0,
                "DeviceId": 300123,
                "DeviceType": "Frame",
                "DeviceName": "Office",
            }
        )
        api = self.make_api(session)

        info = await api.async_validate_device()

        self.assertEqual(info["DeviceName"], "Office")
        self.assertEqual(session.calls[0]["method"], "GET")
        self.assertEqual(
            session.calls[0]["url"],
            "http://192.168.1.10:9000/divoom_api",
        )
        self.assertEqual(
            session.calls[0]["json"],
            {"Command": "Channel/GetClockInfo"},
        )

    async def test_rejects_mismatched_device_id(self) -> None:
        api = self.make_api(FakeSession({"ReturnCode": 0, "DeviceId": 999}))

        with self.assertRaises(DivoomDeviceIdentityError):
            await api.async_validate_device()

    async def test_rejects_missing_device_id(self) -> None:
        api = self.make_api(FakeSession({"ReturnCode": 0, "Brightness": 42}))

        with self.assertRaises(DivoomDeviceIdentityError):
            await api.async_validate_device()

    async def test_reads_and_validates_state(self) -> None:
        session = FakeSession(
            {"ReturnCode": 0, "DeviceId": 300123, "Brightness": 75},
            {"ReturnCode": 0, "OnOff": 1},
        )
        api = self.make_api(session)

        state = await api.async_get_state()

        self.assertTrue(state.is_on)
        self.assertEqual(state.brightness, 75)
        self.assertEqual(
            [call["json"]["Command"] for call in session.calls],
            ["Channel/GetClockInfo", "Channel/GetOnOffScreen"],
        )

    async def test_writes_power_and_brightness_commands(self) -> None:
        session = FakeSession(
            {"ReturnCode": 0, "DeviceId": 300123},
            {"ReturnCode": 0},
            {"ReturnCode": 0, "DeviceId": 300123},
            {"ReturnCode": 0},
        )
        api = self.make_api(session)

        await api.async_set_power(False)
        await api.async_set_brightness(45)

        self.assertEqual(
            [call["json"]["Command"] for call in session.calls],
            [
                "Channel/GetClockInfo",
                "Channel/OnOffScreen",
                "Channel/GetClockInfo",
                "Channel/SetBrightness",
            ],
        )
        self.assertEqual(session.calls[1]["json"]["OnOff"], 0)
        self.assertEqual(session.calls[3]["json"]["Brightness"], 45)

    async def test_rejects_write_if_device_identity_changed(self) -> None:
        session = FakeSession({"ReturnCode": 0, "DeviceId": 999})
        api = self.make_api(session)

        with self.assertRaises(DivoomDeviceIdentityError):
            await api.async_set_power(True)
        self.assertEqual(len(session.calls), 1)

    async def test_rejects_device_command_error(self) -> None:
        api = self.make_api(
            FakeSession({"ReturnCode": 10, "ReturnMessage": "unsupported"})
        )

        with self.assertRaises(DivoomCommandError):
            await api.async_validate_device()


if __name__ == "__main__":
    unittest.main()
