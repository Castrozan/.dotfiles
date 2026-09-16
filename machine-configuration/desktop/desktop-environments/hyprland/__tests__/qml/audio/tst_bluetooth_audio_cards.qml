import QtQuick
import QtTest

Item {
    AudioDeviceSelectionFixture {
        id: audioServiceLogic
    }
    TestCase {
        name: "AudioServiceCardForBluetoothMac"

        function test_finds_card_by_mac_with_colons() {
            audioServiceLogic.cards = [
                {
                    name: "bluez_card.AA_BB_CC_DD_EE_FF",
                    activeProfile: "a2dp-sink"
                },
                {
                    name: "alsa_card.pci-0000_00_1f.3",
                    activeProfile: "output:analog-stereo"
                }
            ];
            var result = audioServiceLogic.cardForBluetoothMac("AA:BB:CC:DD:EE:FF");
            verify(result !== null);
            compare(result.name, "bluez_card.AA_BB_CC_DD_EE_FF");
        }

        function test_returns_null_when_no_matching_card() {
            audioServiceLogic.cards = [
                {
                    name: "alsa_card.pci-0000_00_1f.3",
                    activeProfile: "output:analog-stereo"
                }
            ];
            compare(audioServiceLogic.cardForBluetoothMac("AA:BB:CC:DD:EE:FF"), null);
        }

        function test_returns_null_for_empty_cards() {
            audioServiceLogic.cards = [];
            compare(audioServiceLogic.cardForBluetoothMac("AA:BB:CC:DD:EE:FF"), null);
        }

        function test_normalizes_colons_to_underscores() {
            audioServiceLogic.cards = [
                {
                    name: "bluez_card.11_22_33_44_55_66",
                    activeProfile: "a2dp-sink"
                }
            ];
            var result = audioServiceLogic.cardForBluetoothMac("11:22:33:44:55:66");
            verify(result !== null);
            compare(result.name, "bluez_card.11_22_33_44_55_66");
        }

        function test_mac_already_has_underscores() {
            audioServiceLogic.cards = [
                {
                    name: "bluez_card.11_22_33_44_55_66",
                    activeProfile: "a2dp-sink"
                }
            ];
            var result = audioServiceLogic.cardForBluetoothMac("11_22_33_44_55_66");
            verify(result !== null);
        }
    }
}
