import QtQuick
import QtTest

WeatherServiceFixture {
    id: root

    TestCase {
        name: "WeatherServiceGetWeatherIcon"

        function test_clear_sky_returns_clear_day() {
            compare(weatherServiceLogic.getWeatherIcon("0"), "clear_day");
        }

        function test_mainly_clear_returns_clear_day() {
            compare(weatherServiceLogic.getWeatherIcon("1"), "clear_day");
        }

        function test_partly_cloudy() {
            compare(weatherServiceLogic.getWeatherIcon("2"), "partly_cloudy_day");
        }

        function test_overcast() {
            compare(weatherServiceLogic.getWeatherIcon("3"), "cloud");
        }

        function test_fog() {
            compare(weatherServiceLogic.getWeatherIcon("45"), "foggy");
        }

        function test_rime_fog() {
            compare(weatherServiceLogic.getWeatherIcon("48"), "foggy");
        }

        function test_rain_codes() {
            var rainCodes = ["51", "53", "55", "56", "57", "61", "63", "65", "66", "67", "80", "81", "82"];
            for (var i = 0; i < rainCodes.length; i++)
                compare(weatherServiceLogic.getWeatherIcon(rainCodes[i]), "rainy");
        }

        function test_snow_codes() {
            compare(weatherServiceLogic.getWeatherIcon("71"), "cloudy_snowing");
            compare(weatherServiceLogic.getWeatherIcon("73"), "cloudy_snowing");
            compare(weatherServiceLogic.getWeatherIcon("77"), "cloudy_snowing");
            compare(weatherServiceLogic.getWeatherIcon("85"), "cloudy_snowing");
        }

        function test_heavy_snow_codes() {
            compare(weatherServiceLogic.getWeatherIcon("75"), "snowing_heavy");
            compare(weatherServiceLogic.getWeatherIcon("86"), "snowing_heavy");
        }

        function test_thunderstorm_codes() {
            compare(weatherServiceLogic.getWeatherIcon("95"), "thunderstorm");
            compare(weatherServiceLogic.getWeatherIcon("96"), "thunderstorm");
            compare(weatherServiceLogic.getWeatherIcon("99"), "thunderstorm");
        }

        function test_unknown_code_returns_air() {
            compare(weatherServiceLogic.getWeatherIcon("999"), "air");
        }

        function test_empty_string_code_returns_air() {
            compare(weatherServiceLogic.getWeatherIcon(""), "air");
        }

        function test_numeric_zero_as_string() {
            compare(weatherServiceLogic.getWeatherIcon(0), "clear_day");
        }
    }
}
