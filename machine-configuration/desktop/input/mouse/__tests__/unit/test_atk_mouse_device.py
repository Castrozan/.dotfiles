from unittest.mock import MagicMock, patch

import atk_mouse_device


class TestReadSysfsAttribute:
    def test_reads_existing_attribute(self, tmp_path):
        attr_file = tmp_path / "test_attr"
        attr_file.write_text("  some_value  \n")
        assert atk_mouse_device.read_sysfs_attribute(attr_file) == "some_value"

    def test_returns_default_for_missing_file(self, tmp_path):
        missing = tmp_path / "nonexistent"
        assert atk_mouse_device.read_sysfs_attribute(missing) == "unknown"

    def test_returns_custom_default(self, tmp_path):
        missing = tmp_path / "nonexistent"
        assert atk_mouse_device.read_sysfs_attribute(missing, "N/A") == "N/A"


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

        with patch("atk_mouse_device.Path") as mock_path_cls:
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

            result = atk_mouse_device.find_atk_hidraw_config_interface()
            assert result == "/dev/hidraw5"

    def test_raises_when_no_device_found(self):
        with patch("atk_mouse_device.Path") as mock_path_cls:
            mock_hidraw_base = MagicMock()
            mock_hidraw_base.exists.return_value = True
            mock_hidraw_base.iterdir.return_value = []
            mock_path_cls.return_value = mock_hidraw_base

            try:
                atk_mouse_device.find_atk_hidraw_config_interface()
                assert False, "Should have raised SystemExit"
            except SystemExit:
                pass

    def test_raises_when_sysfs_not_available(self):
        with patch("atk_mouse_device.Path") as mock_path_cls:
            mock_hidraw_base = MagicMock()
            mock_hidraw_base.exists.return_value = False
            mock_path_cls.return_value = mock_hidraw_base

            try:
                atk_mouse_device.find_atk_hidraw_config_interface()
                assert False, "Should have raised SystemExit"
            except SystemExit:
                pass


class TestSendAndReceiveAtkCommand:
    def test_sends_command_and_returns_valid_response(self):
        valid_response = bytes([0x08, 0x08] + [0x00] * 15)

        with patch("atk_mouse_device.os.open", return_value=3):
            with patch("atk_mouse_device.os.close"):
                with patch("atk_mouse_device.os.write"):
                    with patch(
                        "atk_mouse_device.select.select",
                        side_effect=[
                            ([], [], []),
                            ([3], [], []),
                        ],
                    ):
                        with patch(
                            "atk_mouse_device.os.read", return_value=valid_response
                        ):
                            result = atk_mouse_device.send_and_receive_atk_command(
                                "/dev/hidraw0", b"\x08\x08"
                            )
                            assert result == valid_response

    def test_raises_on_timeout(self):
        with patch("atk_mouse_device.os.open", return_value=3):
            with patch("atk_mouse_device.os.close"):
                with patch("atk_mouse_device.os.write"):
                    with patch(
                        "atk_mouse_device.select.select", return_value=([], [], [])
                    ):
                        with patch(
                            "atk_mouse_device.time.monotonic", side_effect=[0, 0, 4]
                        ):
                            try:
                                atk_mouse_device.send_and_receive_atk_command(
                                    "/dev/hidraw0", b"\x08\x08"
                                )
                                assert False, "Should have raised SystemExit"
                            except SystemExit:
                                pass
