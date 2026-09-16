import QtQuick

Item {
    id: root

    property QtObject osdWrapper: QtObject {
        id: osdWrapper

        property bool osdVisible: false
        property string osdType: "volume"
        property int osdValue: 0
        property bool osdMuted: false
        property bool hasReceivedSocketMessage: false

        function handleOsdMessage(message) {
            try {
                var parsed = JSON.parse(message);
                osdType = parsed.type !== undefined ? parsed.type : "volume";
                osdValue = parsed.value !== undefined ? parsed.value : 0;
                osdMuted = parsed.muted !== undefined ? parsed.muted : false;
                hasReceivedSocketMessage = true;
                return true;
            } catch (error) {
                return false;
            }
        }
    }

    property QtObject osdContent: QtObject {
        id: osdContent

        property string osdType: "volume"
        property int osdValue: 0
        property bool osdMuted: false

        function applyValueFromMouseY(mouseY, trackHeight) {
            var fraction = 1.0 - Math.max(0, Math.min(mouseY, trackHeight)) / trackHeight;
            return Math.round(fraction * 100);
        }

        function computeClampedFraction(value) {
            return Math.min(value / 100.0, 1.0);
        }

        function computeIconForType(type, muted) {
            if (type === "brightness")
                return "brightness_6";
            if (type === "mic")
                return muted ? "mic_off" : "mic";
            return muted ? "volume_off" : "volume_up";
        }

        function computeDisplayText(muted, value) {
            return muted ? "M" : value + "%";
        }

        function computeWheelNewValue(currentValue, angleDeltaY) {
            var delta = angleDeltaY > 0 ? 5 : -5;
            return Math.max(0, Math.min(100, currentValue + delta));
        }
    }
}
