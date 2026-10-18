"""Input and brightness helpers."""

from __future__ import annotations

from ipaddress import ip_address

BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 100
HA_BRIGHTNESS_MAX = 255


def normalize_device_id(value: object) -> str:
    """Return a numeric Divoom DeviceID in canonical string form."""
    if isinstance(value, bool):
        raise ValueError("DeviceID must be numeric")
    device_id = str(value)
    if not device_id or not device_id.isascii() or not device_id.isdigit():
        raise ValueError("DeviceID must be numeric")
    normalized_id = device_id.lstrip("0")
    if not normalized_id:
        raise ValueError("DeviceID must be greater than zero")
    return normalized_id


def validate_ip_address(value: str) -> str:
    """Validate an IP address and return its compressed representation."""
    return ip_address(value.strip()).compressed


def device_brightness_to_ha(brightness: int) -> int:
    """Scale device brightness (0-100) to Home Assistant's 0-255 scale."""
    return round(
        max(BRIGHTNESS_MIN, min(BRIGHTNESS_MAX, brightness))
        * HA_BRIGHTNESS_MAX
        / BRIGHTNESS_MAX
    )


def ha_brightness_to_device(brightness: int) -> int:
    """Scale Home Assistant brightness (0-255) to the device's 0-100 scale."""
    return round(
        max(0, min(HA_BRIGHTNESS_MAX, brightness))
        * BRIGHTNESS_MAX
        / HA_BRIGHTNESS_MAX
    )
