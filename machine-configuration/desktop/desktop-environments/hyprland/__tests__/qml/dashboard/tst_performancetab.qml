import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: performanceTabLogic

        property bool useFahrenheitPerformance: false

        function formatTemperatureDisplay(temperatureCelsius) {
            return `${Math.ceil(useFahrenheitPerformance ? temperatureCelsius * 1.8 + 32 : temperatureCelsius)}°${useFahrenheitPerformance ? "F" : "C"}`;
        }
    }

    TestCase {
        name: "PerformanceTabTemperatureDisplayCelsius"

        function init() {
            performanceTabLogic.useFahrenheitPerformance = false;
        }

        function test_whole_celsius_keeps_its_value() {
            compare(performanceTabLogic.formatTemperatureDisplay(45), "45°C");
        }

        function test_fractional_celsius_rounds_up() {
            compare(performanceTabLogic.formatTemperatureDisplay(45.2), "46°C");
        }

        function test_zero_celsius_has_no_sign() {
            compare(performanceTabLogic.formatTemperatureDisplay(0), "0°C");
        }

        function test_negative_celsius_rounds_towards_zero() {
            compare(performanceTabLogic.formatTemperatureDisplay(-3.5), "-3°C");
        }
    }

    TestCase {
        name: "PerformanceTabTemperatureDisplayFahrenheit"

        function init() {
            performanceTabLogic.useFahrenheitPerformance = true;
        }

        function test_boiling_point_converts_exactly() {
            compare(performanceTabLogic.formatTemperatureDisplay(100), "212°F");
        }

        function test_freezing_point_converts_exactly() {
            compare(performanceTabLogic.formatTemperatureDisplay(0), "32°F");
        }

        function test_fractional_conversion_rounds_up() {
            compare(performanceTabLogic.formatTemperatureDisplay(36.6), "98°F");
        }

        function test_typical_cpu_temperature_converts() {
            compare(performanceTabLogic.formatTemperatureDisplay(45), "113°F");
        }
    }

    TestCase {
        name: "PerformanceTabTemperatureDisplayUnitSwitching"

        function test_same_reading_changes_unit_with_the_setting() {
            performanceTabLogic.useFahrenheitPerformance = false;
            const celsiusReading = performanceTabLogic.formatTemperatureDisplay(70);
            performanceTabLogic.useFahrenheitPerformance = true;
            const fahrenheitReading = performanceTabLogic.formatTemperatureDisplay(70);
            compare(celsiusReading, "70°C");
            compare(fahrenheitReading, "158°F");
        }
    }
}
