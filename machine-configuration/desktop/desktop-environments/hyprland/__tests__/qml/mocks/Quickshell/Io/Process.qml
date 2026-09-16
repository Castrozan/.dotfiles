import QtQuick

QtObject {
    property var command: []
    property bool running: false
    property var stdout: null
    property var environment: ({})

    signal exited(int exitCode, int exitStatus)
}
