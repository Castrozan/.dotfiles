pragma Singleton

import Quickshell
import QtQuick

Singleton {
    readonly property int mediaUpdateInterval: 500
    readonly property int resourceUpdateInterval: 1000

    readonly property bool useTwelveHourClock: false
    readonly property bool useFahrenheit: false
    readonly property bool useFahrenheitPerformance: false

    readonly property var sizes: QtObject {
        readonly property int weatherWidth: 200
        readonly property int mediaCoverArtSize: 200
        readonly property int mediaWidth: 160
        readonly property int mediaProgressThickness: 4
        readonly property int mediaProgressSweep: 300
        readonly property int mediaVisualiserSize: 40
        readonly property int dateTimeWidth: 80
        readonly property int infoWidth: 200
        readonly property int infoIconSize: 20
        readonly property int resourceProgessThickness: 6
        readonly property int tabIndicatorSpacing: 5
        readonly property int visualiserBarCount: 30
    }

    readonly property real bongoCatGifSpeed: 1.5

    readonly property var performance: QtObject {
        readonly property bool showCpu: true
        readonly property bool showGpu: true
        readonly property bool showMemory: true
        readonly property bool showStorage: true
        readonly property bool showNetwork: true
        readonly property bool showBattery: true
    }
}
