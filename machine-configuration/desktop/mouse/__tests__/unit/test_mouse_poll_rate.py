from unittest.mock import MagicMock, patch

import mouse_poll_rate


class TestComputeAtkChecksum:
    def test_returns_correct_checksum_for_known_packet(self):
        packet = [
            0x08,
            0x08,
            0x00,
            0x00,
            0x00,
            0x06,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
        ]
        result = mouse_poll_rate.compute_atk_checksum(packet)
        expected = (0x55 - sum(packet)) & 0xFF
        assert result == expected

    def test_returns_checksum_within_byte_range(self):
        packet = [0xFF, 0xFF, 0xFF]
        result = mouse_poll_rate.compute_atk_checksum(packet)
        assert 0 <= result <= 255

    def test_empty_packet_returns_0x55(self):
        assert mouse_poll_rate.compute_atk_checksum([]) == 0x55


class TestBuildAtkCommand:
    def test_builds_get_eeprom_command(self):
        command = mouse_poll_rate.build_atk_command(0x08, 0x00, 0x00, 0x06)
        assert command[0] == 0x08
        assert command[1] == 0x08
        assert command[5] == 0x06
        assert len(command) == 17

    def test_includes_data_bytes(self):
        command = mouse_poll_rate.build_atk_command(
            0x07, 0x00, 0x00, 0x06, [0x40, 0x15]
        )
        assert command[6] == 0x40
        assert command[7] == 0x15

    def test_pads_missing_data_bytes_with_zeros(self):
        command = mouse_poll_rate.build_atk_command(0x08, 0x00, 0x00, 0x06, [0x01])
        assert command[6] == 0x01
        assert command[7] == 0x00
        assert command[15] == 0x00

    def test_checksum_is_last_byte(self):
        command = mouse_poll_rate.build_atk_command(0x08, 0x00, 0x00, 0x06)
        expected_checksum = mouse_poll_rate.compute_atk_checksum(list(command[:-1]))
        assert command[-1] == expected_checksum


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


class TestReadSysfsAttribute:
    def test_reads_existing_attribute(self, tmp_path):
        attr_file = tmp_path / "test_attr"
        attr_file.write_text("  some_value  \n")
        assert mouse_poll_rate.read_sysfs_attribute(attr_file) == "some_value"

    def test_returns_default_for_missing_file(self, tmp_path):
        missing = tmp_path / "nonexistent"
        assert mouse_poll_rate.read_sysfs_attribute(missing) == "unknown"

    def test_returns_custom_default(self, tmp_path):
        missing = tmp_path / "nonexistent"
        assert mouse_poll_rate.read_sysfs_attribute(missing, "N/A") == "N/A"


class TestFindAtkHidrawConfigInterface:
    def test_finds_matching_device(self, tmp_path):
        hidraw_dir = tmp_path / "hidraw5"
        hidraw_dir.mkdir()

        device_dir = hidraw_dir / "device"
        device_dir.mkdir()

        interface_parent = device_dir / "iface_parent"
        interface_parent.mkdir()
        (interface_parent / "bInterfaceNumber").write_text("01\n")

        vendor_grandparent = interface_parent / "vendor_gp"
        vendor_grandparent.mkdir()
        (vendor_grandparent / "idVendor").write_text("373b\n")

        vendor_resolve = vendor_grandparent / "idVendor"
        interface_resolve = interface_parent / "bInterfaceNumber"

        with patch("mouse_poll_rate.Path") as mock_path_cls:
            mock_hidraw_base = MagicMock()
            mock_hidraw_base.exists.return_value = True

            mock_entry = MagicMock()
            mock_entry.name = "hidraw5"

            vendor_chain = MagicMock()
            vendor_chain.resolve.return_value = vendor_resolve

            interface_chain = MagicMock()
            interface_chain.resolve.return_value = interface_resolve

            mock_entry.__truediv__ = lambda self, k: (
                MagicMock(
                    __truediv__=lambda self2, k2: MagicMock(
                        __truediv__=lambda self3, k3: (
                            MagicMock(__truediv__=lambda self4, k4: vendor_chain)
                            if k3 == ".."
                            else interface_chain
                            if k3 == "bInterfaceNumber"
                            else MagicMock()
                        )
                    )
                    if k2 == ".."
                    else MagicMock()
                )
                if k == "device"
                else MagicMock()
            )

            mock_hidraw_base.iterdir.return_value = [mock_entry]
            mock_path_cls.return_value = mock_hidraw_base

            result = mouse_poll_rate.find_atk_hidraw_config_interface()
            assert result == "/dev/hidraw5"

    def test_raises_when_no_device_found(self):
        with patch("mouse_poll_rate.Path") as mock_path_cls:
            mock_hidraw_base = MagicMock()
            mock_hidraw_base.exists.return_value = True
            mock_hidraw_base.iterdir.return_value = []
            mock_path_cls.return_value = mock_hidraw_base

            try:
                mouse_poll_rate.find_atk_hidraw_config_interface()
                assert False, "Should have raised SystemExit"
            except SystemExit:
                pass

    def test_raises_when_sysfs_not_available(self):
        with patch("mouse_poll_rate.Path") as mock_path_cls:
            mock_hidraw_base = MagicMock()
            mock_hidraw_base.exists.return_value = False
            mock_path_cls.return_value = mock_hidraw_base

            try:
                mouse_poll_rate.find_atk_hidraw_config_interface()
                assert False, "Should have raised SystemExit"
            except SystemExit:
                pass


class TestSendAndReceiveAtkCommand:
    def test_sends_command_and_returns_valid_response(self):
        valid_response = bytes([0x08, 0x08] + [0x00] * 15)

        with patch("mouse_poll_rate.os.open", return_value=3):
            with patch("mouse_poll_rate.os.close"):
                with patch("mouse_poll_rate.os.write"):
                    with patch(
                        "mouse_poll_rate.select.select",
                        side_effect=[
                            ([], [], []),
                            ([3], [], []),
                        ],
                    ):
                        with patch(
                            "mouse_poll_rate.os.read", return_value=valid_response
                        ):
                            result = mouse_poll_rate.send_and_receive_atk_command(
                                "/dev/hidraw0", b"\x08\x08"
                            )
                            assert result == valid_response

    def test_raises_on_timeout(self):
        with patch("mouse_poll_rate.os.open", return_value=3):
            with patch("mouse_poll_rate.os.close"):
                with patch("mouse_poll_rate.os.write"):
                    with patch(
                        "mouse_poll_rate.select.select", return_value=([], [], [])
                    ):
                        with patch(
                            "mouse_poll_rate.time.monotonic", side_effect=[0, 0, 4]
                        ):
                            try:
                                mouse_poll_rate.send_and_receive_atk_command(
                                    "/dev/hidraw0", b"\x08\x08"
                                )
                                assert False, "Should have raised SystemExit"
                            except SystemExit:
                                pass


class TestGetCurrentRate:
    def test_returns_decoded_rate(self):
        response = bytes([0x08, 0x08, 0x00, 0x00, 0x00, 0x06, 0x40, 0x15] + [0x00] * 9)

        with patch(
            "mouse_poll_rate.find_atk_hidraw_config_interface",
            return_value="/dev/hidraw0",
        ):
            with patch(
                "mouse_poll_rate.send_and_receive_atk_command",
                return_value=response,
            ):
                assert mouse_poll_rate.get_current_rate() == "8000Hz"


class TestSetRate:
    def test_skips_when_already_at_target(self, capsys):
        current_response = bytes(
            [0x08, 0x08, 0x00, 0x00, 0x00, 0x06, 0x40, 0x15] + [0x00] * 9
        )

        with patch(
            "mouse_poll_rate.find_atk_hidraw_config_interface",
            return_value="/dev/hidraw0",
        ):
            with patch(
                "mouse_poll_rate.send_and_receive_atk_command",
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
            "mouse_poll_rate.find_atk_hidraw_config_interface",
            return_value="/dev/hidraw0",
        ):
            with patch(
                "mouse_poll_rate.send_and_receive_atk_command",
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
            "mouse_poll_rate.find_atk_hidraw_config_interface",
            return_value="/dev/hidraw0",
        ):
            with patch(
                "mouse_poll_rate.send_and_receive_atk_command",
                side_effect=[current_response, SystemExit("No response from device")],
            ):
                mouse_poll_rate.set_rate("8k")
                output = capsys.readouterr().err
                assert "re-enumerated" in output


class TestShowDeviceInfo:
    def test_displays_device_information(self, capsys):
        mock_usb_path = MagicMock()

        call_counter = {"n": 0}
        ordered_values = ["ATK Mouse", "373b", "1234", "480", " 2.00 "]

        def read_sysfs_side_effect(path, default="unknown"):
            idx = call_counter["n"]
            call_counter["n"] += 1
            if idx < len(ordered_values):
                return ordered_values[idx]
            return default

        with patch(
            "mouse_poll_rate.find_atk_usb_device_path",
            return_value=mock_usb_path,
        ):
            with patch(
                "mouse_poll_rate.read_sysfs_attribute",
                side_effect=read_sysfs_side_effect,
            ):
                with patch(
                    "mouse_poll_rate.find_atk_hidraw_config_interface",
                    return_value="/dev/hidraw0",
                ):
                    with patch(
                        "mouse_poll_rate.get_current_rate",
                        return_value="8000Hz",
                    ):
                        mouse_poll_rate.show_device_info()
                        output = capsys.readouterr().out
                        assert "ATK Mouse" in output
                        assert "480" in output
                        assert "8000Hz" in output


class TestMain:
    def test_get_subcommand(self):
        with patch("mouse_poll_rate.sys.argv", ["cmd", "get"]):
            with patch(
                "mouse_poll_rate.get_current_rate", return_value="4000Hz"
            ) as mock_get:
                mouse_poll_rate.main()
                mock_get.assert_called_once()

    def test_set_subcommand(self):
        with patch("mouse_poll_rate.sys.argv", ["cmd", "set", "8k"]):
            with patch("mouse_poll_rate.set_rate") as mock_set:
                mouse_poll_rate.main()
                mock_set.assert_called_once_with("8k")

    def test_info_subcommand(self):
        with patch("mouse_poll_rate.sys.argv", ["cmd", "info"]):
            with patch("mouse_poll_rate.show_device_info") as mock_info:
                mouse_poll_rate.main()
                mock_info.assert_called_once()

    def test_no_args_exits_with_usage(self):
        with patch("mouse_poll_rate.sys.argv", ["cmd"]):
            try:
                mouse_poll_rate.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1

    def test_set_without_rate_exits(self):
        with patch("mouse_poll_rate.sys.argv", ["cmd", "set"]):
            try:
                mouse_poll_rate.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1

    def test_unknown_subcommand_exits(self):
        with patch("mouse_poll_rate.sys.argv", ["cmd", "bogus"]):
            try:
                mouse_poll_rate.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1
