from unittest.mock import patch

import brightness


class TestDecreaseBrightnessLowersHardwareAboveMinimum:
    def test_decrements_hardware_brightness_when_above_minimum(self):
        with (
            patch(
                "brightness.get_hardware_brightness_percentage",
                return_value=50,
            ),
            patch("brightness.set_hardware_brightness_percentage") as mock_set,
            patch("brightness.send_brightness_osd") as mock_osd,
        ):
            brightness.decrease_brightness(10)

            mock_set.assert_called_once_with(40)
            mock_osd.assert_called_once_with(40)

    def test_clamps_hardware_brightness_to_minimum(self):
        with (
            patch(
                "brightness.get_hardware_brightness_percentage",
                return_value=5,
            ),
            patch("brightness.set_hardware_brightness_percentage") as mock_set,
            patch("brightness.send_brightness_osd") as mock_osd,
        ):
            brightness.decrease_brightness(10)

            mock_set.assert_called_once_with(
                brightness.HARDWARE_BRIGHTNESS_MINIMUM_PERCENT
            )
            mock_osd.assert_called_once_with(
                brightness.HARDWARE_BRIGHTNESS_MINIMUM_PERCENT
            )


class TestDecreaseBrightnessLowersGammaAtHardwareMinimum:
    def test_lowers_gamma_when_hardware_already_at_minimum(self):
        with (
            patch(
                "brightness.get_hardware_brightness_percentage",
                return_value=brightness.HARDWARE_BRIGHTNESS_MINIMUM_PERCENT,
            ),
            patch("brightness.read_persisted_gamma_percentage", return_value=100),
            patch(
                "brightness.apply_compositor_gamma_percentage", return_value=True
            ) as mock_apply,
            patch("brightness.write_persisted_gamma_percentage") as mock_write,
            patch("brightness.send_brightness_osd") as mock_osd,
        ):
            brightness.decrease_brightness(10)

            mock_apply.assert_called_once_with(90)
            mock_write.assert_called_once_with(90)
            mock_osd.assert_called_once_with(90)

    def test_clamps_gamma_to_minimum(self):
        with (
            patch(
                "brightness.get_hardware_brightness_percentage",
                return_value=brightness.HARDWARE_BRIGHTNESS_MINIMUM_PERCENT,
            ),
            patch("brightness.read_persisted_gamma_percentage", return_value=15),
            patch(
                "brightness.apply_compositor_gamma_percentage", return_value=True
            ) as mock_apply,
            patch("brightness.write_persisted_gamma_percentage") as mock_write,
            patch("brightness.send_brightness_osd") as mock_osd,
        ):
            brightness.decrease_brightness(10)

            mock_apply.assert_called_once_with(brightness.GAMMA_MINIMUM_PERCENT)
            mock_write.assert_called_once_with(brightness.GAMMA_MINIMUM_PERCENT)
            mock_osd.assert_called_once_with(brightness.GAMMA_MINIMUM_PERCENT)

    def test_skips_gamma_write_when_compositor_apply_fails(self):
        with (
            patch(
                "brightness.get_hardware_brightness_percentage",
                return_value=brightness.HARDWARE_BRIGHTNESS_MINIMUM_PERCENT,
            ),
            patch("brightness.read_persisted_gamma_percentage", return_value=100),
            patch("brightness.apply_compositor_gamma_percentage", return_value=False),
            patch("brightness.write_persisted_gamma_percentage") as mock_write,
            patch("brightness.send_brightness_osd") as mock_osd,
        ):
            brightness.decrease_brightness(10)

            mock_write.assert_not_called()
            mock_osd.assert_called_once_with(
                brightness.HARDWARE_BRIGHTNESS_MINIMUM_PERCENT
            )
