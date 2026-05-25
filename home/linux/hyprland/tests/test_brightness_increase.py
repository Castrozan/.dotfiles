from unittest.mock import patch

import brightness


class TestIncreaseBrightnessRaisesHardwareWhenGammaAtMax:
    def test_increments_hardware_brightness_when_gamma_full(self):
        with (
            patch(
                "brightness.read_persisted_gamma_percentage",
                return_value=brightness.GAMMA_MAXIMUM_PERCENT,
            ),
            patch(
                "brightness.get_hardware_brightness_percentage",
                return_value=50,
            ),
            patch("brightness.set_hardware_brightness_percentage") as mock_set,
            patch("brightness.send_brightness_osd") as mock_osd,
        ):
            brightness.increase_brightness(10)

            mock_set.assert_called_once_with(60)
            mock_osd.assert_called_once_with(60)

    def test_clamps_hardware_brightness_to_maximum(self):
        with (
            patch(
                "brightness.read_persisted_gamma_percentage",
                return_value=brightness.GAMMA_MAXIMUM_PERCENT,
            ),
            patch(
                "brightness.get_hardware_brightness_percentage",
                return_value=95,
            ),
            patch("brightness.set_hardware_brightness_percentage") as mock_set,
            patch("brightness.send_brightness_osd") as mock_osd,
        ):
            brightness.increase_brightness(10)

            mock_set.assert_called_once_with(100)
            mock_osd.assert_called_once_with(100)


class TestIncreaseBrightnessRaisesGammaBeforeHardware:
    def test_raises_gamma_when_below_maximum(self):
        with (
            patch("brightness.read_persisted_gamma_percentage", return_value=50),
            patch(
                "brightness.apply_compositor_gamma_percentage", return_value=True
            ) as mock_apply,
            patch("brightness.write_persisted_gamma_percentage") as mock_write,
            patch("brightness.set_hardware_brightness_percentage") as mock_set,
            patch("brightness.send_brightness_osd") as mock_osd,
        ):
            brightness.increase_brightness(10)

            mock_apply.assert_called_once_with(60)
            mock_write.assert_called_once_with(60)
            mock_set.assert_not_called()
            mock_osd.assert_called_once_with(60)

    def test_clamps_gamma_to_maximum_and_does_not_touch_hardware(self):
        with (
            patch("brightness.read_persisted_gamma_percentage", return_value=95),
            patch(
                "brightness.apply_compositor_gamma_percentage", return_value=True
            ) as mock_apply,
            patch("brightness.write_persisted_gamma_percentage") as mock_write,
            patch("brightness.set_hardware_brightness_percentage") as mock_set,
            patch("brightness.send_brightness_osd") as mock_osd,
        ):
            brightness.increase_brightness(10)

            mock_apply.assert_called_once_with(100)
            mock_write.assert_called_once_with(100)
            mock_set.assert_not_called()
            mock_osd.assert_called_once_with(100)

    def test_falls_back_to_hardware_when_gamma_apply_fails(self):
        with (
            patch("brightness.read_persisted_gamma_percentage", return_value=50),
            patch("brightness.apply_compositor_gamma_percentage", return_value=False),
            patch("brightness.write_persisted_gamma_percentage") as mock_write,
            patch(
                "brightness.get_hardware_brightness_percentage",
                return_value=50,
            ),
            patch("brightness.set_hardware_brightness_percentage") as mock_set,
            patch("brightness.send_brightness_osd") as mock_osd,
        ):
            brightness.increase_brightness(10)

            mock_write.assert_not_called()
            mock_set.assert_called_once_with(60)
            mock_osd.assert_called_once_with(60)
