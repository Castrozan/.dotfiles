from unittest.mock import patch

import pytest

import corsair_mouse_brightness


class FakeReceiver:
    def __init__(self, responses):
        self.responses = list(responses)
        self.written_reports = []

    def write(self, report):
        self.written_reports.append(bytes(report))

    def read(self, size, timeout=None):
        return self.responses.pop(0) if self.responses else b""

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        return False


def response(command, status=0, value=0):
    return bytes([0x01, command, status]) + value.to_bytes(2, "little") + bytes(59)


def command_bytes(report):
    return report[1:7]


class TestFindReceiverCommandInterfacePath:
    def test_selects_vendor_command_interface(self):
        interfaces = [
            {"usage_page": 0x01, "usage": 0x02, "path": b"/dev/hidraw3"},
            {"usage_page": 0xFF42, "usage": 0x02, "path": b"/dev/hidraw5"},
            {"usage_page": 0xFF42, "usage": 0x01, "path": b"/dev/hidraw4"},
        ]
        with patch.object(
            corsair_mouse_brightness.hid, "enumerate", return_value=interfaces
        ):
            assert (
                corsair_mouse_brightness.find_receiver_command_interface_path()
                == b"/dev/hidraw4"
            )

    def test_reports_missing_receiver(self):
        with patch.object(corsair_mouse_brightness.hid, "enumerate", return_value=[]):
            with pytest.raises(
                corsair_mouse_brightness.CorsairMouseError, match="not connected"
            ):
                corsair_mouse_brightness.find_receiver_command_interface_path()


class TestGetProperty:
    def test_sends_wireless_get_and_decodes_little_endian_value(self):
        receiver = FakeReceiver([response(0x02, value=250)])
        assert corsair_mouse_brightness.get_property(receiver, 0x02) == 250
        assert command_bytes(receiver.written_reports[0]) == bytes(
            [0x09, 0x02, 0x02, 0x00, 0x00, 0x00]
        )
        assert len(receiver.written_reports[0]) == 65

    def test_skips_unrelated_reports_until_command_echo(self):
        receiver = FakeReceiver([response(0x12), response(0x02, value=7)])
        assert corsair_mouse_brightness.get_property(receiver, 0x02) == 7

    def test_reports_silent_mouse(self):
        receiver = FakeReceiver([])
        with pytest.raises(corsair_mouse_brightness.CorsairMouseError, match="wake"):
            corsair_mouse_brightness.get_property(receiver, 0x02)

    def test_reports_failed_status(self):
        receiver = FakeReceiver([response(0x02, status=5)])
        with pytest.raises(
            corsair_mouse_brightness.CorsairMouseError, match="status 5"
        ):
            corsair_mouse_brightness.get_property(receiver, 0x44)


class TestStoreOnboardBrightness:
    def test_writes_brightness_in_software_mode_then_restores_hardware_mode(self):
        receiver = FakeReceiver(
            [response(0x01), response(0x01), response(0x01), response(0x02, value=0)]
        )
        assert corsair_mouse_brightness.store_onboard_brightness(receiver, 0) == 0
        assert [command_bytes(report) for report in receiver.written_reports] == [
            bytes([0x09, 0x01, 0x03, 0x00, 0x02, 0x00]),
            bytes([0x09, 0x01, 0x02, 0x00, 0x00, 0x00]),
            bytes([0x09, 0x01, 0x03, 0x00, 0x01, 0x00]),
            bytes([0x09, 0x02, 0x02, 0x00, 0x00, 0x00]),
        ]

    def test_restores_hardware_mode_when_brightness_write_fails(self):
        receiver = FakeReceiver(
            [response(0x01), response(0x01, status=3), response(0x01)]
        )
        with pytest.raises(
            corsair_mouse_brightness.CorsairMouseError, match="status 3"
        ):
            corsair_mouse_brightness.store_onboard_brightness(receiver, 1000)
        assert command_bytes(receiver.written_reports[-1]) == bytes(
            [0x09, 0x01, 0x03, 0x00, 0x01, 0x00]
        )


class TestParseRequestedBrightness:
    def test_no_argument_reads(self):
        assert corsair_mouse_brightness.parse_requested_brightness([]) is None

    def test_accepts_range_bounds(self):
        assert corsair_mouse_brightness.parse_requested_brightness(["0"]) == 0
        assert corsair_mouse_brightness.parse_requested_brightness(["1000"]) == 1000

    @pytest.mark.parametrize("arguments", [["1001"], ["-1"], ["off"], ["1", "2"]])
    def test_rejects_invalid_arguments(self, arguments):
        with pytest.raises(corsair_mouse_brightness.CorsairMouseError):
            corsair_mouse_brightness.parse_requested_brightness(arguments)


class TestMain:
    def test_prints_stored_brightness(self, capsys):
        receiver = FakeReceiver(
            [response(0x01), response(0x01), response(0x01), response(0x02, value=0)]
        )
        with (
            patch.object(
                corsair_mouse_brightness.sys, "argv", ["corsair-mouse-brightness", "0"]
            ),
            patch.object(
                corsair_mouse_brightness,
                "find_receiver_command_interface_path",
                return_value=b"x",
            ),
            patch.object(corsair_mouse_brightness.hid, "Device", return_value=receiver),
        ):
            corsair_mouse_brightness.main()
        assert capsys.readouterr().out.strip() == "0"

    def test_exits_nonzero_with_message_on_error(self, capsys):
        with (
            patch.object(
                corsair_mouse_brightness.sys, "argv", ["corsair-mouse-brightness", "x"]
            ),
            pytest.raises(SystemExit) as exit_info,
        ):
            corsair_mouse_brightness.main()
        assert exit_info.value.code == 1
        assert "usage" in capsys.readouterr().err
