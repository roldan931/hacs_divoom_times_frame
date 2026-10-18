"""Tests for pure input and brightness helpers."""

import unittest

from custom_components.divoom_times_frame.helpers import (
    device_brightness_to_ha,
    ha_brightness_to_device,
    normalize_device_id,
    validate_ip_address,
)


class InputHelperTests(unittest.TestCase):
    """Check normalized setup inputs."""

    def test_normalizes_numeric_device_ids(self) -> None:
        self.assertEqual(normalize_device_id("003001"), "3001")
        self.assertEqual(normalize_device_id(3001), "3001")

    def test_rejects_invalid_device_ids(self) -> None:
        for value in ("", "0", "12x", "１２３", True, None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_device_id(value)

    def test_normalizes_ipv4_and_ipv6(self) -> None:
        self.assertEqual(validate_ip_address("192.168.1.10"), "192.168.1.10")
        self.assertEqual(validate_ip_address("2001:0db8::1"), "2001:db8::1")

    def test_rejects_non_ip_hosts(self) -> None:
        with self.assertRaises(ValueError):
            validate_ip_address("example.local")


class BrightnessScaleTests(unittest.TestCase):
    """Check conversions between device and Home Assistant scales."""

    def test_device_scale_maps_to_home_assistant(self) -> None:
        self.assertEqual(device_brightness_to_ha(0), 0)
        self.assertEqual(device_brightness_to_ha(50), 128)
        self.assertEqual(device_brightness_to_ha(100), 255)

    def test_home_assistant_scale_maps_to_device(self) -> None:
        self.assertEqual(ha_brightness_to_device(0), 0)
        self.assertEqual(ha_brightness_to_device(128), 50)
        self.assertEqual(ha_brightness_to_device(255), 100)

    def test_conversions_clamp_out_of_range_values(self) -> None:
        self.assertEqual(device_brightness_to_ha(120), 255)
        self.assertEqual(ha_brightness_to_device(-1), 0)


if __name__ == "__main__":
    unittest.main()
