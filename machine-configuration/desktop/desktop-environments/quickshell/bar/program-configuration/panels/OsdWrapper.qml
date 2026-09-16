pragma ComponentBehavior: Bound

import Quickshell.Io
import "../dashboard/components"
import "../dashboard"
import QtQuick

Item {
    id: osdWrapperRoot

    property bool osdVisible: false
    property string osdType: "volume"
    property int osdValue: 0
    property bool osdMuted: false
    property bool hasReceivedSocketMessage: false
    property real visibleProgress: 0

    signal osdMessageReceived()

    visible: osdVisible || visibleProgress > 0
    width: visible ? implicitWidth : 0
    height: implicitHeight
    implicitWidth: osdContentLoader.implicitWidth
    implicitHeight: osdContentLoader.implicitHeight
    clip: true

    function handleOsdMessage(message: string): void {
        try {
            let parsed = JSON.parse(message);
            osdType = parsed.type ?? "volume";
            osdValue = parsed.value ?? 0;
            osdMuted = parsed.muted ?? false;
            hasReceivedSocketMessage = true;
            osdMessageReceived();
        } catch (error) {
            return;
        }
    }

    function queryCurrentState(): void {
        queryCurrentVolumeProcess.running = true;
    }

    onOsdVisibleChanged: {
        if (osdVisible && !hasReceivedSocketMessage)
            queryCurrentState();
        if (!osdVisible)
            hasReceivedSocketMessage = false;
    }

    Process {
        id: queryCurrentVolumeProcess
        command: ["volume", "--get"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                let parsed = parseInt(data.trim());
                if (!isNaN(parsed))
                    osdWrapperRoot.osdValue = parsed;
            }
        }
    }

    Process {
        id: queryCurrentMuteProcess
        command: ["pactl", "get-sink-mute", "@DEFAULT_SINK@"]
        stdout: SplitParser {
            splitMarker: ""
            onRead: data => {
                osdWrapperRoot.osdMuted = data.trim().indexOf("yes") >= 0;
            }
        }
    }

    Connections {
        target: queryCurrentVolumeProcess
        function onRunningChanged(): void {
            if (!queryCurrentVolumeProcess.running)
                queryCurrentMuteProcess.running = true;
        }
    }

    states: State {
        name: "visible"
        when: osdWrapperRoot.osdVisible

        PropertyChanges {
            osdWrapperRoot.visibleProgress: 1
        }
    }

    transitions: [
        Transition {
            from: ""
            to: "visible"

            Anim {
                target: osdWrapperRoot
                property: "visibleProgress"
                duration: Appearance.anim.durations.expressiveDefaultSpatial
                easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
            }
        },
        Transition {
            from: "visible"
            to: ""

            Anim {
                target: osdWrapperRoot
                property: "visibleProgress"
                easing.bezierCurve: Appearance.anim.curves.emphasized
            }
        }
    ]

    Loader {
        id: osdContentLoader

        anchors.verticalCenter: parent.verticalCenter
        x: osdWrapperRoot.width * (1 - osdWrapperRoot.visibleProgress)
        opacity: osdWrapperRoot.visibleProgress

        active: osdWrapperRoot.osdVisible || osdWrapperRoot.visible

        sourceComponent: OsdContent {
            osdType: osdWrapperRoot.osdType
            osdValue: osdWrapperRoot.osdValue
            osdMuted: osdWrapperRoot.osdMuted

            onOsdValueChanged: osdWrapperRoot.osdValue = osdValue
            onInteractionKeepAlive: osdWrapperRoot.osdMessageReceived()
        }
    }
}
