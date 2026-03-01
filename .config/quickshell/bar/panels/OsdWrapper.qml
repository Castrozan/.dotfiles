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

    signal osdMessageReceived()

    visible: width > 0
    width: implicitWidth
    height: implicitHeight
    implicitWidth: 0
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

    SocketServer {
        active: true
        path: "/tmp/quickshell-osd.sock"

        handler: Socket {
            parser: SplitParser {
                splitMarker: "\n"
                onRead: message => osdWrapperRoot.handleOsdMessage(message)
            }
        }
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
            osdWrapperRoot.implicitWidth: osdContentLoader.implicitWidth
        }
    }

    transitions: [
        Transition {
            from: ""
            to: "visible"

            Anim {
                target: osdWrapperRoot
                property: "implicitWidth"
                duration: Appearance.anim.durations.expressiveDefaultSpatial
                easing.bezierCurve: Appearance.anim.curves.expressiveDefaultSpatial
            }
        },
        Transition {
            from: "visible"
            to: ""

            Anim {
                target: osdWrapperRoot
                property: "implicitWidth"
                easing.bezierCurve: Appearance.anim.curves.emphasized
            }
        }
    ]

    Loader {
        id: osdContentLoader

        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter

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
