import QtQuick
import QtTest

WeatherServiceFixture {
    id: root

    TestCase {
        name: "WeatherServiceBuildWeatherApiUrl"

        function test_builds_url_with_valid_coordinates() {
            weatherServiceLogic.locationCoordinates = "52.52,13.41";
            var url = weatherServiceLogic.buildWeatherApiUrl();
            verify(url.indexOf("https://api.open-meteo.com/v1/forecast?") === 0);
            verify(url.indexOf("latitude=52.52") !== -1);
            verify(url.indexOf("longitude=13.41") !== -1);
            verify(url.indexOf("forecast_days=7") !== -1);
            verify(url.indexOf("timezone=auto") !== -1);
        }

        function test_returns_empty_for_empty_coordinates() {
            weatherServiceLogic.locationCoordinates = "";
            compare(weatherServiceLogic.buildWeatherApiUrl(), "");
        }

        function test_returns_empty_for_no_comma() {
            weatherServiceLogic.locationCoordinates = "52.52";
            compare(weatherServiceLogic.buildWeatherApiUrl(), "");
        }

        function test_handles_negative_coordinates() {
            weatherServiceLogic.locationCoordinates = "-23.55,-46.63";
            var url = weatherServiceLogic.buildWeatherApiUrl();
            verify(url.indexOf("latitude=-23.55") !== -1);
            verify(url.indexOf("longitude=-46.63") !== -1);
        }
    }
}
