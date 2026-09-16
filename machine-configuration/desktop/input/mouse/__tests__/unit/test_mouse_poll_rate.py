from unittest.mock import patch

import mouse_poll_rate


class TestDecodeRateValue:
    def test_decodes_8000hz(self):
        assert mouse_poll_rate.decode_rate_value(0x40, 0x15) == "8000Hz"

    def test_decodes_4000hz(self):
        assert mouse_poll_rate.decode_rate_value(0x20, 0x35) == "4000Hz"

    def test_decodes_2000hz(self):
        assert mouse_poll_rate.decode_rate_value(0x10, 0x45) == "2000Hz"

    def test_decodes_1000hz(self):
        assert mouse_poll_rate.decode_rate_value(0x01, 0x54) == "1000Hz"

    def test_returns_unknown_for_unrecognized_value(self):
        result = mouse_poll_rate.decode_rate_value(0xAA, 0xBB)
        assert "unknown" in result


class TestRateArgumentToBytes:
    def test_parses_8k(self):
        assert mouse_poll_rate.rate_argument_to_bytes("8k") == (0x40, 0x15)

    def test_parses_8000(self):
        assert mouse_poll_rate.rate_argument_to_bytes("8000") == (0x40, 0x15)

    def test_parses_4k(self):
        assert mouse_poll_rate.rate_argument_to_bytes("4k") == (0x20, 0x35)

    def test_parses_2k(self):
        assert mouse_poll_rate.rate_argument_to_bytes("2k") == (0x10, 0x45)

    def test_parses_1k(self):
        assert mouse_poll_rate.rate_argument_to_bytes("1k") == (0x01, 0x54)

    def test_rejects_invalid_rate(self):
        try:
            mouse_poll_rate.rate_argument_to_bytes("3k")
            assert False, "Should have raised SystemExit"
        except SystemExit:
            pass


class TestGetCurrentRate:
    def test_returns_decoded_rate(self):
        response = bytes([0x08, 0x08, 0x00, 0x00, 0x00, 0x06, 0x40, 0x15] + [0x00] * 9)

        with patch(
            "atk_mouse_device.find_atk_hidraw_config_interface",
            return_value="/dev/hidraw0",
        ):
            with patch(
                "atk_mouse_device.send_and_receive_atk_command",
                return_value=response,
            ):
                assert mouse_poll_rate.get_current_rate() == "8000Hz"


class TestSetRate:
    def test_skips_when_already_at_target(self, capsys):
        current_response = bytes(
            [0x08, 0x08, 0x00, 0x00, 0x00, 0x06, 0x40, 0x15] + [0x00] * 9
        )

        with patch(
            "atk_mouse_device.find_atk_hidraw_config_interface",
            return_value="/dev/hidraw0",
        ):
            with patch(
                "atk_mouse_device.send_and_receive_atk_command",
                return_value=current_response,
            ):
                mouse_poll_rate.set_rate("8k")
                output = capsys.readouterr().out
                assert "Already at 8000Hz" in output

    def test_changes_rate_successfully(self, capsys):
        current_response = bytes(
            [0x08, 0x08, 0x00, 0x00, 0x00, 0x06, 0x01, 0x54, 0xAA, 0xBB, 0xCC, 0xDD]
            + [0x00] * 5
        )
        verify_response = bytes(
            [0x08, 0x08, 0x00, 0x00, 0x00, 0x06, 0x40, 0x15] + [0x00] * 9
        )

        with patch(
            "atk_mouse_device.find_atk_hidraw_config_interface",
            return_value="/dev/hidraw0",
        ):
            with patch(
                "atk_mouse_device.send_and_receive_atk_command",
                side_effect=[current_response, None, verify_response],
            ):
                mouse_poll_rate.set_rate("8k")
                output = capsys.readouterr().out
                assert "Current rate: 1000Hz" in output
                assert "Rate changed successfully" in output

    def test_handles_device_re_enumeration_on_set(self, capsys):
        current_response = bytes(
            [0x08, 0x08, 0x00, 0x00, 0x00, 0x06, 0x01, 0x54, 0xAA, 0xBB, 0xCC, 0xDD]
            + [0x00] * 5
        )

        with patch(
            "atk_mouse_device.find_atk_hidraw_config_interface",
            return_value="/dev/hidraw0",
        ):
            with patch(
                "atk_mouse_device.send_and_receive_atk_command",
                side_effect=[current_response, SystemExit("No response from device")],
            ):
                mouse_poll_rate.set_rate("8k")
                output = capsys.readouterr().err
                assert "re-enumerated" in output
