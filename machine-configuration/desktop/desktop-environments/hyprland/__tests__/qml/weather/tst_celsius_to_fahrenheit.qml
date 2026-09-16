import QtQuick
import QtTest

WeatherServiceFixture {
    id: root

    TestCase {
        name: "WeatherServiceCelsiusToFahrenheit"

        function test_freezing_point() {
            fuzzyCompare(weatherServiceLogic.celsiusToFahrenheit(0), 32.0, 0.01);
        }

        function test_boiling_point() {
            fuzzyCompare(weatherServiceLogic.celsiusToFahrenheit(100), 212.0, 0.01);
        }

        function test_body_temperature() {
            fuzzyCompare(weatherServiceLogic.celsiusToFahrenheit(37), 98.6, 0.01);
        }

        function test_negative_temperature() {
            fuzzyCompare(weatherServiceLogic.celsiusToFahrenheit(-40), -40.0, 0.01);
        }

        function test_room_temperature() {
            fuzzyCompare(weatherServiceLogic.celsiusToFahrenheit(20), 68.0, 0.01);
        }

        function test_absolute_zero_celsius() {
            fuzzyCompare(weatherServiceLogic.celsiusToFahrenheit(-273.15), -459.67, 0.01);
        }
    }
}
