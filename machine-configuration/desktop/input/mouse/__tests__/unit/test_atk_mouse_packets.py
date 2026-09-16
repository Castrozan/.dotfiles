import atk_mouse_device


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
        result = atk_mouse_device.compute_atk_checksum(packet)
        expected = (0x55 - sum(packet)) & 0xFF
        assert result == expected

    def test_returns_checksum_within_byte_range(self):
        packet = [0xFF, 0xFF, 0xFF]
        result = atk_mouse_device.compute_atk_checksum(packet)
        assert 0 <= result <= 255

    def test_empty_packet_returns_0x55(self):
        assert atk_mouse_device.compute_atk_checksum([]) == 0x55


class TestBuildAtkCommand:
    def test_builds_get_eeprom_command(self):
        command = atk_mouse_device.build_atk_command(0x08, 0x00, 0x00, 0x06)
        assert command[0] == 0x08
        assert command[1] == 0x08
        assert command[5] == 0x06
        assert len(command) == 17

    def test_includes_data_bytes(self):
        command = atk_mouse_device.build_atk_command(
            0x07, 0x00, 0x00, 0x06, [0x40, 0x15]
        )
        assert command[6] == 0x40
        assert command[7] == 0x15

    def test_pads_missing_data_bytes_with_zeros(self):
        command = atk_mouse_device.build_atk_command(0x08, 0x00, 0x00, 0x06, [0x01])
        assert command[6] == 0x01
        assert command[7] == 0x00
        assert command[15] == 0x00

    def test_checksum_is_last_byte(self):
        command = atk_mouse_device.build_atk_command(0x08, 0x00, 0x00, 0x06)
        expected_checksum = atk_mouse_device.compute_atk_checksum(list(command[:-1]))
        assert command[-1] == expected_checksum
