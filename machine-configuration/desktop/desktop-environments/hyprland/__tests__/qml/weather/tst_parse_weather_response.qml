import QtQuick
import QtTest

WeatherServiceFixture {
    id: root

    TestCase {
        name: "WeatherServiceParseWeatherResponse"

        readonly property string sampleWeatherResponse: JSON.stringify({
            current: {
                temperature_2m: 22.5,
                relative_humidity_2m: 65,
                apparent_temperature: 20.3,
                is_day: 1,
                weather_code: 2,
                wind_speed_10m: 12.5
            },
            daily: {
                time: ["2026-03-29", "2026-03-30"],
                weather_code: [2, 61],
                temperature_2m_max: [25.0, 18.0],
                temperature_2m_min: [12.0, 10.0],
                sunrise: ["2026-03-29T06:30", "2026-03-30T06:28"],
                sunset: ["2026-03-29T18:45", "2026-03-30T18:46"]
            }
        })

        function test_parses_current_conditions() {
            weatherServiceLogic.currentConditions = null;
            weatherServiceLogic.forecast = [];
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            verify(weatherServiceLogic.currentConditions !== null);
            compare(weatherServiceLogic.currentConditions.weatherCode, 2);
            compare(weatherServiceLogic.currentConditions.weatherDesc, "Partly cloudy");
            compare(weatherServiceLogic.currentConditions.tempC, 23);
            compare(weatherServiceLogic.currentConditions.humidity, 65);
            fuzzyCompare(weatherServiceLogic.currentConditions.windSpeed, 12.5, 0.01);
        }

        function test_parses_fahrenheit_temperature() {
            weatherServiceLogic.currentConditions = null;
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            compare(weatherServiceLogic.currentConditions.tempF, Math.round(22.5 * 9 / 5 + 32));
        }

        function test_parses_feels_like_temperature() {
            weatherServiceLogic.currentConditions = null;
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            compare(weatherServiceLogic.currentConditions.feelsLikeC, Math.round(20.3));
            compare(weatherServiceLogic.currentConditions.feelsLikeF, Math.round(20.3 * 9 / 5 + 32));
        }

        function test_parses_sunrise_sunset() {
            weatherServiceLogic.currentConditions = null;
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            compare(weatherServiceLogic.currentConditions.sunrise, "2026-03-29T06:30");
            compare(weatherServiceLogic.currentConditions.sunset, "2026-03-29T18:45");
        }

        function test_parses_forecast_days() {
            weatherServiceLogic.forecast = [];
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            compare(weatherServiceLogic.forecast.length, 2);
            compare(weatherServiceLogic.forecast[0].date, "2026-03-29");
            compare(weatherServiceLogic.forecast[0].maxTempC, 25);
            compare(weatherServiceLogic.forecast[0].minTempC, 12);
            compare(weatherServiceLogic.forecast[0].weatherCode, 2);
            compare(weatherServiceLogic.forecast[0].icon, "partly_cloudy_day");
        }

        function test_parses_second_forecast_day() {
            weatherServiceLogic.forecast = [];
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            compare(weatherServiceLogic.forecast[1].date, "2026-03-30");
            compare(weatherServiceLogic.forecast[1].weatherCode, 61);
            compare(weatherServiceLogic.forecast[1].icon, "rainy");
        }

        function test_skips_response_without_current() {
            weatherServiceLogic.currentConditions = null;
            weatherServiceLogic.parseWeatherResponse(JSON.stringify({
                daily: {
                    time: []
                }
            }));
            compare(weatherServiceLogic.currentConditions, null);
        }

        function test_skips_response_without_daily() {
            weatherServiceLogic.currentConditions = null;
            weatherServiceLogic.parseWeatherResponse(JSON.stringify({
                current: {
                    temperature_2m: 20
                }
            }));
            compare(weatherServiceLogic.currentConditions, null);
        }

        function test_forecast_fahrenheit_conversion() {
            weatherServiceLogic.forecast = [];
            weatherServiceLogic.parseWeatherResponse(sampleWeatherResponse);

            compare(weatherServiceLogic.forecast[0].maxTempF, Math.round(25.0 * 9 / 5 + 32));
            compare(weatherServiceLogic.forecast[0].minTempF, Math.round(12.0 * 9 / 5 + 32));
        }
    }
}
