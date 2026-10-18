"""Models used by the integration."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeviceState:
    """Reported state of the Times Frame display."""

    is_on: bool
    brightness: int
