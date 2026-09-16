import QtQuick
import QtTest

WeatherServiceFixture {
    id: root

    TestCase {
        name: "WeatherServiceGetWeatherCondition"

        function test_clear() {
            compare(weatherServiceLogic.getWeatherCondition("0"), "Clear");
        }

        function test_overcast() {
            compare(weatherServiceLogic.getWeatherCondition("3"), "Overcast");
        }

        function test_fog() {
            compare(weatherServiceLogic.getWeatherCondition("45"), "Fog");
        }

        function test_drizzle() {
            compare(weatherServiceLogic.getWeatherCondition("51"), "Drizzle");
        }

        function test_freezing_drizzle() {
            compare(weatherServiceLogic.getWeatherCondition("56"), "Freezing drizzle");
        }

        function test_heavy_rain() {
            compare(weatherServiceLogic.getWeatherCondition("65"), "Heavy rain");
        }

        function test_heavy_snow() {
            compare(weatherServiceLogic.getWeatherCondition("75"), "Heavy snow");
        }

        function test_thunderstorm_with_hail() {
            compare(weatherServiceLogic.getWeatherCondition("99"), "Thunderstorm with hail");
        }

        function test_unknown_code_returns_unknown() {
            compare(weatherServiceLogic.getWeatherCondition("999"), "Unknown");
        }

        function test_empty_code_returns_unknown() {
            compare(weatherServiceLogic.getWeatherCondition(""), "Unknown");
        }
    }
}
