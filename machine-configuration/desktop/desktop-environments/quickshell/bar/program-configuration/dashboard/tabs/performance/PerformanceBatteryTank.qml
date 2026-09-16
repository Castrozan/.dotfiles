pragma ComponentBehavior: Bound

import "../../components"
import "../.."
import QtQuick
import QtQuick.Layouts
import Quickshell.Services.UPower

StyledClippingRect {
    id: batteryTankRoot

    property real batteryPercentage: UPower.displayDevice.percentage
    property bool isBatteryCharging: UPower.displayDevice.state === UPowerDeviceState.Charging
    property color batteryAccentColor: Colours.palette.m3primary
    property real animatedBatteryPercentage: 0

    color: Colours.tPalette.m3surfaceContainer
    radius: Appearance.rounding.large
    Component.onCompleted: animatedBatteryPercentage = batteryPercentage
    onBatteryPercentageChanged: animatedBatteryPercentage = batteryPercentage

    StyledRect {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: parent.height * batteryTankRoot.animatedBatteryPercentage
        color: Qt.alpha(batteryTankRoot.batteryAccentColor, 0.15)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Appearance.padding.large
        spacing: Appearance.spacing.small

        ColumnLayout {
            Layout.fillWidth: true
            spacing: Appearance.spacing.small

            MaterialIcon {
                text: {
                    if (!UPower.displayDevice.isLaptopBattery)
                        return "balance";

                    if (UPower.displayDevice.state === UPowerDeviceState.FullyCharged)
                        return "battery_full";

                    const percentage = UPower.displayDevice.percentage;
                    const isCharging = [UPowerDeviceState.Charging, UPowerDeviceState.PendingCharge].includes(UPower.displayDevice.state);
                    if (percentage >= 0.99)
                        return "battery_full";

                    let batteryLevel = Math.floor(percentage * 7);
                    if (isCharging && (batteryLevel === 4 || batteryLevel === 1))
                        batteryLevel--;

                    return isCharging ? `battery_charging_${(batteryLevel + 3) * 10}` : `battery_${batteryLevel}_bar`;
                }
                font.pointSize: Appearance.font.size.large
                color: batteryTankRoot.batteryAccentColor
            }

            StyledText {
                Layout.fillWidth: true
                text: "Battery"
                font.pointSize: Appearance.font.size.normal
                color: Colours.palette.m3onSurface
            }
        }

        Item {
            Layout.fillHeight: true
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: -4

            StyledText {
                Layout.alignment: Qt.AlignRight
                text: `${Math.round(batteryTankRoot.batteryPercentage * 100)}%`
                font.pointSize: Appearance.font.size.extraLarge
                font.weight: Font.Medium
                color: batteryTankRoot.batteryAccentColor
            }

            StyledText {
                Layout.alignment: Qt.AlignRight
                text: {
                    if (UPower.displayDevice.state === UPowerDeviceState.FullyCharged)
                        return "Full";

                    if (batteryTankRoot.isBatteryCharging)
                        return "Charging";

                    const remainingSeconds = UPower.displayDevice.timeToEmpty;
                    if (remainingSeconds === 0)
                        return "...";

                    const remainingHours = Math.floor(remainingSeconds / 3600);
                    const remainingMinutes = Math.floor((remainingSeconds % 3600) / 60);
                    if (remainingHours > 0)
                        return `${remainingHours}h ${remainingMinutes}m`;

                    return `${remainingMinutes}m`;
                }
                font.pointSize: Appearance.font.size.smaller
                color: Colours.palette.m3onSurfaceVariant
            }
        }
    }

    Behavior on animatedBatteryPercentage {
        Anim {
            duration: Appearance.anim.durations.large
        }
    }
}
