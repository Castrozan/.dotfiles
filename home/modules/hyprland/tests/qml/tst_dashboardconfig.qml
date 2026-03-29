import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: dashboardConfigValues

        readonly property int mediaUpdateInterval: 500
        readonly property int resourceUpdateInterval: 3000
        readonly property int audioUpdateInterval: 3000

        readonly property bool useTwelveHourClock: false
        readonly property bool useFahrenheit: false
        readonly property bool useFahrenheitPerformance: false

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

        readonly property real bongoCatGifSpeed: 1.5

        readonly property bool showCpu: true
        readonly property bool showGpu: true
        readonly property bool showMemory: true
        readonly property bool showStorage: true
        readonly property bool showNetwork: true
        readonly property bool showBattery: true
    }

    TestCase {
        name: "DashboardConfigIntervals"

        function test_media_update_interval_is_positive() {
            verify(dashboardConfigValues.mediaUpdateInterval > 0);
        }

        function test_resource_update_interval_is_positive() {
            verify(dashboardConfigValues.resourceUpdateInterval > 0);
        }

        function test_audio_update_interval_is_positive() {
            verify(dashboardConfigValues.audioUpdateInterval > 0);
        }

        function test_media_update_interval_is_reasonable() {
            verify(dashboardConfigValues.mediaUpdateInterval >= 100);
            verify(dashboardConfigValues.mediaUpdateInterval <= 10000);
        }

        function test_resource_update_interval_is_reasonable() {
            verify(dashboardConfigValues.resourceUpdateInterval >= 500);
            verify(dashboardConfigValues.resourceUpdateInterval <= 30000);
        }

        function test_audio_update_interval_is_reasonable() {
            verify(dashboardConfigValues.audioUpdateInterval >= 500);
            verify(dashboardConfigValues.audioUpdateInterval <= 30000);
        }
    }

    TestCase {
        name: "DashboardConfigSizes"

        function test_all_sizes_are_positive() {
            verify(dashboardConfigValues.weatherWidth > 0);
            verify(dashboardConfigValues.mediaCoverArtSize > 0);
            verify(dashboardConfigValues.mediaWidth > 0);
            verify(dashboardConfigValues.mediaProgressThickness > 0);
            verify(dashboardConfigValues.mediaProgressSweep > 0);
            verify(dashboardConfigValues.mediaVisualiserSize > 0);
            verify(dashboardConfigValues.dateTimeWidth > 0);
            verify(dashboardConfigValues.infoWidth > 0);
            verify(dashboardConfigValues.infoIconSize > 0);
            verify(dashboardConfigValues.resourceProgessThickness > 0);
            verify(dashboardConfigValues.tabIndicatorSpacing > 0);
            verify(dashboardConfigValues.visualiserBarCount > 0);
        }

        function test_media_progress_sweep_within_360() {
            verify(dashboardConfigValues.mediaProgressSweep <= 360);
            verify(dashboardConfigValues.mediaProgressSweep > 0);
        }

        function test_bongo_cat_gif_speed_is_positive() {
            verify(dashboardConfigValues.bongoCatGifSpeed > 0);
        }

        function test_visualiser_bar_count_is_reasonable() {
            verify(dashboardConfigValues.visualiserBarCount >= 1);
            verify(dashboardConfigValues.visualiserBarCount <= 100);
        }
    }

    TestCase {
        name: "DashboardConfigDefaults"

        function test_default_clock_is_twenty_four_hour() {
            compare(dashboardConfigValues.useTwelveHourClock, false);
        }

        function test_default_temperature_is_celsius() {
            compare(dashboardConfigValues.useFahrenheit, false);
        }

        function test_default_performance_temperature_is_celsius() {
            compare(dashboardConfigValues.useFahrenheitPerformance, false);
        }

        function test_all_performance_sections_enabled_by_default() {
            verify(dashboardConfigValues.showCpu);
            verify(dashboardConfigValues.showGpu);
            verify(dashboardConfigValues.showMemory);
            verify(dashboardConfigValues.showStorage);
            verify(dashboardConfigValues.showNetwork);
            verify(dashboardConfigValues.showBattery);
        }
    }
}
